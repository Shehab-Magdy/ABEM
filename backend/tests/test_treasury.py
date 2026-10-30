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


# ── R-29 ─────────────────────────────────────────────────────────────────────

def _billed(building, admin_user):
    from apps.expenses.models import ApartmentExpense

    category = ExpenseCategory.objects.create(building=building, name="Lift")
    expense = Expense.objects.create(
        building=building, category=category, title="Repair", amount=Decimal("200.00"),
        expense_date=date.today(), created_by=admin_user,
    )
    units = [Apartment.objects.create(building=building, unit_number=n) for n in ("1", "2")]
    for unit in units:
        ApartmentExpense.objects.create(expense=expense, apartment=unit, share_amount=Decimal("100.00"))
    return units


def test_credit_with_unpaid_shares_is_not_counted_as_paid(admin_client, building, admin_user):
    from apps.payments.models import PaymentExpense

    paid_unit, credit_unit = _billed(building, admin_user)
    expense = Expense.objects.get(building=building)
    payment = Payment.objects.create(
        apartment=paid_unit, amount_paid=Decimal("100.00"), payment_date=date.today(), recorded_by=admin_user
    )
    PaymentExpense.objects.create(payment=payment, expense=expense, allocated_amount=Decimal("100.00"))
    # a prepayment/credit that is not allocated to the share: balance is negative but the share is still unpaid
    Apartment.objects.filter(pk=credit_unit.pk).update(balance=Decimal("-50.00"))
    Apartment.objects.filter(pk=paid_unit.pk).update(balance=Decimal("0.00"))

    data = admin_client.get(f"/api/v1/buildings/{building.pk}/treasury/").data
    assert data["units_billed"] == 2 and data["units_paid"] == 1


def test_treasury_shows_reversals_and_sales_separately(admin_client, building, admin_user):
    from apps.payments.models import BuildingAsset

    unit = Apartment.objects.create(building=building, unit_number="1")
    original = Payment.objects.create(
        apartment=unit, amount_paid=Decimal("500.00"), payment_date=date.today(), recorded_by=admin_user
    )
    Payment.objects.create(
        apartment=unit, amount_paid=Decimal("-500.00"), payment_date=date.today(), recorded_by=admin_user,
        reversal_of=original,
    )
    asset = BuildingAsset.objects.create(building=building, name="Old lift", created_by=admin_user)
    from apps.payments.models import AssetSale

    AssetSale.objects.create(
        asset=asset, sale_date=date.today(), sale_price=Decimal("200.00"), recorded_by=admin_user
    )
    data = admin_client.get(f"/api/v1/buildings/{building.pk}/treasury/").data
    assert Decimal(data["total_reversals"]) == Decimal("500.00")
    assert Decimal(data["total_sales"]) == Decimal("200.00")
    assert Decimal(data["total_payments"]) == Decimal("500.00")
    assert Decimal(data["total_received"]) == Decimal("200.00")  # backward compatible: net payments + sales
    assert Decimal(data["balance"]) == Decimal("1200.00")
