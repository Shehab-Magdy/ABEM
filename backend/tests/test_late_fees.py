"""Per-unit rate factors and late fees on overdue subscription shares."""
from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.apartments.models import Apartment
from apps.buildings.models import Building
from apps.expenses.late_fees import apply_late_fees
from apps.expenses.models import Expense, ExpenseKind, LateFee, SubscriptionPlan
from apps.expenses.subscriptions import bill_subscriptions
from apps.payments.models import Payment

pytestmark = pytest.mark.django_db


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def building(admin_user):
    return Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user)


@pytest.fixture
def units(building):
    flat = Apartment.objects.create(building=building, unit_number="1")
    shop = Apartment.objects.create(building=building, unit_number="S1", rate_factor=Decimal("1.50"))
    return flat, shop


def _plan(building, **extra):
    return SubscriptionPlan.objects.create(
        building=building, amount=Decimal("200.00"), billing_day=1, due_days=10, starts_on=date(2026, 10, 1), **extra
    )


def _bal(unit):
    return Apartment.objects.get(pk=unit.pk).balance


def test_rate_factor_scales_each_units_charge(building, units):
    _plan(building)
    bill_subscriptions(date(2026, 10, 1))
    flat, shop = units
    assert _bal(flat) == Decimal("200.00") and _bal(shop) == Decimal("300.00")
    assert Expense.objects.get().amount == Decimal("500.00")


def test_rate_factor_must_be_sensible(admin_user, units):
    for bad in ("0", "11", "-1"):
        resp = _client(admin_user).patch(f"/api/v1/apartments/{units[0].pk}/", {"rate_factor": bad}, format="json")
        assert resp.status_code == 400
    assert _client(admin_user).patch(f"/api/v1/apartments/{units[0].pk}/", {"rate_factor": "1.20"}, format="json").status_code == 200


def test_fixed_late_fee_after_due_date_and_grace(building, units):
    _plan(building, late_fee_type="fixed", late_fee_value=Decimal("25.00"), grace_days=3)
    bill_subscriptions(date(2026, 10, 1))                       # due 11 Oct
    assert apply_late_fees(date(2026, 10, 14)) == 0             # still within 3 grace days
    assert apply_late_fees(date(2026, 10, 15)) == 2
    assert _bal(units[0]) == Decimal("225.00") and _bal(units[1]) == Decimal("325.00")
    assert Expense.objects.filter(kind=ExpenseKind.LATE_FEE).count() == 2


def test_percent_late_fee_is_on_what_is_still_owed(building, units, admin_user):
    _plan(building, late_fee_type="percent", late_fee_value=Decimal("10"))
    bill_subscriptions(date(2026, 10, 1))
    Payment.objects.create(apartment=units[0], amount_paid=Decimal("100.00"), payment_date=date(2026, 10, 5), recorded_by=admin_user)
    # (a manually-created payment has no allocation, so it is spread over the unit's unpaid charges)
    apply_late_fees(date(2026, 10, 20))
    fee = Expense.objects.get(kind=ExpenseKind.LATE_FEE, apartment_expenses__apartment=units[1])
    assert fee.amount == Decimal("30.00")                       # 10% of the shop's 300


def test_a_share_is_fined_only_once_and_paid_shares_not_at_all(building, units, admin_user):
    _plan(building, late_fee_type="fixed", late_fee_value=Decimal("25.00"))
    bill_subscriptions(date(2026, 10, 1))
    from apps.expenses.models import ApartmentExpense
    from apps.payments.models import PaymentExpense

    payment = Payment.objects.create(apartment=units[0], amount_paid=Decimal("200.00"), payment_date=date(2026, 10, 5), recorded_by=admin_user)
    PaymentExpense.objects.create(payment=payment, expense=Expense.objects.get(kind=ExpenseKind.SUBSCRIPTION), allocated_amount=Decimal("200.00"))

    assert apply_late_fees(date(2026, 10, 20)) == 1             # only the shop is late
    assert apply_late_fees(date(2026, 10, 25)) == 0             # never twice
    assert LateFee.objects.count() == 1


def test_no_fee_when_the_plan_has_none(building, units):
    _plan(building)
    bill_subscriptions(date(2026, 10, 1))
    assert apply_late_fees(date(2026, 12, 1)) == 0


def test_waiving_a_fee_reverses_it_and_records_why(building, units, admin_user):
    _plan(building, late_fee_type="fixed", late_fee_value=Decimal("25.00"))
    bill_subscriptions(date(2026, 10, 1))
    apply_late_fees(date(2026, 10, 20))
    fee = LateFee.objects.filter(share__apartment=units[0]).get()

    resp = _client(admin_user).post(f"/api/v1/expenses/late-fees/{fee.pk}/waive/", {"reason": "Paid late by agreement"}, format="json")
    assert resp.status_code == 200 and resp.data["waived_at"]
    assert _bal(units[0]) == Decimal("200.00")                  # fee taken back off
    fee.refresh_from_db()
    assert fee.waived_reason == "Paid late by agreement" and fee.waived_by == admin_user
    assert _client(admin_user).post(f"/api/v1/expenses/late-fees/{fee.pk}/waive/", {}, format="json").status_code == 200
    assert _bal(units[0]) == Decimal("200.00")                  # waiving twice changes nothing
    assert apply_late_fees(date(2026, 10, 30)) == 0             # and it is not re-applied


def test_late_fees_are_not_building_costs(building, units, admin_user):
    _plan(building, late_fee_type="fixed", late_fee_value=Decimal("25.00"))
    bill_subscriptions(date(2026, 10, 1))
    apply_late_fees(date(2026, 10, 20))
    treasury = _client(admin_user).get(f"/api/v1/buildings/{building.pk}/treasury/").data
    assert Decimal(treasury["total_expenses"]) == Decimal("0.00")


def test_only_the_buildings_admin_sees_or_waives_fees(building, units, admin_user, owner_user, django_user_model):
    _plan(building, late_fee_type="fixed", late_fee_value=Decimal("25.00"))
    bill_subscriptions(date(2026, 10, 1))
    apply_late_fees(date(2026, 10, 20))
    fee = LateFee.objects.first()
    assert _client(owner_user).get("/api/v1/expenses/late-fees/").status_code == 403
    outsider = django_user_model.objects.create_user(email="x@abem.test", password="XPass1!xxx", role="admin")
    assert _client(outsider).get("/api/v1/expenses/late-fees/").data["results"] == []
    assert _client(outsider).post(f"/api/v1/expenses/late-fees/{fee.pk}/waive/", {}, format="json").status_code == 404


def test_plan_api_accepts_and_validates_late_fee_settings(admin_user, building):
    url = f"/api/v1/buildings/{building.pk}/subscription/"
    ok = _client(admin_user).post(url, {"amount": "100", "late_fee_type": "percent", "late_fee_value": "5", "grace_days": 2}, format="json")
    assert ok.status_code == 200 and ok.data["plan"]["late_fee_type"] == "percent" and ok.data["plan"]["grace_days"] == 2
    for bad in ({"late_fee_type": "weird"}, {"late_fee_type": "percent", "late_fee_value": "150"}, {"late_fee_type": "fixed", "late_fee_value": "0"}, {"grace_days": 99}):
        resp = _client(admin_user).post(url, {"amount": "100", "late_fee_value": "5", **bad}, format="json")
        assert resp.status_code == 400, bad
