"""Large costs wait for the chair (or a resident vote) before anyone is billed."""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.apartments.models import Apartment
from apps.buildings.models import Building, UserBuilding
from apps.expenses.models import Expense, ExpenseCategory
from apps.governance.finalize import finalize_polls
from apps.governance.models import Poll

pytestmark = pytest.mark.django_db


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def building(admin_user):
    return Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user, approval_threshold=Decimal("1000.00"))


@pytest.fixture
def residents(building, django_user_model):
    made = []
    for n in range(1, 5):
        u = django_user_model.objects.create_user(email=f"r{n}@abem.test", password="RPass1!xxx", role="owner")
        apt = Apartment.objects.create(building=building, unit_number=str(n), owner=u)
        apt.owners.add(u)
        UserBuilding.objects.create(user=u, building=building)
        made.append((u, apt))
    return made


@pytest.fixture
def category(building):
    return ExpenseCategory.objects.create(building=building, name="Lift")


def _add(user, building, category, amount, **extra):
    return _client(user).post("/api/v1/expenses/", {
        "building_id": str(building.pk), "category_id": str(category.pk), "title": "New elevator",
        "amount": str(amount), "expense_date": str(date.today()), "split_type": "equal_all", **extra,
    }, format="json")


def _balances(residents):
    return [Apartment.objects.get(pk=a.pk).balance for _, a in residents]


def _make_chair(building, user):
    UserBuilding.objects.filter(building=building, user=user).update(board_role="chair")


def test_a_cost_under_the_threshold_bills_immediately(admin_user, building, residents, category):
    resp = _add(admin_user, building, category, 800)
    assert resp.status_code == 201 and resp.data["approval_status"] == "approved"
    assert _balances(residents) == [Decimal("200.00")] * 4


def test_a_large_cost_waits_and_bills_no_one(admin_user, building, residents, category):
    resp = _add(admin_user, building, category, 5000)
    assert resp.status_code == 201 and resp.data["approval_status"] == "pending"
    assert _balances(residents) == [Decimal("0.00")] * 4
    assert Expense.objects.get().apartment_expenses.count() == 0


def test_pending_costs_are_not_spent_money_yet(admin_user, building, residents, category):
    _add(admin_user, building, category, 5000)
    treasury = _client(admin_user).get(f"/api/v1/buildings/{building.pk}/treasury/").data
    assert Decimal(treasury["total_expenses"]) == Decimal("0.00")


def test_the_chair_approves_and_units_are_billed(admin_user, building, residents, category):
    chair = residents[0][0]
    _make_chair(building, chair)
    expense_id = _add(admin_user, building, category, 5000).data["id"]

    assert _client(chair).get(f"/api/v1/expenses/{expense_id}/").data["can_decide"] is True
    assert _client(admin_user).get(f"/api/v1/expenses/{expense_id}/").data["can_decide"] is False   # admin cannot approve their own
    assert _client(admin_user).post(f"/api/v1/expenses/{expense_id}/approve/").status_code == 403

    resp = _client(chair).post(f"/api/v1/expenses/{expense_id}/approve/", {"note": "Agreed at the meeting"}, format="json")
    assert resp.status_code == 200 and resp.data["approval_status"] == "approved"
    assert _balances(residents) == [Decimal("1250.00")] * 4
    treasury = _client(admin_user).get(f"/api/v1/buildings/{building.pk}/treasury/").data
    assert Decimal(treasury["total_expenses"]) == Decimal("5000.00")
    assert _client(chair).post(f"/api/v1/expenses/{expense_id}/approve/").status_code == 409     # not twice


def test_the_chair_can_reject(admin_user, building, residents, category):
    chair = residents[0][0]
    _make_chair(building, chair)
    expense_id = _add(admin_user, building, category, 5000).data["id"]
    resp = _client(chair).post(f"/api/v1/expenses/{expense_id}/reject/", {"note": "Too expensive"}, format="json")
    assert resp.status_code == 200 and resp.data["approval_status"] == "rejected"
    assert _balances(residents) == [Decimal("0.00")] * 4


def test_without_a_chair_the_admin_decides_so_nothing_is_stuck(admin_user, building, residents, category):
    expense_id = _add(admin_user, building, category, 5000).data["id"]
    assert _client(admin_user).post(f"/api/v1/expenses/{expense_id}/approve/").status_code == 200


def test_ordinary_residents_cannot_decide(admin_user, building, residents, category):
    _make_chair(building, residents[0][0])
    expense_id = _add(admin_user, building, category, 5000).data["id"]
    assert _client(residents[1][0]).post(f"/api/v1/expenses/{expense_id}/approve/").status_code == 403


