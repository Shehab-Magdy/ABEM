"""Monthly subscription billing: charge every unit the building's fixed amount, once per month."""
from __future__ import annotations

import calendar
from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.apartments.models import Apartment
from apps.audit.mixins import log_job_run

from .models import ApartmentExpense, Expense, ExpenseCategory, ExpenseKind, SplitType, SubscriptionPlan, SubscriptionRun

CATEGORY_NAME = "الاشتراك الشهري"


def _months(start: date, end: date):
    """First days of every month from `start`'s month through `end`'s month."""
    month = start.replace(day=1)
    while month <= end:
        yield month
        month = date(month.year + (month.month == 12), month.month % 12 + 1, 1)


def _billing_date(month: date, billing_day: int) -> date:
    return month.replace(day=min(billing_day, calendar.monthrange(month.year, month.month)[1]))


def bill_plan_month(plan: SubscriptionPlan, month: date) -> Expense | None:
    """Charge every unpaused unit for `month`. Returns the charge, or None if nothing to bill or already billed."""
    if SubscriptionRun.objects.filter(plan=plan, month=month).exists():
        return None
    units = list(Apartment.objects.filter(building=plan.building, billing_paused=False))
    if not units:
        return None

    # each unit pays the plan amount times its rate factor (a shop 1.5x, a large flat 1.2x ...)
    shares = {u.pk: (plan.amount * u.rate_factor).quantize(Decimal("0.01")) for u in units}
    billed_on = _billing_date(month, plan.billing_day)
    category, _ = ExpenseCategory.objects.get_or_create(building=plan.building, name=CATEGORY_NAME)
    with transaction.atomic():
        charge = Expense.objects.create(
            building=plan.building,
            category=category,
            title=f"{CATEGORY_NAME} {month:%Y-%m}",
            amount=sum(shares.values()),
            expense_date=billed_on,
            due_date=billed_on + timedelta(days=plan.due_days),
            kind=ExpenseKind.SUBSCRIPTION,
            split_type=SplitType.CUSTOM,
            created_by=plan.building.admin,
        )
        ApartmentExpense.objects.bulk_create(
            [ApartmentExpense(apartment=u, expense=charge, share_amount=shares[u.pk]) for u in units]
        )
        for unit in units:
            Apartment.objects.filter(pk=unit.pk).update(balance=F("balance") + shares[unit.pk])
        SubscriptionRun.objects.create(plan=plan, month=month, expense=charge)
    return charge


def bill_subscriptions(today: date | None = None) -> int:
    """Bill every active plan for each month whose billing day has arrived. Returns how many charges were created.

    Safe to run daily and to repeat: a month is billed once, and a missed run catches up the next day.
    """
    today = today or timezone.localdate()
    created = 0
    runs: dict = {}
    from apps.plans.services import billing_allowed

    for plan in SubscriptionPlan.objects.filter(is_active=True, building__deleted_at__isnull=True, building__is_active=True).select_related("building"):
        if not billing_allowed(plan.building, today):
            continue  # the building's plan no longer includes billing (after its grace period)
        for month in _months(plan.starts_on, today):
            if _billing_date(month, plan.billing_day) > today:
                continue
            if bill_plan_month(plan, month):
                created += 1
                runs.setdefault(plan.building_id, {"created": 0})["created"] += 1
    log_job_run("bill_subscriptions", runs)
    return created
