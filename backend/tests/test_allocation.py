"""Payment allocation: validated, capped at what is owed, and automatic when not given."""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.apartments.models import Apartment
from apps.buildings.models import Building
from apps.expenses.models import ApartmentExpense, Expense, ExpenseCategory
from apps.expenses.utils import paid_toward_expense
from apps.payments.models import Payment, PaymentExpense

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup(admin_user):
    building = Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user)
    unit = Apartment.objects.create(building=building, unit_number="1", balance=Decimal("300.00"))
    category = ExpenseCategory.objects.create(building=building, name="Lift")

    def expense(title, amount, days_ago):
        e = Expense.objects.create(
            building=building, category=category, title=title, amount=Decimal(amount),
            expense_date=date.today() - timedelta(days=days_ago), created_by=admin_user,
        )
        ApartmentExpense.objects.create(expense=e, apartment=unit, share_amount=Decimal(amount))
        return e

    old, new = expense("Old", "100.00", 30), expense("New", "200.00", 5)
    client = APIClient()
    client.force_authenticate(admin_user)
    return {"building": building, "unit": unit, "old": old, "new": new, "client": client, "expense": expense}


def _pay(s, amount, **extra):
    return s["client"].post(
        "/api/v1/payments/",
        {"apartment_id": str(s["unit"].pk), "amount_paid": amount, "payment_date": str(date.today()),
         "payment_method": "cash", **extra},
        format="json",
    )


def _paid(s, key):
    return paid_toward_expense(s[key], s["unit"].pk)


def test_payment_without_allocations_pays_the_oldest_expense_first(setup):
    assert _pay(setup, "150.00").status_code == 201
    assert _paid(setup, "old") == Decimal("100.00")
    assert _paid(setup, "new") == Decimal("50.00")


def test_automatic_split_stays_within_the_selected_expenses(setup):
    resp = _pay(setup, "150.00", expense_ids=[str(setup["new"].pk)])
    assert resp.status_code == 201
    assert _paid(setup, "new") == Decimal("150.00") and _paid(setup, "old") == Decimal("0.00")


def test_overpayment_is_credit_not_over_allocated(setup):
    assert _pay(setup, "500.00").status_code == 201
    assert _paid(setup, "old") == Decimal("100.00") and _paid(setup, "new") == Decimal("200.00")
    setup["unit"].refresh_from_db()
    assert setup["unit"].balance == Decimal("-200.00")  # 300 - 500: credit


def test_manual_allocation_is_used_when_valid(setup):
    rows = [{"expense_id": str(setup["new"].pk), "allocated_amount": 120}]
    assert _pay(setup, "120.00", expense_ids=[str(setup["new"].pk)], allocations=rows).status_code == 201
    assert _paid(setup, "new") == Decimal("120.00")


def test_cannot_allocate_more_than_the_unit_owes_on_an_expense(setup):
    rows = [{"expense_id": str(setup["old"].pk), "allocated_amount": 150}]
    resp = _pay(setup, "150.00", allocations=rows)
    assert resp.status_code == 400
    assert not Payment.objects.exists()


def test_cannot_allocate_to_an_expense_the_unit_does_not_owe(setup, admin_user):
    other_building = Building.objects.create(name="Other", address="9 Elm", admin=admin_user)
    other = Expense.objects.create(
        building=other_building, category=ExpenseCategory.objects.create(building=other_building, name="X"),
        title="Elsewhere", amount=Decimal("50.00"), expense_date=date.today(), created_by=admin_user,
    )
    rows = [{"expense_id": str(other.pk), "allocated_amount": 50}]
    assert _pay(setup, "50.00", allocations=rows).status_code == 400
    assert not PaymentExpense.objects.exists()


def test_negative_and_duplicate_allocations_are_rejected(setup):
    old = str(setup["old"].pk)
    assert _pay(setup, "10.00", allocations=[{"expense_id": old, "allocated_amount": -5}]).status_code == 400
    dup = [{"expense_id": old, "allocated_amount": 5}, {"expense_id": old, "allocated_amount": 5}]
    assert _pay(setup, "10.00", allocations=dup).status_code == 400



def test_confirmed_instapay_claim_is_allocated_oldest_first(setup, owner_user):
    unit = setup["unit"]
    unit.owner = owner_user
    unit.save()
    unit.owners.add(owner_user)
    resident = APIClient()
    resident.force_authenticate(owner_user)
    claim = resident.post(
        "/api/v1/payments/claims/", {"apartment_id": str(unit.pk), "amount": "150.00", "reference": "IP-1"}, format="json"
    )
    assert claim.status_code == 201
    assert setup["client"].post(f"/api/v1/payments/claims/{claim.data['id']}/confirm/").status_code == 200
    assert _paid(setup, "old") == Decimal("100.00") and _paid(setup, "new") == Decimal("50.00")
