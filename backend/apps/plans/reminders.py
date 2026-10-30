"""Tell building admins their plan (or trial) is ending, so billing never stops by surprise."""
from __future__ import annotations

from datetime import date, timedelta

from django.utils import timezone

from apps.buildings.models import Building
from apps.expenses.models import SubscriptionPlan
from apps.notifications.models import NotificationType
from apps.notifications.services import notify_user

from .models import BuildingPlan, PlatformSettings

REMIND_AT = (7, 3, 1, 0)  # days left


def _admins(building):
    people = {building.admin_id: building.admin}
    for co in building.co_admins.all():
        people[co.pk] = co
    return [u for u in people.values() if u.is_active]


def _tell(building, ar, en):
    for user in _admins(building):
        is_ar = getattr(user, "preferred_language", "ar") == "ar"
        title, body = ar if is_ar else en
        notify_user(user=user, notification_type=NotificationType.ANNOUNCEMENT, title=title, body=body,
                    metadata={"building_id": str(building.pk), "kind": "plan"})


def send_plan_reminders(today: date | None = None) -> int:
    """Run daily. Each building is told at 7, 3 and 1 days before its plan or trial ends, and on the last day;
    a building that bills monthly is told again when billing stops after the grace period. Returns messages sent."""
    today = today or timezone.localdate()
    settings = PlatformSettings.load()
    plans = {p.building_id: p for p in BuildingPlan.objects.all()}
    sent = 0
    for building in Building.objects.filter(deleted_at__isnull=True, is_active=True).select_related("admin"):
        row = plans.get(building.pk)
        ends = row.paid_until if row else building.created_at.date() + timedelta(days=settings.trial_days)
        left = (ends - today).days
        what_ar, what_en = ("باقتك", "Your plan") if row else ("الفترة التجريبية", "Your trial")
        if left in REMIND_AT:
            when_ar = "تنتهي اليوم" if left == 0 else f"تنتهي بعد {left} يوم"
            when_en = "ends today" if left == 0 else f"ends in {left} day(s)"
            _tell(
                building,
                (f"{what_ar} {when_ar}", f"جدّد من صفحة الباقة حتى يستمر الاشتراك الشهري لعمارة {building.name} بدون توقف."),
                (f"{what_en} {when_en}", f"Renew on the Plan page so monthly billing for {building.name} keeps running."),
            )
            sent += 1
        elif left == -settings.grace_days and SubscriptionPlan.objects.filter(building=building, is_active=True).exists():
            _tell(
                building,
                ("توقفت الفواتير الشهرية", f"انتهت مهلة الباقة لعمارة {building.name}. جدّد الباقة لاستئناف الفواتير."),
                ("Monthly billing has stopped", f"The plan grace period for {building.name} is over. Renew to resume billing."),
            )
            sent += 1
    return sent
