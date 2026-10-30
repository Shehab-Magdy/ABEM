"""Payment reminders: tell owners about shares that are due soon or overdue."""
from __future__ import annotations

import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.expenses.models import ApartmentExpense
from apps.expenses.utils import paid_toward_expense

from .email_service import send_notification_email
from .models import NotificationType, ReminderKind, ReminderLog
from .services import _get_content, _get_user_lang, notify_user

logger = logging.getLogger(__name__)

LEAD_DAYS = 3      # remind this many days before the due date
REPEAT_DAYS = 7    # while overdue, remind at most once a week


def _recipients(apartment):
    users = {u.pk: u for u in apartment.owners.all()}
    if apartment.owner_id:
        users[apartment.owner_id] = apartment.owner
    return [u for u in users.values() if u.is_active]


def _already_sent(share, kind, today) -> bool:
    logs = ReminderLog.objects.filter(expense=share.expense, apartment=share.apartment, kind=kind)
    if kind == ReminderKind.DUE_SOON:
        return logs.exists()  # once per share
    return logs.filter(sent_on__gt=today - timedelta(days=REPEAT_DAYS)).exists()


def send_payment_reminders(today=None) -> dict:
    """Send due-soon and overdue reminders for every unpaid share. Returns counts.

    Safe to run more than once a day: a share is reminded at most once while it is
    coming due, then at most once every REPEAT_DAYS while overdue.
    """
    today = today or timezone.localdate()
    counts = {"due_soon": 0, "overdue": 0, "skipped": 0, "emails_failed": 0}

    shares = (
        ApartmentExpense.objects.filter(
            expense__deleted_at__isnull=True,
            expense__is_manually_paid=False,
            expense__due_date__isnull=False,
            expense__due_date__lte=today + timedelta(days=LEAD_DAYS),
        )
        .select_related("expense", "apartment__building", "apartment__owner")
        .prefetch_related("apartment__owners")
    )

    for share in shares:
        due = share.expense.due_date
        kind = ReminderKind.OVERDUE if due < today else ReminderKind.DUE_SOON
        remaining = share.share_amount - paid_toward_expense(share.expense, share.apartment_id)
        if remaining <= 0 or _already_sent(share, kind, today):
            counts["skipped"] += 1
            continue

        recipients = _recipients(share.apartment)
        if not recipients:
            counts["skipped"] += 1
            continue

        message_key = "payment_overdue" if kind == ReminderKind.OVERDUE else "payment_reminder"
        for user in recipients:
            lang = _get_user_lang(user)
            currency = "ج.م." if lang == "ar" else "EGP"
            title, body = _get_content(message_key, lang, amount=f"{remaining:.2f} {currency}", date=str(due))
            notify_user(
                user=user,
                notification_type=(
                    NotificationType.PAYMENT_OVERDUE if kind == ReminderKind.OVERDUE else NotificationType.PAYMENT_DUE
                ),
                title=title,
                body=body,
                message_key=message_key,
                metadata={"expense_id": str(share.expense_id), "apartment_id": str(share.apartment_id)},
            )
            if user.email:
                sent = send_notification_email(
                    "payment_overdue" if kind == ReminderKind.OVERDUE else "payment_reminder",
                    user.email,
                    {
                        "owner_name": user.get_full_name() or user.email,
                        "building_name": share.apartment.building.name,
                        "amount": remaining,
                        "due_date": due,
                        "payment_url": f"{settings.FRONTEND_URL.rstrip('/')}/dashboard",
                    },
                    lang=lang,
                )
                if not sent:
                    counts["emails_failed"] += 1

        ReminderLog.objects.create(
            expense=share.expense, apartment=share.apartment, kind=kind, sent_on=today
        )
        counts[kind] += 1
    return counts
