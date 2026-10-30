"""R-21: writes cannot move a record to, or point it at, a building the caller does not manage."""

from datetime import date
from decimal import Decimal

import pytest
from apps.apartments.models import Apartment
from apps.buildings.models import Building
from apps.expenses.models import Expense, ExpenseCategory
from apps.payments.models import BuildingAsset

pytestmark = pytest.mark.django_db


@pytest.fixture
def other_admin(django_user_model):
    return django_user_model.objects.create_user(
        email="admin-b@abem.test", password="AdminPass1!", first_name="B", last_name="Admin", role="admin"
    )


@pytest.fixture
def mine(admin_user):
    building = Building.objects.create(name="Mine", address="1 A St", admin=admin_user)
    unit = Apartment.objects.create(building=building, unit_number="1")
    category = ExpenseCategory.objects.create(building=building, name="Mine cat")
    expense = Expense.objects.create(
        building=building,
        category=category,
        title="Mine exp",
        amount=Decimal("100.00"),
        expense_date=date.today(),
        created_by=admin_user,
    )
    asset = BuildingAsset.objects.create(building=building, name="Mine asset", created_by=admin_user)
    return {"building": building, "unit": unit, "category": category, "expense": expense, "asset": asset}


@pytest.fixture
def theirs(other_admin):
    building = Building.objects.create(name="Theirs", address="2 B St", admin=other_admin)
    category = ExpenseCategory.objects.create(building=building, name="Their cat")
    unit = Apartment.objects.create(building=building, unit_number="9")
    return {"building": building, "category": category, "unit": unit}


def test_unit_building_cannot_change(admin_client, mine, theirs):
    resp = admin_client.patch(
        f"/api/v1/apartments/{mine['unit'].pk}/", {"building_id": str(theirs["building"].pk)}, format="json"
    )
    assert resp.status_code in (400, 403)
    mine["unit"].refresh_from_db()
    assert mine["unit"].building_id == mine["building"].pk


def test_expense_building_cannot_change(admin_client, mine, theirs):
    resp = admin_client.patch(
        f"/api/v1/expenses/{mine['expense'].pk}/", {"building_id": str(theirs["building"].pk)}, format="json"
    )
    assert resp.status_code in (400, 403)
    mine["expense"].refresh_from_db()
    assert mine["expense"].building_id == mine["building"].pk


def test_expense_cannot_use_other_buildings_category_on_update(admin_client, mine, theirs):
    resp = admin_client.patch(
        f"/api/v1/expenses/{mine['expense'].pk}/", {"category_id": str(theirs["category"].pk)}, format="json"
    )
    assert resp.status_code in (400, 403)
    mine["expense"].refresh_from_db()
    assert mine["expense"].category_id == mine["category"].pk


def test_expense_cannot_be_created_with_other_buildings_category(admin_client, mine, theirs):
    resp = admin_client.post(
        "/api/v1/expenses/",
        {
            "building_id": str(mine["building"].pk),
            "category_id": str(theirs["category"].pk),
            "title": "x",
            "amount": "10.00",
            "expense_date": str(date.today()),
            "split_type": "equal_all",
        },
        format="json",
    )
    assert resp.status_code in (400, 403)


def test_custom_split_cannot_name_other_buildings_unit(admin_client, mine, theirs):
    resp = admin_client.post(
        "/api/v1/expenses/",
        {
            "building_id": str(mine["building"].pk),
            "category_id": str(mine["category"].pk),
            "title": "x",
            "amount": "10.00",
            "expense_date": str(date.today()),
            "split_type": "custom",
            "custom_split_apartments": [str(theirs["unit"].pk)],
        },
        format="json",
    )
    assert resp.status_code == 400
    theirs["unit"].refresh_from_db()
    assert theirs["unit"].balance == Decimal("0.00")


def test_asset_building_cannot_change(admin_client, mine, theirs):
    resp = admin_client.patch(
        f"/api/v1/payments/assets/{mine['asset'].pk}/", {"building_id": str(theirs["building"].pk)}, format="json"
    )
    assert resp.status_code in (400, 403)
    mine["asset"].refresh_from_db()
    assert mine["asset"].building_id == mine["building"].pk


def test_same_building_edits_still_work(admin_client, mine):
    assert (
        admin_client.patch(f"/api/v1/expenses/{mine['expense'].pk}/", {"title": "Renamed"}, format="json").status_code
        == 200
    )
    assert (
        admin_client.patch(
            f"/api/v1/apartments/{mine['unit'].pk}/",
            {"building_id": str(mine["building"].pk), "floor": 0},
            format="json",
        ).status_code
        == 200
    )
