"""Monthly subscription: billed once per month, skips paused units, never counts as a building cost."""
from datetime import date
from decimal import Decimal

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.apartments.models import Apartment
from apps.buildings.models import Building
from apps.expenses.models import Expense, ExpenseKind, SubscriptionPlan
from apps.expenses.subscriptions import bill_subscriptions
from apps.notifications.reminders import send_payment_reminders
from apps.payments.models import Payment

pytestmark = pytest.mark.django_db


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def building(admin_user):
    return Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user, starting_balance=Decimal("1000.00"))


@pytest.fixture
def units(building, owner_user):
    made = [Apartment.objects.create(building=building, unit_number=str(n)) for n in (1, 2, 3)]
    made[0].owner = owner_user
    made[0].save()
    made[0].owners.add(owner_user)
    return made


@pytest.fixture
def plan(building):
    from apps.plans.models import BuildingPlan

    # a paid plan, so the test dates below are not past the new-building trial
    BuildingPlan.objects.create(building=building, plan_id="standard", paid_until=date(2027, 12, 31))
    return SubscriptionPlan.objects.create(
        building=building, amount=Decimal("150.00"), billing_day=5, due_days=10, starts_on=date(2026, 10, 1)
    )


def _balances(units):
    return [Apartment.objects.get(pk=u.pk).balance for u in units]


def test_each_unit_is_charged_on_the_billing_day(plan, units):
    assert bill_subscriptions(date(2026, 10, 4)) == 0          # not yet the 5th
    assert bill_subscriptions(date(2026, 10, 5)) == 1
    assert _balances(units) == [Decimal("150.00")] * 3
    charge = Expense.objects.get(kind=ExpenseKind.SUBSCRIPTION)
    assert charge.amount == Decimal("450.00") and charge.due_date == date(2026, 10, 15)
    assert charge.apartment_expenses.count() == 3


def test_a_month_is_billed_only_once(plan, units):
    bill_subscriptions(date(2026, 10, 5))
    assert bill_subscriptions(date(2026, 10, 20)) == 0
    assert _balances(units) == [Decimal("150.00")] * 3


def test_missed_months_are_caught_up(plan, units):
    assert bill_subscriptions(date(2026, 12, 6)) == 3           # Oct, Nov, Dec
    assert _balances(units) == [Decimal("450.00")] * 3


def test_paused_units_are_skipped(plan, units):
    units[2].billing_paused = True
    units[2].save()
    bill_subscriptions(date(2026, 10, 5))
    assert _balances(units) == [Decimal("150.00"), Decimal("150.00"), Decimal("0.00")]
    assert Expense.objects.get().amount == Decimal("300.00")


def test_inactive_plans_and_buildings_without_units_do_nothing(plan, building):
    assert bill_subscriptions(date(2026, 10, 5)) == 0            # no units yet
    plan.is_active = False
    plan.save()
    assert bill_subscriptions(date(2026, 10, 5)) == 0


def test_a_subscription_is_not_a_building_cost(plan, units, admin_user):
    bill_subscriptions(date(2026, 10, 5))
    Payment.objects.create(apartment=units[0], amount_paid=Decimal("150.00"), payment_date=date(2026, 10, 6), recorded_by=admin_user)

    treasury = _client(admin_user).get(f"/api/v1/buildings/{plan.building_id}/treasury/").data
    assert Decimal(treasury["balance"]) == Decimal("1150.00")    # 1000 start + 150 paid; the 450 billed is not spent
    assert Decimal(treasury["total_expenses"]) == Decimal("0.00")

    statement = _client(admin_user).get(f"/api/v1/buildings/{plan.building_id}/statement/", {"month": "2026-10"}).data
    assert Decimal(statement["total_expenses"]) == Decimal("0.00")
    assert Decimal(statement["closing_balance"]) == Decimal("1150.00")

    dash = _client(admin_user).get("/api/v1/dashboard/admin/").data
    assert Decimal(dash["total_expenses"]) == Decimal("0.00")


def test_owners_get_reminders_for_unpaid_subscriptions(plan, units, owner_user):
    bill_subscriptions(date(2026, 10, 5))
    counts = send_payment_reminders(date(2026, 10, 16))          # due on the 15th
    assert counts["overdue"] == 1                                # only the unit that has an owner is reminded
    assert owner_user.notifications.count() == 1


def test_command_runs(plan, units, capsys):
    call_command("bill_subscriptions")
    assert "subscription charge" in capsys.readouterr().out


def test_admin_sets_the_plan_and_residents_cannot(admin_user, building, owner_user):
    url = f"/api/v1/buildings/{building.pk}/subscription/"
    assert _client(admin_user).get(url).data == {"plan": None}
    resp = _client(admin_user).post(url, {"amount": "200", "billing_day": 3, "due_days": 7}, format="json")
    assert resp.status_code == 200 and resp.data["plan"]["amount"] == "200.00"
    assert SubscriptionPlan.objects.get(building=building).billing_day == 3
    assert _client(owner_user).post(url, {"amount": "1"}, format="json").status_code in (403, 404)


def test_plan_validation_and_building_scope(admin_user, building, django_user_model):
    url = f"/api/v1/buildings/{building.pk}/subscription/"
    for bad in ({"amount": "0"}, {"amount": "abc"}, {"amount": "100", "billing_day": 31}, {"amount": "100", "due_days": 99}):
        assert _client(admin_user).post(url, bad, format="json").status_code == 400
    outsider = django_user_model.objects.create_user(email="x@abem.test", password="XPass1!xxx", role="admin")
    assert _client(outsider).post(url, {"amount": "100"}, format="json").status_code == 404


def test_admin_can_pause_a_unit_through_the_unit_api(admin_user, units):
    resp = _client(admin_user).patch(
        f"/api/v1/apartments/{units[1].pk}/", {"billing_paused": True, "billing_pause_reason": "Vacant"}, format="json"
    )
    assert resp.status_code == 200 and resp.data["billing_paused"] is True


def test_expense_list_labels_and_filters_by_kind(plan, units, admin_user, building):
    from apps.expenses.models import ExpenseCategory

    bill_subscriptions(date(2026, 10, 5))
    category = ExpenseCategory.objects.create(building=building, name="Lift")
    Expense.objects.create(building=building, category=category, title="Repair", amount=Decimal("90.00"),
                           expense_date=date(2026, 10, 6), created_by=admin_user)
    url = f"/api/v1/expenses/?building_id={building.pk}"
    everything = _client(admin_user).get(url).data["results"]
    assert {e["kind"] for e in everything} == {"cost", "subscription"}
    only_subs = _client(admin_user).get(url + "&kind=subscription").data["results"]
    assert [e["kind"] for e in only_subs] == ["subscription"]
    assert [e["kind"] for e in _client(admin_user).get(url + "&kind=cost").data["results"]] == ["cost"]


def test_kind_cannot_be_set_through_the_expense_api(admin_user, building):
    from apps.expenses.models import ExpenseCategory

    category = ExpenseCategory.objects.create(building=building, name="Lift")
    resp = _client(admin_user).post("/api/v1/expenses/", {
        "building_id": str(building.pk), "category_id": str(category.pk), "title": "Sneaky", "amount": "50.00",
        "expense_date": "2026-10-06", "split_type": "equal_all", "kind": "subscription",
    }, format="json")
    assert resp.status_code == 201 and Expense.objects.get(title="Sneaky").kind == "cost"
