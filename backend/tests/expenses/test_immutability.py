"""R-24: an expense that has been paid toward cannot be deleted or have its money changed."""

from datetime import date
from decimal import Decimal

import pytest
from apps.apartments.models import Apartment
from apps.buildings.models import Building
from apps.expenses.models import ApartmentExpense, Expense, ExpenseCategory

pytestmark = pytest.mark.django_db


@pytest.fixture
def setup(admin_user):
    building = Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user)
    units = [Apartment.objects.create(building=building, unit_number=str(i)) for i in (1, 2)]
    category = ExpenseCategory.objects.create(building=building, name="Lift")
    expense = Expense.objects.create(
        building=building,
        category=category,
        title="Repair",
        amount=Decimal("200.00"),
        expense_date=date.today(),
        created_by=admin_user,
        approval_status="approved",
    )
    for unit in units:
        ApartmentExpense.objects.create(expense=expense, apartment=unit, share_amount=Decimal("100.00"))
        unit.balance = Decimal("100.00")
        unit.save()
    return {"building": building, "units": units, "expense": expense}


def _pay(client, unit, amount="40.00"):
    resp = client.post(
        "/api/v1/payments/",
        {
            "apartment_id": str(unit.pk),
            "amount_paid": amount,
            "payment_date": str(date.today()),
            "payment_method": "cash",
        },
        format="json",
    )
    assert resp.status_code == 201, resp.data
    return resp.data


def _url(setup):
    return f"/api/v1/expenses/{setup['expense'].pk}/"


def test_unpaid_expense_can_be_edited_and_deleted(admin_client, setup):
    assert admin_client.patch(_url(setup), {"amount": "300.00"}, format="json").status_code == 200
    assert admin_client.delete(_url(setup)).status_code == 204


def test_paid_expense_cannot_be_deleted(admin_client, setup):
    _pay(admin_client, setup["units"][0])
    resp = admin_client.delete(_url(setup))
    assert resp.status_code == 400
    assert "credit note" in str(resp.data).lower() or "revers" in str(resp.data).lower()
    setup["expense"].refresh_from_db()
    assert setup["expense"].deleted_at is None


@pytest.mark.parametrize("body", [{"amount": "999.00"}, {"split_type": "equal_apartments"}])
def test_paid_expense_money_cannot_change(admin_client, setup, body):
    _pay(admin_client, setup["units"][0])
    resp = admin_client.patch(_url(setup), body, format="json")
    assert resp.status_code == 400
    setup["expense"].refresh_from_db()
    assert setup["expense"].amount == Decimal("200.00")
    assert setup["expense"].apartment_expenses.count() == 2


def test_paid_expense_units_cannot_change(admin_client, setup):
    _pay(admin_client, setup["units"][0])
    resp = admin_client.patch(
        _url(setup),
        {"split_type": "custom", "custom_split_apartments": [str(setup["units"][1].pk)]},
        format="json",
    )
    assert resp.status_code == 400
    assert setup["expense"].apartment_expenses.count() == 2


def test_paid_expense_text_edit_keeps_shares_and_balances(admin_client, setup):
    _pay(admin_client, setup["units"][0])
    resp = admin_client.patch(_url(setup), {"title": "Renamed", "amount": "200.00"}, format="json")
    assert resp.status_code == 200
    setup["expense"].refresh_from_db()
    assert setup["expense"].title == "Renamed"
    shares = {ae.apartment_id: ae.share_amount for ae in setup["expense"].apartment_expenses.all()}
    assert set(shares.values()) == {Decimal("100.00")}
    setup["units"][0].refresh_from_db()
    assert setup["units"][0].balance == Decimal("60.00")


def test_fully_reversed_payment_unlocks_the_expense(admin_client, setup):
    payment = _pay(admin_client, setup["units"][0])
    assert (
        admin_client.post(
            f"/api/v1/payments/{payment['id']}/reverse/", {"reason": "mistake"}, format="json"
        ).status_code
        == 201
    )
    assert admin_client.patch(_url(setup), {"amount": "300.00"}, format="json").status_code == 200
