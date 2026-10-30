"""Marking obligations done and reminding the board before they fall due."""
from __future__ import annotations

from datetime import date, timedelta

from dateutil.relativedelta import relativedelta
from django.db.models import Q
from django.utils import timezone

from apps.buildings.models import UserBuilding
from apps.notifications.models import NotificationType
from apps.notifications.services import notify_user

from .models import Contractor, Obligation, Repeat

REMIND_EVERY_DAYS = 7
CONTRACT_REMIND_DAYS = 30

_STEP = {Repeat.MONTHLY: relativedelta(months=1), Repeat.QUARTERLY: relativedelta(months=3), Repeat.YEARLY: relativedelta(years=1)}


def mark_done(obligation: Obligation, today: date | None = None) -> Obligation:
    """Record that it was done. A repeating obligation moves to its next due date; a one-off is finished."""
    today = today or timezone.localdate()
    obligation.last_done_on = today
    if obligation.repeat == Repeat.NONE:
        obligation.is_active = False
    else:
        step = _STEP[obligation.repeat]
        nxt = obligation.due_date + step
        while nxt <= today:  # skipped periods are not owed again
            nxt += step
        obligation.due_date = nxt
        obligation.last_reminded_on = None
    obligation.save()
    return obligation


def _board_and_admins(building):
    people = {building.admin_id: building.admin}
    for co in building.co_admins.all():
        people[co.pk] = co
    for ub in UserBuilding.objects.filter(building=building).exclude(board_role="").select_related("user"):
        people[ub.user_id] = ub.user
    return [u for u in people.values() if u.is_active]


def _tell(building, title_ar, title_en, body_ar, body_en):
    for user in _board_and_admins(building):
        ar = getattr(user, "preferred_language", "ar") == "ar"
        notify_user(user=user, notification_type=NotificationType.ANNOUNCEMENT, title=title_ar if ar else title_en, body=body_ar if ar else body_en)


def _due(last, today):
    return last is None or (today - last).days >= REMIND_EVERY_DAYS


def send_obligation_reminders(today: date | None = None) -> int:
    """Remind the building's admins and board about obligations coming due (or overdue) and contracts ending.

    Each is reminded at most once every week. Returns how many reminders were sent.
    """
    today = today or timezone.localdate()
    sent = 0
    due = Obligation.objects.filter(is_active=True, building__deleted_at__isnull=True).select_related("building__admin", "contractor")
    for ob in due:
        if ob.due_date - today > timedelta(days=ob.remind_days) or not _due(ob.last_reminded_on, today):
            continue
        late = ob.due_date < today
        who = f" — {ob.contractor.name}" if ob.contractor else ""
        _tell(
            ob.building,
            "التزام متأخر" if late else "التزام قريب الموعد", "Overdue obligation" if late else "Obligation coming up",
            f"{ob.title}{who}: {ob.due_date}", f"{ob.title}{who}: {ob.due_date}",
        )
        ob.last_reminded_on = today
        ob.save(update_fields=["last_reminded_on"])
        sent += 1

    contracts = Contractor.objects.filter(
        is_active=True, contract_end__isnull=False, contract_end__lte=today + timedelta(days=CONTRACT_REMIND_DAYS),
        building__deleted_at__isnull=True,
    ).select_related("building__admin")
    for c in contracts:
        if not _due(c.last_reminded_on, today):
            continue
        ended = c.contract_end < today
        _tell(
            c.building,
            "انتهى عقد" if ended else "عقد على وشك الانتهاء", "Contract ended" if ended else "Contract ending soon",
            f"{c.name} ({c.trade}): {c.contract_end}", f"{c.name} ({c.trade}): {c.contract_end}",
        )
        c.last_reminded_on = today
        c.save(update_fields=["last_reminded_on"])
        sent += 1
    return sent
