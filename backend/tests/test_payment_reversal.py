"""R-22: numbered receipts and payment reversals."""

from datetime import date
from decimal import Decimal

import pytest
from apps.apartments.models import Apartment
from apps.audit.models import AuditLog
from apps.buildings.models import Building
from apps.expenses.models import ApartmentExpense, Expense, ExpenseCategory
from apps.expenses.utils import paid_toward_expense
from apps.payments.models import Payment

pytestmark = pytest.mark.django_db


@pytest.fixture
def building(admin_user):
    return Building.objects.create(
        name="Tower",
        address="1 Nile St",
        admin=admin_user,
        starting_balance=Decimal("0"),
    )


@pytest.fixture
def unit(building):
    return Apartment.objects.create(building=building, unit_number="1", balance=Decimal("300.00"))


@pytest.fixture
def expense(building, unit, admin_user):
    category = ExpenseCategory.objects.create(building=building, name="Lift")
    exp = Expense.objects.create(
        building=building,
        category=category,
        title="Repair",
        amount=Decimal("300.00"),
        expense_date=date.today(),
        created_by=admin_user,
    )
    ApartmentExpense.objects.create(expense=exp, apartment=unit, share_amount=Decimal("300.00"))
    return exp


def _pay(client, unit, amount="100.00"):
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


def test_receipt_numbers_are_sequential_per_building(admin_client, admin_user, unit, django_user_model):
    first, second = _pay(admin_client, unit), _pay(admin_client, unit)
    assert (first["receipt_no"], second["receipt_no"]) == (1, 2)
    other = Building.objects.create(name="Other", address="x", admin=admin_user)
    other_unit = Apartment.objects.create(building=other, unit_number="1")
    assert _pay(admin_client, other_unit)["receipt_no"] == 1


def test_reverse_restores_balance_and_links_original(admin_client, unit, expense):
    original = _pay(admin_client, unit, "100.00")
    unit.refresh_from_db()
    assert unit.balance == Decimal("200.00")
    assert paid_toward_expense(expense, unit.pk) == Decimal("100.00")

    resp = admin_client.post(
        f"/api/v1/payments/{original['id']}/reverse/",
        {"reason": "Wrong unit"},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert str(resp.data["reversal_of"]) == str(original["id"])
    assert Decimal(resp.data["amount_paid"]) == Decimal("-100.00")
    assert resp.data["reversal_reason"] == "Wrong unit"
    assert resp.data["receipt_no"] == original["receipt_no"] + 1

    unit.refresh_from_db()
    assert unit.balance == Decimal("300.00")
    assert paid_toward_expense(expense, unit.pk) == Decimal("0.00")
    assert admin_client.get(f"/api/v1/payments/{original['id']}/").data["is_voided"] is True
    assert AuditLog.objects.filter(action="payment.reversed", entity_id=original["id"]).exists()


def test_reverse_requires_reason(admin_client, unit):
    original = _pay(admin_client, unit)
    for body in ({}, {"reason": "   "}):
        assert admin_client.post(f"/api/v1/payments/{original['id']}/reverse/", body, format="json").status_code == 400
    unit.refresh_from_db()
    assert unit.balance == Decimal("200.00")


def test_cannot_reverse_twice_or_reverse_a_reversal(admin_client, unit):
    original = _pay(admin_client, unit)
    url = f"/api/v1/payments/{original['id']}/reverse/"
    reversal = admin_client.post(url, {"reason": "oops"}, format="json")
    assert reversal.status_code == 201
    assert admin_client.post(url, {"reason": "again"}, format="json").status_code == 409
    again = admin_client.post(
        f"/api/v1/payments/{reversal.data['id']}/reverse/",
        {"reason": "x"},
        format="json",
    )
    assert again.status_code == 409
    unit.refresh_from_db()
    assert unit.balance == Decimal("300.00")


def test_treasury_counts_reversal_negatively(admin_client, building, unit):
    original = _pay(admin_client, unit, "100.00")
    _pay(admin_client, unit, "50.00")
    url = f"/api/v1/buildings/{building.pk}/treasury/"
    assert Decimal(admin_client.get(url).data["balance"]) == Decimal("150.00")
    admin_client.post(f"/api/v1/payments/{original['id']}/reverse/", {"reason": "oops"}, format="json")
    assert Decimal(admin_client.get(url).data["balance"]) == Decimal("50.00")


def _client_for(user):
    from rest_framework.test import APIClient
    from rest_framework_simplejwt.tokens import RefreshToken

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return client


def test_owner_and_other_admin_cannot_reverse(admin_client, owner_user, unit, django_user_model):
    original = _pay(admin_client, unit)
    url = f"/api/v1/payments/{original['id']}/reverse/"
    assert _client_for(owner_user).post(url, {"reason": "x"}, format="json").status_code == 403
    stranger = django_user_model.objects.create_user(
        email="s@abem.test",
        password="AdminPass1!",
        first_name="S",
        last_name="S",
        role="admin",
    )
    assert _client_for(stranger).post(url, {"reason": "x"}, format="json").status_code == 404
    unit.refresh_from_db()
    assert unit.balance == Decimal("200.00")


def test_payments_are_still_not_editable_or_deletable(admin_client, unit):
    original = _pay(admin_client, unit)
    url = f"/api/v1/payments/{original['id']}/"
    assert admin_client.patch(url, {"amount_paid": "1.00"}, format="json").status_code == 405
    assert admin_client.delete(url).status_code == 405
    assert Payment.objects.get(pk=original["id"]).amount_paid == Decimal("100.00")


def test_receipt_shows_number_and_voided(admin_client, unit):
    original = _pay(admin_client, unit)
    admin_client.post(f"/api/v1/payments/{original['id']}/reverse/", {"reason": "oops"}, format="json")
    resp = admin_client.get(f"/api/v1/payments/{original['id']}/receipt/")
    if resp.status_code == 503:
        pytest.skip("WeasyPrint is not available in this environment")
    assert resp.status_code == 200
    assert resp["Content-Disposition"].endswith('receipt_1.pdf"')


def test_reverse_legacy_links_split_exactly(admin_client, building, unit, admin_user):
    from apps.expenses.utils import has_payments
    from apps.payments.models import PaymentExpense

    category = ExpenseCategory.objects.create(building=building, name="Misc")
    expenses = []
    for i in range(3):
        exp = Expense.objects.create(
            building=building,
            category=category,
            title=f"E{i}",
            amount=Decimal("100.00"),
            expense_date=date.today(),
            created_by=admin_user,
        )
        ApartmentExpense.objects.create(expense=exp, apartment=unit, share_amount=Decimal("100.00"))
        expenses.append(exp)
    legacy = Payment.objects.create(
        apartment=unit,
        amount_paid=Decimal("100.00"),
        payment_date=date.today(),
        recorded_by=admin_user,
    )
    for exp in expenses:
        PaymentExpense.objects.create(payment=legacy, expense=exp, allocated_amount=None)

    resp = admin_client.post(f"/api/v1/payments/{legacy.pk}/reverse/", {"reason": "legacy"}, format="json")
    assert resp.status_code == 201, resp.data

    reversal = Payment.objects.get(reversal_of=legacy)
    assert sum(link.allocated_amount for link in reversal.payment_expenses.all()) == Decimal("-100.00")
    for exp in expenses:
        assert paid_toward_expense(exp, unit.pk) == Decimal("0")
        assert has_payments(exp) is False
