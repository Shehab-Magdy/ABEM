"""An owner/renter sees treasury, statement, annual report and dashboard figures only for buildings they belong to."""

from datetime import date
from decimal import Decimal

import pytest
from apps.apartments.models import Apartment
from apps.buildings.models import Building, UserBuilding
from apps.payments.models import Payment

pytestmark = pytest.mark.django_db


@pytest.fixture
def two_buildings(admin_user, owner_user, django_user_model):
    other = django_user_model.objects.create_user(
        email="other-owner@abem.test",
        password="Pass1234!x",
        first_name="O",
        last_name="Two",
        role="owner",
    )
    a = Building.objects.create(
        name="A", address="1 St", admin=admin_user, starting_balance=Decimal("100.00")
    )
    b = Building.objects.create(
        name="B", address="2 St", admin=admin_user, starting_balance=Decimal("900.00")
    )
    unit_a = Apartment.objects.create(building=a, unit_number="1", owner=owner_user)
    unit_a.owners.add(owner_user)
    unit_b = Apartment.objects.create(building=b, unit_number="1", owner=other)
    unit_b.owners.add(other)
    UserBuilding.objects.create(user=owner_user, building=a)
    UserBuilding.objects.create(user=other, building=b)
    today = date.today()
    Payment.objects.create(
        apartment=unit_a,
        amount_paid=Decimal("10.00"),
        payment_date=today,
        recorded_by=admin_user,
    )
    Payment.objects.create(
        apartment=unit_b,
        amount_paid=Decimal("77.00"),
        payment_date=today,
        recorded_by=admin_user,
    )
    return a, b


def test_owner_building_list_only_has_their_building(owner_client, two_buildings):
    a, b = two_buildings
    ids = {
        row["id"]
        for row in owner_client.get("/api/v1/buildings/?page_size=50").data["results"]
    }
    assert ids == {str(a.pk)}


@pytest.mark.parametrize(
    "path", ["treasury/", "statement/?month=2026-10", "annual-report/?year=2026"]
)
def test_owner_cannot_read_other_buildings_figures(owner_client, two_buildings, path):
    a, b = two_buildings
    assert owner_client.get(f"/api/v1/buildings/{b.pk}/{path}").status_code == 404


def test_owner_reads_own_treasury(owner_client, two_buildings):
    a, _ = two_buildings
    resp = owner_client.get(f"/api/v1/buildings/{a.pk}/treasury/")
    assert resp.status_code == 200
    assert Decimal(resp.data["balance"]) == Decimal("110.00")


def test_owner_dashboard_ignores_other_buildings(owner_client, two_buildings):
    _, b = two_buildings
    data = owner_client.get("/api/v1/dashboard/owner/").data
    amounts = [p["amount_paid"] for p in data["recent_payments"]]
    assert amounts == ["10.00"]


def test_admin_still_sees_all_their_buildings(admin_client, two_buildings):
    a, b = two_buildings
    ids = {
        row["id"]
        for row in admin_client.get("/api/v1/buildings/?page_size=50").data["results"]
    }
    assert ids == {str(a.pk), str(b.pk)}
    assert admin_client.get(f"/api/v1/buildings/{b.pk}/treasury/").status_code == 200
