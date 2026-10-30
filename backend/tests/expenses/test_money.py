"""Expense splitting, balances and paid-amount accounting."""
from datetime import date
from decimal import Decimal

import pytest

from apps.apartments.models import Apartment
from apps.buildings.models import Building
from apps.expenses.models import ApartmentExpense, Expense, ExpenseCategory
from apps.expenses.utils import paid_toward_expense
from apps.payments.models import Payment, PaymentExpense

pytestmark = pytest.mark.django_db


@pytest.fixture
def building(admin_user):
    return Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user)


@pytest.fixture
def units(building):
    return [Apartment.objects.create(building=building, unit_number=str(n)) for n in (1, 2, 3)]


@pytest.fixture
def category(building):
    return ExpenseCategory.objects.create(building=building, name="Lift")


def _payload(building, category, **extra):
    return {
        "building_id": str(building.pk),
        "category_id": str(category.pk),
        "title": "Lift repair",
        "amount": "300.00",
        "expense_date": str(date.today()),
        **extra,
    }


def test_deleting_an_expense_reverses_apartment_balances(admin_client, building, units, category):
    resp = admin_client.post("/api/v1/expenses/", _payload(building, category, split_type="equal_all"), format="json")
    assert resp.status_code == 201, resp.data
    assert all(Apartment.objects.get(pk=u.pk).balance > 0 for u in units)

    assert admin_client.delete(f"/api/v1/expenses/{resp.data['id']}/").status_code == 204
    assert all(Apartment.objects.get(pk=u.pk).balance == Decimal("0.00") for u in units)


def test_editing_title_of_custom_split_keeps_the_same_units(admin_client, building, units, category):
    resp = admin_client.post(
        "/api/v1/expenses/",
        _payload(building, category, split_type="custom", custom_split_apartments=[str(units[0].pk), str(units[1].pk)]),
        format="json",
    )
    assert resp.status_code == 201, resp.data
    expense_id = resp.data["id"]

    assert admin_client.patch(f"/api/v1/expenses/{expense_id}/", {"title": "Renamed"}, format="json").status_code == 200
    shared = set(ApartmentExpense.objects.filter(expense_id=expense_id).values_list("apartment_id", flat=True))
    assert shared == {units[0].pk, units[1].pk}
    assert Apartment.objects.get(pk=units[2].pk).balance == Decimal("0.00")


def test_one_payment_over_several_expenses_is_split_not_counted_whole(building, units, admin_user, category):
    expenses = [
        Expense.objects.create(
            building=building, category=category, title=f"E{n}", amount=Decimal("100.00"),
            expense_date=date.today(), created_by=admin_user,
        )
        for n in range(5)
    ]
    payment = Payment.objects.create(
        apartment=units[0], amount_paid=Decimal("100.00"), payment_date=date.today(), recorded_by=admin_user
    )
    for expense in expenses:  # legacy payment: no allocations recorded
        PaymentExpense.objects.create(payment=payment, expense=expense)

    assert paid_toward_expense(expenses[0], units[0].pk) == Decimal("20.00")


def test_allocated_amount_is_used_when_recorded(building, units, admin_user, category):
    expense = Expense.objects.create(
        building=building, category=category, title="E", amount=Decimal("100.00"),
        expense_date=date.today(), created_by=admin_user,
    )
    payment = Payment.objects.create(
        apartment=units[0], amount_paid=Decimal("100.00"), payment_date=date.today(), recorded_by=admin_user
    )
    PaymentExpense.objects.create(payment=payment, expense=expense, allocated_amount=Decimal("65.00"))
    assert paid_toward_expense(expense, units[0].pk) == Decimal("65.00")
