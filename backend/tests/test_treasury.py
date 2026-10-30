"""Treasury = starting balance + payments + asset sales - expenses, per building."""
from datetime import date
from decimal import Decimal

import pytest

from apps.apartments.models import Apartment
from apps.buildings.models import Building, UserBuilding
from apps.expenses.models import Expense, ExpenseCategory
from apps.payments.models import Payment

pytestmark = pytest.mark.django_db


@pytest.fixture
def building(admin_user):
    return Building.objects.create(
        name="Tower", address="1 Nile St", admin=admin_user, starting_balance=Decimal("1000.00")
    )


@pytest.fixture
def activity(building, admin_user):
    unit = Apartment.objects.create(building=building, unit_number="1")
    category = ExpenseCategory.objects.create(building=building, name="Lift")
    Expense.objects.create(
        building=building, category=category, title="Repair", amount=Decimal("300.00"),
        expense_date=date.today(), created_by=admin_user,
    )
    Payment.objects.create(
        apartment=unit, amount_paid=Decimal("500.00"), payment_date=date.today(), recorded_by=admin_user
    )


def test_balance_is_start_plus_received_minus_spent(admin_client, building, activity):
    resp = admin_client.get(f"/api/v1/buildings/{building.pk}/treasury/")
    assert resp.status_code == 200
    assert Decimal(resp.data["balance"]) == Decimal("1200.00")  # 1000 + 500 - 300


def test_residents_can_view_but_not_edit(api_client, owner_user, building, activity):
    UserBuilding.objects.create(user=owner_user, building=building)
    api_client.force_authenticate(owner_user)
    assert api_client.get(f"/api/v1/buildings/{building.pk}/treasury/").status_code == 200
    assert api_client.patch(f"/api/v1/buildings/{building.pk}/", {"starting_balance": "0"}, format="json").status_code == 403


def test_strangers_cannot_view_another_buildings_treasury(api_client, owner_user, building, activity):
    api_client.force_authenticate(owner_user)
    assert api_client.get(f"/api/v1/buildings/{building.pk}/treasury/").status_code == 404
