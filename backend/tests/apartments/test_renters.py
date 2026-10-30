"""Renters: invited by the unit's owner or admin, see only their unit, cannot claim or invite."""
from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.apartments.models import Apartment
from apps.buildings.models import Building
from apps.expenses.models import ApartmentExpense, Expense, ExpenseCategory
from apps.payments.models import Payment

pytestmark = pytest.mark.django_db


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def building(admin_user):
    return Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user)


@pytest.fixture
def unit(building, owner_user):
    apt = Apartment.objects.create(building=building, unit_number="3A", owner=owner_user, balance=Decimal("100.00"))
    apt.owners.add(owner_user)
    from apps.buildings.models import UserBuilding

    UserBuilding.objects.create(user=owner_user, building=building)
    return apt


@pytest.fixture
def other_unit(building, django_user_model):
    neighbour = django_user_model.objects.create_user(email="n@abem.test", password="NPass1!xxx", role="owner")
    return Apartment.objects.create(building=building, unit_number="4B", owner=neighbour, balance=Decimal("500.00"))


@pytest.fixture
def renter(django_user_model):
    return django_user_model.objects.create_user(email="renter@abem.test", password="RPass1!xxx", role="renter")


def _invite_and_join(owner_user, unit, renter):
    token = _client(owner_user).post(f"/api/v1/apartments/{unit.pk}/invite-renter/", {}, format="json").data["token"]
    return _client(renter).post("/api/v1/apartments/invite/use/", {"token": token}, format="json")


def test_owner_invites_a_renter_who_joins_the_unit(owner_user, unit, renter):
    info = _client(owner_user).post(f"/api/v1/apartments/{unit.pk}/invite-renter/", {}, format="json")
    assert info.status_code == 201
    token = info.data["token"]
    assert APIClient().get("/api/v1/apartments/invite/validate/", {"token": token}).data["role"] == "renter"

    assert _client(renter).post("/api/v1/apartments/invite/use/", {"token": token}, format="json").status_code == 200
    unit.refresh_from_db()
    assert unit.owner is not None and unit.owner != renter       # renter never becomes the owner
    assert unit.owners.filter(pk=renter.pk).exists()
    assert renter.buildings.filter(pk=unit.building_id).exists()
    assert [r["name"] for r in _client(unit.owner).get(f"/api/v1/apartments/{unit.pk}/").data["renters"]] == [renter.email]
    assert renter.email not in _client(unit.owner).get(f"/api/v1/apartments/{unit.pk}/").data["owner_names"]


def test_renter_joining_a_vacant_unit_does_not_make_them_the_owner(admin_user, building, renter):
    vacant = Apartment.objects.create(building=building, unit_number="9")
    token = _client(admin_user).post(f"/api/v1/apartments/{vacant.pk}/invite-renter/", {}, format="json").data["token"]
    assert _client(renter).post("/api/v1/apartments/invite/use/", {"token": token}, format="json").status_code == 200
    vacant.refresh_from_db()
    assert vacant.owner is None and vacant.owners.filter(pk=renter.pk).exists()


def test_renter_sees_only_their_unit(owner_user, unit, other_unit, renter):
    _invite_and_join(owner_user, unit, renter)
    c = _client(renter)
    assert [a["unit_number"] for a in c.get("/api/v1/apartments/").data["results"]] == ["3A"]
    in_building = c.get(f"/api/v1/buildings/{unit.building_id}/apartments/").data
    rows = in_building["results"] if isinstance(in_building, dict) else in_building
    assert [a["unit_number"] for a in rows] == ["3A"]
    assert c.get(f"/api/v1/apartments/{other_unit.pk}/").status_code == 404


def test_renter_can_pay_see_the_treasury_and_statement(owner_user, unit, renter):
    _invite_and_join(owner_user, unit, renter)
    c = _client(renter)
    assert c.get(f"/api/v1/buildings/{unit.building_id}/treasury/").status_code == 200
    assert c.get(f"/api/v1/buildings/{unit.building_id}/statement/").status_code == 200
    claim = c.post("/api/v1/payments/claims/", {"apartment_id": str(unit.pk), "amount": "40.00"}, format="json")
    assert claim.status_code == 201


def test_renter_cannot_claim_units_or_invite_others(owner_user, unit, other_unit, renter):
    _invite_and_join(owner_user, unit, renter)
    c = _client(renter)
    assert c.post(f"/api/v1/apartments/{other_unit.pk}/claim/").status_code == 403
    assert c.post(f"/api/v1/apartments/{unit.pk}/invite-renter/", {}, format="json").status_code == 403
    assert c.post(f"/api/v1/apartments/{unit.pk}/remove-renter/", {"user_id": str(renter.pk)}, format="json").status_code == 403


def test_owner_can_end_a_renters_link(owner_user, unit, renter):
    _invite_and_join(owner_user, unit, renter)
    resp = _client(owner_user).post(f"/api/v1/apartments/{unit.pk}/remove-renter/", {"user_id": str(renter.pk)}, format="json")
    assert resp.status_code == 200
    assert not unit.owners.filter(pk=renter.pk).exists()
    assert not renter.buildings.filter(pk=unit.building_id).exists()
    assert _client(renter).get(f"/api/v1/apartments/{unit.pk}/").status_code == 404


def test_strangers_cannot_invite_renters_to_someone_elses_unit(unit, other_unit, owner_user):
    # owner_user owns 3A, not 4B
    assert _client(owner_user).post(f"/api/v1/apartments/{other_unit.pk}/invite-renter/", {}, format="json").status_code == 404


def test_renter_can_report_maintenance_and_receives_reminders(owner_user, unit, renter, admin_user):
    from apps.notifications.reminders import send_payment_reminders

    _invite_and_join(owner_user, unit, renter)
    report = _client(renter).post(
        "/api/v1/maintenance/", {"building_id": str(unit.building_id), "category": "elevator"}, format="json"
    )
    assert report.status_code == 201

    category = ExpenseCategory.objects.create(building=unit.building, name="Lift")
    expense = Expense.objects.create(
        building=unit.building, category=category, title="Lift", amount=Decimal("100.00"),
        expense_date=date(2026, 10, 1), due_date=date(2026, 10, 2), created_by=admin_user,
    )
    ApartmentExpense.objects.create(expense=expense, apartment=unit, share_amount=Decimal("100.00"))
    send_payment_reminders(date(2026, 10, 10))
    assert renter.notifications.count() == 1 and owner_user.notifications.count() == 1
