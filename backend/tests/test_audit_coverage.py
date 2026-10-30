"""R-26: money actions leave an audit entry (claim reject, plan payments, expense decisions, scheduled jobs)."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.apartments.models import Apartment
from apps.audit.models import AuditLog
from apps.buildings.models import Building, UserBuilding
from apps.expenses.late_fees import apply_late_fees
from apps.expenses.models import Expense, ExpenseCategory, RecurringConfig, SubscriptionPlan
from apps.expenses.recurring import generate_recurring_expenses
from apps.expenses.subscriptions import bill_subscriptions
from apps.expenses.utils import run_split_engine

pytestmark = pytest.mark.django_db


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def building(admin_user):
    return Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user)


def test_claim_reject_is_audited(admin_user, owner_user, building):
    UserBuilding.objects.create(user=owner_user, building=building)
    apt = Apartment.objects.create(building=building, unit_number="1", owner=owner_user, balance=Decimal("100"))
    apt.owners.add(owner_user)
    claim = _client(owner_user).post(
        "/api/v1/payments/claims/", {"apartment_id": str(apt.pk), "amount": "50.00", "reference": "r"}, format="json"
    )
    assert _client(admin_user).post(f"/api/v1/payments/claims/{claim.data['id']}/reject/").status_code == 200
    assert AuditLog.objects.filter(action="reject", entity="payment_claim", entity_id=claim.data["id"]).exists()


def test_plan_payment_confirm_and_reject_are_audited(admin_user, building, django_user_model):
    root = django_user_model.objects.create_superuser(email="root@abem.test", password="Pass1234!x")
    body = {"building_id": str(building.pk), "plan_code": "standard", "period": "monthly", "reference": "x"}
    first = _client(admin_user).post("/api/v1/plans/payments/", body, format="json").data["id"]
    assert _client(root).post(f"/api/v1/plans/payments/{first}/confirm/").status_code == 200
    second = _client(admin_user).post("/api/v1/plans/payments/", body, format="json").data["id"]
    assert _client(root).post(f"/api/v1/plans/payments/{second}/reject/").status_code == 200
    assert AuditLog.objects.filter(action="confirm", entity="plan_payment", entity_id=first).exists()
    assert AuditLog.objects.filter(action="reject", entity="plan_payment", entity_id=second).exists()


def test_expense_approve_and_reject_are_their_own_actions(admin_user, building):
    category = ExpenseCategory.objects.create(building=building, name="Lift")
    Apartment.objects.create(building=building, unit_number="1")
    ids = []
    for _n in range(2):
        e = Expense.objects.create(
            building=building, category=category, title="Big", amount=Decimal("100"), expense_date=date.today(),
            created_by=admin_user, approval_status="pending",
        )
        ids.append(e.pk)
    assert _client(admin_user).post(f"/api/v1/expenses/{ids[0]}/approve/").status_code == 200
    assert _client(admin_user).post(f"/api/v1/expenses/{ids[1]}/reject/").status_code == 200
    assert AuditLog.objects.filter(action="approve", entity="expense", entity_id=ids[0]).exists()
    assert AuditLog.objects.filter(action="reject", entity="expense", entity_id=ids[1]).exists()


def test_recurring_generation_is_audited_per_building(admin_user, building):
    Apartment.objects.create(building=building, unit_number="1")
    category = ExpenseCategory.objects.create(building=building, name="Cleaning")
    expense = Expense.objects.create(
        building=building, category=category, title="Cleaning", amount=Decimal("200.00"),
        expense_date=date.today() - timedelta(days=40), is_recurring=True, created_by=admin_user,
    )
    run_split_engine(expense)
    RecurringConfig.objects.create(expense=expense, frequency="monthly", next_due=date.today() - timedelta(days=1))
    assert generate_recurring_expenses() == 1
    entry = AuditLog.objects.get(action="generate_recurring", entity="building", entity_id=building.pk)
    assert entry.changes["created"] == 1 and entry.user is None


def test_subscription_billing_and_late_fees_are_audited(building):
    Apartment.objects.create(building=building, unit_number="1")
    SubscriptionPlan.objects.create(
        building=building, amount=Decimal("200.00"), billing_day=1, due_days=10, starts_on=date(2026, 10, 1),
        late_fee_type="fixed", late_fee_value=Decimal("20.00"), grace_days=0,
    )
    assert bill_subscriptions(date(2026, 10, 1)) == 1
    assert AuditLog.objects.get(action="bill_subscriptions", entity_id=building.pk).changes["created"] == 1
    assert apply_late_fees(date(2026, 10, 20)) == 1
    entry = AuditLog.objects.get(action="apply_late_fees", entity_id=building.pk)
    assert entry.changes["created"] == 1 and entry.changes["total"] == "20.00"
