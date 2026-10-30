"""What plan a building is really on, and what that allows."""
from __future__ import annotations

import calendar
from datetime import date, timedelta

from .models import BuildingPlan, Plan, PlatformSettings


def _add_months(day: date, months: int) -> date:
    month_index = day.month - 1 + months
    year, month = day.year + month_index // 12, month_index % 12 + 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def free_plan() -> Plan:
    return Plan.objects.get(code="free")


def effective_plan(building, today: date | None = None) -> tuple[Plan, date | None, bool]:
    """(plan, paid_until, on_trial). A lapsed paid plan falls back to free; new buildings get a short trial."""
    today = today or date.today()
    row = BuildingPlan.objects.select_related("plan").filter(building=building).first()
    if row and row.paid_until >= today:
        return row.plan, row.paid_until, False
    trial_end = building.created_at.date() + timedelta(days=PlatformSettings.load().trial_days)
    if today <= trial_end:
        top = Plan.objects.filter(is_active=True).order_by("-price_monthly").first()
        if top:
            return top, trial_end, True
    return free_plan(), None, False


def has_feature(building, feature: str) -> bool:
    return feature in (effective_plan(building)[0].features or [])


def unit_room(building, adding: int = 1) -> bool:
    """True when the building may add `adding` more units under its plan."""
    limit = effective_plan(building)[0].max_units
    return limit is None or building.apartments.count() + adding <= limit


def extend(building, plan: Plan, period: str, today: date | None = None) -> date:
    """Move paid_until forward one period (from the old end date if still running) and switch to `plan`."""
    today = today or date.today()
    row = BuildingPlan.objects.filter(building=building).first()
    start = row.paid_until if row and row.paid_until >= today and row.plan_id == plan.code else today
    until = _add_months(start, 12 if period == "yearly" else 1)
    BuildingPlan.objects.update_or_create(building=building, defaults={"plan": plan, "paid_until": until})
    return until


def billing_allowed(building, today: date | None = None) -> bool:
    """True while the building's plan includes monthly billing, plus a grace period after it ends.

    The grace period covers a lapsed paid plan or a finished trial, so charges do not stop on the first day.
    """
    today = today or date.today()
    plan, _, _ = effective_plan(building, today)
    if "subscriptions" in (plan.features or []):
        return True
    row = BuildingPlan.objects.select_related("plan").filter(building=building).first()
    if row:
        ended_on, covered = row.paid_until, "subscriptions" in (row.plan.features or [])
    else:
        settings_ = PlatformSettings.load()
        ended_on = building.created_at.date() + timedelta(days=settings_.trial_days)
        top = Plan.objects.filter(is_active=True).order_by("-price_monthly").first()
        covered = bool(top and "subscriptions" in (top.features or []))
    return covered and ended_on + timedelta(days=PlatformSettings.load().grace_days) >= today
