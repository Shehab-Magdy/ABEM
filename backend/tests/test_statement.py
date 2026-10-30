"""Monthly statement: balances roll forward correctly and access follows the building."""
from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.apartments.models import Apartment
from apps.buildings.models import Building, UserBuilding
from apps.expenses.models import Expense, ExpenseCategory
from apps.payments.models import Payment

pytestmark = pytest.mark.django_db


@pytest.fixture
def building(admin_user):
    b = Building.objects.create(
        name="Tower", address="1 Nile St", admin=admin_user, starting_balance=Decimal("1000.00")
    )
    unit = Apartment.objects.create(building=b, unit_number="1", balance=Decimal("100.00"))
    other = Apartment.objects.create(building=b, unit_number="2")
    category = ExpenseCategory.objects.create(building=b, name="Lift")

    def pay(day, amount, apt=unit):
        Payment.objects.create(apartment=apt, amount_paid=Decimal(amount), payment_date=day, recorded_by=admin_user)

    def spend(day, amount, title="Lift"):
        Expense.objects.create(
            building=b, category=category, title=title, amount=Decimal(amount), expense_date=day, created_by=admin_user
        )

    pay(date(2026, 9, 20), "300.00")           # before October
    spend(date(2026, 9, 25), "100.00")         # before October
    pay(date(2026, 10, 1), "200.00")           # first day of October
    pay(date(2026, 10, 31), "50.00", other)    # last day of October
    spend(date(2026, 10, 15), "120.00", "October repair")
    pay(date(2026, 11, 1), "999.00")           # after October
    spend(date(2026, 11, 1), "999.00")         # after October
    return b


def _get(user, building, **params):
    client = APIClient()
    client.force_authenticate(user)
    return client.get(f"/api/v1/buildings/{building.pk}/statement/", params)


def test_month_numbers_roll_forward(admin_user, building):
    data = _get(admin_user, building, month="2026-10").data
    assert Decimal(data["opening_balance"]) == Decimal("1200.00")   # 1000 + 300 - 100
    assert Decimal(data["total_received"]) == Decimal("250.00")     # 200 + 50
    assert Decimal(data["total_expenses"]) == Decimal("120.00")
    assert Decimal(data["closing_balance"]) == Decimal("1330.00")
    assert [e["title"] for e in data["expenses"]] == ["October repair"]
    assert data["units_paid"] == 2 and data["units_total"] == 2


def test_next_month_opens_where_the_last_one_closed(admin_user, building):
    october = _get(admin_user, building, month="2026-10").data
    november = _get(admin_user, building, month="2026-11").data
    assert november["opening_balance"] == october["closing_balance"]


def test_statement_shows_unit_numbers_not_names(admin_user, owner_user, building):
    unit = building.apartments.get(unit_number="1")
    unit.owner = owner_user
    unit.save()
    row = _get(admin_user, building, month="2026-10").data["units"][0]
    assert set(row) == {"unit", "paid_this_month", "balance_due"}


def test_residents_can_view_but_strangers_cannot(owner_user, building, django_user_model):
    UserBuilding.objects.create(user=owner_user, building=building)
    assert _get(owner_user, building, month="2026-10").status_code == 200
    stranger = django_user_model.objects.create_user(email="s@abem.test", password="Pass1234!x", role="owner")
    assert _get(stranger, building, month="2026-10").status_code == 404


def test_other_admins_cannot_view(building, django_user_model):
    other = django_user_model.objects.create_user(email="b@abem.test", password="Pass1234!x", role="admin")
    assert _get(other, building, month="2026-10").status_code == 404


def test_bad_month_is_a_400(admin_user, building):
    assert _get(admin_user, building, month="october").status_code == 400
    assert _get(admin_user, building, month="2026-13").status_code == 400


def test_pdf_download_in_both_languages(admin_user, building):
    for lang in ("ar", "en"):
        admin_user.preferred_language = lang
        admin_user.save()
        resp = _get(admin_user, building, month="2026-10", file_format="pdf")
        assert resp.status_code == 200 and resp["Content-Type"] == "application/pdf"
        assert resp.content.startswith(b"%PDF")
