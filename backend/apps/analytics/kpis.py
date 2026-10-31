"""Platform KPIs (R-17), worked out from data the app already keeps.

Nothing extra is tracked: no events, no third-party scripts. A building counts as active when something
was recorded in it (a payment, an expense or a work order) in the window, so the numbers cannot drift.
"""

from __future__ import annotations

from datetime import timedelta

from django.db.models import Count, Max
from django.db.models.functions import TruncMonth
from django.utils import timezone

ACTIVE_DAYS = 30
QUIET_DAYS = 90


def _health(last, now):
    if last is None:
        return "new"
    age = (now - last).days
    if age <= ACTIVE_DAYS:
        return "active"
    return "quiet" if age <= QUIET_DAYS else "dormant"


def _plan_info(row, today, grace_days):
    """The building's BuildingPlan as a small dict, or None when it has no row (free / trial)."""
    if row is None:
        return None
    if row.paid_until >= today:
        status = "active"
    elif row.paid_until + timedelta(days=grace_days) >= today:
        status = "grace"  # lapsed, but monthly billing keeps running (see plans.services.billing_allowed)
    else:
        status = "expired"
    return {
        "code": row.plan.code,
        "name_en": row.plan.name_en,
        "name_ar": row.plan.name_ar,
        "paid_until": row.paid_until.isoformat(),
        "status": status,
    }


def build_platform_kpis(now=None) -> dict:
    from apps.apartments.models import Apartment
    from apps.authentication.models import User
    from apps.buildings.models import Building
    from apps.expenses.models import Expense
    from apps.maintenance.models import WorkOrder
    from apps.notifications.models import Notification
    from apps.payments.models import Payment

    now = now or timezone.now()
    since = now - timedelta(days=ACTIVE_DAYS)
    buildings = Building.objects.filter(deleted_at__isnull=True)

    # Latest recorded activity per building (any of payment / expense / work order)
    last = {}
    for qs, key in (
        (Payment.objects.all(), "apartment__building_id"),
        (Expense.objects.filter(deleted_at__isnull=True), "building_id"),
        (WorkOrder.objects.all(), "report__building_id"),
    ):
        for row in qs.values(key).annotate(last=Max("created_at")):
            if row[key] not in last or row["last"] > last[row[key]]:
                last[row[key]] = row["last"]

    from apps.plans.models import BuildingPlan, PlatformSettings

    plan_rows = {
        bp.building_id: bp for bp in BuildingPlan.objects.select_related("plan")
    }
    grace_days = PlatformSettings.load().grace_days
    today = now.date()

    rows = []
    for b in buildings.annotate(units=Count("apartments", distinct=True)):
        when = last.get(b.pk)
        rows.append(
            {
                "id": str(b.pk),
                "name": b.name,
                "units": b.units,
                "created_at": b.created_at.date().isoformat(),
                "last_activity": when.date().isoformat() if when else None,
                "health": _health(when, now),
                "plan": _plan_info(plan_rows.get(b.pk), today, grace_days),
            }
        )
    rows.sort(key=lambda r: (r["last_activity"] or "", r["name"]), reverse=True)

    signups = (
        User.objects.filter(created_at__gte=now - timedelta(days=183))
        .annotate(m=TruncMonth("created_at"))
        .values("m")
        .annotate(n=Count("id"))
        .order_by("m")
    )
    admins = User.objects.filter(role="admin")
    total_buildings = len(rows)
    return {
        "generated_at": now.isoformat(),
        "totals": {
            "buildings": total_buildings,
            "units": Apartment.objects.filter(building__in=buildings).count(),
            "admins": admins.count(),
            "residents": User.objects.exclude(role="admin")
            .filter(is_superuser=False)
            .count(),
        },
        "last_30_days": {
            "new_admins": admins.filter(created_at__gte=since).count(),
            "new_buildings": buildings.filter(created_at__gte=since).count(),
            "payments_recorded": Payment.objects.filter(created_at__gte=since).count(),
            "expenses_added": Expense.objects.filter(
                created_at__gte=since, deleted_at__isnull=True
            ).count(),
            "reminders_sent": Notification.objects.filter(
                created_at__gte=since,
                notification_type__in=["payment_due", "payment_overdue"],
            ).count(),
            "active_buildings": sum(1 for r in rows if r["health"] == "active"),
        },
        "activation": {
            "with_units": sum(1 for r in rows if r["units"] > 0),
            "with_activity": sum(1 for r in rows if r["last_activity"]),
        },
        "signups_by_month": [
            {"month": s["m"].strftime("%Y-%m"), "count": s["n"]} for s in signups
        ],
        "buildings": rows,
    }
