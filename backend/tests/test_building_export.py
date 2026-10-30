"""Full building XLSX export: admin only, scoped to managed buildings."""

import io
from datetime import date
from decimal import Decimal

import openpyxl
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.apartments.models import Apartment
from apps.audit.models import AuditLog
from apps.buildings.models import Building
from apps.expenses.models import (ApartmentExpense, Expense, ExpenseCategory,
                                  ExpenseKind, LateFee)
from apps.payments.models import Payment, PaymentClaim

pytestmark = pytest.mark.django_db

User = get_user_model()


def _url(building):
    return f"/api/v1/exports/building/{building.pk}/"


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def _sheets(response):
    wb = openpyxl.load_workbook(io.BytesIO(response.content))
    return {
        ws.title: [[c for c in row] for row in ws.iter_rows(values_only=True)]
        for ws in wb.worksheets
    }


@pytest.fixture
def building(admin_user):
    return Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user)


@pytest.fixture
def populated(building, admin_user, owner_user):
    unit = Apartment.objects.create(
        building=building, unit_number="7", owner=owner_user
    )
    unit.owners.add(owner_user)
    renter = User.objects.create_user(
        email="renter@abem.test", password="RenterPass1!", role="renter"
    )
    unit.owners.add(renter)
    category = ExpenseCategory.objects.create(building=building, name="Cleaning")
    expense = Expense.objects.create(
        building=building,
        category=category,
        title="Stairs",
        amount=Decimal("100.00"),
        expense_date=date(2026, 10, 1),
    )
    share = ApartmentExpense.objects.create(
        apartment=unit, expense=expense, share_amount=Decimal("100.00")
    )
    fee = Expense.objects.create(
        building=building,
        category=category,
        title="Late fee",
        amount=Decimal("5.00"),
        expense_date=date(2026, 10, 20),
        kind=ExpenseKind.LATE_FEE,
    )
    LateFee.objects.create(share=share, expense=fee)
    pay = Payment.objects.create(
        apartment=unit,
        amount_paid=Decimal("40.00"),
        payment_date=date(2026, 10, 5),
        recorded_by=admin_user,
    )
    Payment.objects.create(
        apartment=unit,
        amount_paid=Decimal("-40.00"),
        payment_date=date(2026, 10, 6),
        recorded_by=admin_user,
        reversal_of=pay,
        reversal_reason="entered twice",
    )
    PaymentClaim.objects.create(
        apartment=unit, amount=Decimal("10.00"), reference="IP-1", created_by=owner_user
    )
    AuditLog.objects.create(
        user=admin_user, action="create", entity="expense", entity_id=expense.pk
    )
    return unit


def test_admin_downloads_workbook_with_all_sheets(admin_user, building, populated):
    resp = _client(admin_user).get(_url(building))
    assert resp.status_code == 200
    assert resp["Content-Type"].endswith("spreadsheetml.sheet")
    sheets = _sheets(resp)
    assert list(sheets) == [
        "Units",
        "Residents",
        "Expenses",
        "Payments",
        "Claims",
        "Late fees",
        "Audit log",
    ]
    assert [r[0] for r in sheets["Units"][1:]] == ["7"]
    assert {r[1] for r in sheets["Residents"][1:]} == {"owner", "renter"}
    assert {r[1] for r in sheets["Expenses"][1:]} == {"Stairs", "Late fee"}
    assert len(sheets["Payments"]) == 3  # header + payment + its reversal
    assert any(
        r[8] for r in sheets["Payments"][1:]
    )  # the reversal row references the original
    assert sheets["Claims"][1][3] == "IP-1"
    assert len(sheets["Late fees"]) == 2
    assert any(r[2] == "create" and r[3] == "expense" for r in sheets["Audit log"][1:])


def test_other_admin_cannot_export_my_building(building, populated):
    other = User.objects.create_user(
        email="other@abem.test", password="OtherPass1!", role="admin"
    )
    Building.objects.create(name="Elsewhere", address="2 Nile St", admin=other)
    assert _client(other).get(_url(building)).status_code == 404


def test_export_excludes_other_buildings_data(admin_user, building, populated):
    other_admin = User.objects.create_user(
        email="other@abem.test", password="OtherPass1!", role="admin"
    )
    theirs = Building.objects.create(
        name="Elsewhere", address="2 Nile St", admin=other_admin
    )
    Apartment.objects.create(building=theirs, unit_number="SECRET")
    theirs_unit = Apartment.objects.get(building=theirs, unit_number="SECRET")
    # a co-admin shared by both buildings acts on the OTHER building's entities
    shared = User.objects.create_user(
        email="shared@abem.test", password="SharedPass1!", role="admin"
    )
    building.co_admins.add(shared)
    theirs.co_admins.add(shared)
    AuditLog.objects.create(
        user=shared, action="update", entity="apartment", entity_id=theirs_unit.pk
    )
    AuditLog.objects.create(
        user=shared,
        action="create",
        entity="plan_payment",
        entity_id=None,
        changes={"building_id": str(theirs.pk)},
    )
    sheets = _sheets(_client(admin_user).get(_url(building)))
    assert "SECRET" not in {r[0] for r in sheets["Units"]}
    assert "shared@abem.test" not in {r[1] for r in sheets["Audit log"]}


def test_owner_cannot_export(owner_user, building):
    assert _client(owner_user).get(_url(building)).status_code == 403


def test_anonymous_cannot_export(building):
    assert APIClient().get(_url(building)).status_code == 401


def test_formula_like_strings_are_neutralised(admin_user, building):
    Apartment.objects.create(building=building, unit_number="=1+1", floor=-1)
    Apartment.objects.create(building=building, unit_number="@SUM(A1)")
    sheets = _sheets(_client(admin_user).get(_url(building)))
    units = {r[0] for r in sheets["Units"][1:]}
    assert units == {"'=1+1", "'@SUM(A1)"}


def test_safe_cell_leaves_numbers_and_dates_alone():
    from apps.exports.safe import safe_cell

    assert safe_cell(5) == 5
    assert safe_cell(date(2026, 1, 1)) == date(2026, 1, 1)
    assert safe_cell("-5 off") == "'-5 off"
    assert safe_cell("plain") == "plain"