def test_editing_a_cost_above_the_threshold_cannot_dodge_approval(admin_user, building, residents, category):
    expense_id = _add(admin_user, building, category, 800).data["id"]
    assert _balances(residents) == [Decimal("200.00")] * 4
    resp = _client(admin_user).patch(f"/api/v1/expenses/{expense_id}/", {"amount": "9000"}, format="json")
    assert resp.status_code == 200 and resp.data["approval_status"] == "pending"
    assert _balances(residents) == [Decimal("0.00")] * 4          # the earlier billing was taken back


def test_lowering_a_pending_cost_under_the_threshold_approves_it(admin_user, building, residents, category):
    expense_id = _add(admin_user, building, category, 5000).data["id"]
    resp = _client(admin_user).patch(f"/api/v1/expenses/{expense_id}/", {"amount": "400"}, format="json")
    assert resp.data["approval_status"] == "approved" and _balances(residents) == [Decimal("100.00")] * 4


def test_custom_split_is_remembered_until_approval(admin_user, building, residents, category):
    chair = residents[0][0]
    _make_chair(building, chair)
    chosen = [str(residents[1][1].pk), str(residents[2][1].pk)]
    expense_id = _add(admin_user, building, category, 4000, split_type="custom", custom_split_apartments=chosen).data["id"]
    _client(chair).post(f"/api/v1/expenses/{expense_id}/approve/")
    assert _balances(residents) == [Decimal("0.00"), Decimal("2000.00"), Decimal("2000.00"), Decimal("0.00")]


def _vote(user, poll_id, apartment, option_id):
    return _client(user).post(f"/api/v1/governance/polls/{poll_id}/vote/", {"apartment_id": str(apartment.pk), "option_id": option_id}, format="json")


def test_residents_can_decide_by_vote(admin_user, building, residents, category):
    expense_id = _add(admin_user, building, category, 5000).data["id"]
    resp = _client(admin_user).post(f"/api/v1/expenses/{expense_id}/put-to-vote/", {}, format="json")
    assert resp.status_code == 201
    poll = Poll.objects.get()
    approve_option, reject_option = [str(o.pk) for o in poll.options.all()]

    for (user, apt), option in zip(residents, [approve_option, approve_option, approve_option, reject_option]):
        assert _vote(user, poll.pk, apt, option).status_code == 200
    assert _client(admin_user).post(f"/api/v1/governance/polls/{poll.pk}/close/").status_code == 200

    expense = Expense.objects.get()
    assert expense.approval_status == "approved" and _balances(residents) == [Decimal("1250.00")] * 4


def test_a_losing_vote_rejects_and_a_tie_leaves_it_pending(admin_user, building, residents, category):
    first = _add(admin_user, building, category, 5000).data["id"]
    _client(admin_user).post(f"/api/v1/expenses/{first}/put-to-vote/", {}, format="json")
    poll = Poll.objects.get(expense_id=first)
    approve_option, reject_option = [str(o.pk) for o in poll.options.all()]
    for (user, apt), option in zip(residents, [reject_option, reject_option, reject_option, approve_option]):
        _vote(user, poll.pk, apt, option)
    _client(admin_user).post(f"/api/v1/governance/polls/{poll.pk}/close/")
    assert Expense.objects.get(pk=first).approval_status == "rejected"

    second = _add(admin_user, building, category, 6000, title="Another").data["id"]
    _client(admin_user).post(f"/api/v1/expenses/{second}/put-to-vote/", {}, format="json")
    poll2 = Poll.objects.get(expense_id=second)
    a2, r2 = [str(o.pk) for o in poll2.options.all()]
    for (user, apt), option in zip(residents, [a2, a2, r2, r2]):
        _vote(user, poll2.pk, apt, option)
    _client(admin_user).post(f"/api/v1/governance/polls/{poll2.pk}/close/")
    assert Expense.objects.get(pk=second).approval_status == "pending"        # tie: not decided


def test_the_daily_job_settles_polls_whose_time_is_up(admin_user, building, residents, category):
    expense_id = _add(admin_user, building, category, 5000).data["id"]
    _client(admin_user).post(f"/api/v1/expenses/{expense_id}/put-to-vote/", {}, format="json")
    poll = Poll.objects.get()
    approve_option = str(poll.options.first().pk)
    for user, apt in residents[:3]:
        _vote(user, poll.pk, apt, approve_option)
    assert finalize_polls(timezone.now()) == 0                                  # voting still open
    assert finalize_polls(timezone.now() + timedelta(days=4)) == 1
    assert Expense.objects.get().approval_status == "approved"
    assert finalize_polls(timezone.now() + timedelta(days=5)) == 0              # settled once


def test_threshold_is_set_through_the_building_and_blank_means_no_rule(admin_user, building, residents, category):
    assert _client(admin_user).patch(f"/api/v1/buildings/{building.pk}/", {"approval_threshold": None}, format="json").status_code == 200
    assert _add(admin_user, building, category, 50000).data["approval_status"] == "approved"
