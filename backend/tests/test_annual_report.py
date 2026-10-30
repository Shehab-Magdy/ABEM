"""Annual report: yearly totals roll forward, group correctly and follow the building's access rules."""
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
    unit = Apartment.objects.create(building=b, unit_number="1", balance=Decimal("75.00"))
    Apartment.objects.create(building=b, unit_number="2")
    lift = ExpenseCategory.objects.create(building=b, name="Lift")
    clean = ExpenseCategory.objects.create(building=b, name="Cleaning")

    def pay(day, amount):
        Payment.objects.create(apartment=unit, amount_paid=Decimal(amount), payment_date=day, recorded_by=admin_user)

    def spend(day, amount, category, **extra):
        Expense.objects.create(
            building=b, category=category, title="x", amount=Decimal(amount),
            expense_date=day, created_by=admin_user, **extra,
        )

    pay(date(2025, 12, 31), "500.00")     # last year
    spend(date(2025, 12, 30), "200.00", lift)
    pay(date(2026, 1, 5), "100.00")
    pay(date(2026, 1, 20), "50.00")
    pay(date(2026, 6, 1), "300.00")
    spend(date(2026, 3, 1), "120.00", lift)
    spend(date(2026, 3, 9), "30.00", clean)
    spend(date(2026, 3, 10), "999.00", clean, kind="subscription")  # a charge to units, not a cost
    spend(date(2026, 4, 1), "999.00", clean, approval_status="pending")  # not approved yet
    pay(date(2027, 1, 1), "999.00")       # next year
    return b


def _get(user, building, **params):
    client = APIClient()
    client.force_authenticate(user)
    return client.get(f"/api/v1/buildings/{building.pk}/annual-report/", params)


def test_year_totals_and_grouping(admin_user, building):
    data = _get(admin_user, building, year=2026).data
    assert Decimal(data["opening_balance"]) == Decimal("1300.00")  # 1000 + 500 - 200
    assert Decimal(data["total_collected"]) == Decimal("450.00")
    assert Decimal(data["total_expenses"]) == Decimal("150.00")    # subscriptions and pending are left out
    assert Decimal(data["closing_balance"]) == Decimal("1600.00")
    assert len(data["months"]) == 12
    assert Decimal(data["months"][0]["collected"]) == Decimal("150.00")
    assert Decimal(data["months"][2]["expenses"]) == Decimal("150.00")
    by_category = [(c["category"], c["amount"]) for c in data["expenses_by_category"]]
    assert by_category == [("Lift", "120.00"), ("Cleaning", "30.00")]


def test_next_year_opens_where_the_last_closed(admin_user, building):
    closed = _get(admin_user, building, year=2026).data["closing_balance"]
    assert _get(admin_user, building, year=2027).data["opening_balance"] == closed


def test_unpaid_dues_list_units_only(admin_user, building):
    data = _get(admin_user, building, year=2026).data
    assert data["unpaid_units"] == [{"unit": "1", "balance_due": "75.00"}]
    assert Decimal(data["total_unpaid"]) == Decimal("75.00")


def test_access_follows_the_building(owner_user, building, django_user_model):
    UserBuilding.objects.create(user=owner_user, building=building)
    assert _get(owner_user, building, year=2026).status_code == 200
    stranger = django_user_model.objects.create_user(email="s@abem.test", password="Pass1234!x", role="owner")
    assert _get(stranger, building, year=2026).status_code == 404


def test_bad_year_is_a_400(admin_user, building):
    assert _get(admin_user, building, year="abc").status_code == 400
    assert _get(admin_user, building, year=1800).status_code == 400


def test_pdf_in_both_languages(admin_user, building):
    for lang in ("ar", "en"):
        admin_user.preferred_language = lang
        admin_user.save()
        resp = _get(admin_user, building, year=2026, file_format="pdf")
        assert resp.status_code == 200 and resp["Content-Type"] == "application/pdf"
        assert resp.content.startswith(b"%PDF")
