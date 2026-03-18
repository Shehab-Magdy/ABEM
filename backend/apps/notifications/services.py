"""Notification service helpers – Sprint 6 + i18n.

All functions create in-app Notification records with localised content
based on the recipient's preferred_language.
Email / push integrations are no-ops in development.
"""
from __future__ import annotations

from django.utils import translation

from .models import Notification, NotificationType

# ── Bilingual notification content ───────────────────────────────────────────

NOTIFICATION_CONTENT = {
    "expense_added": {
        "en": {
            "title": "New Expense Added",
            "body": "Expense '{title}' has been added to your account.",
        },
        "ar": {
            "title": "مصروف جديد",
            "body": "تم إضافة مصروف '{title}' إلى حسابك.",
        },
    },
    "payment_confirmed": {
        "en": {
            "title": "Payment Confirmed",
            "body": "Payment of {amount} EGP has been recorded.",
        },
        "ar": {
            "title": "تم تأكيد الدفعة",
            "body": "تم تسجيل دفعة بمبلغ {amount} ج.م.",
        },
    },
    "payment_reminder": {
        "en": {
            "title": "Payment Due",
            "body": "You have a payment of {amount} due on {date}.",
        },
        "ar": {
            "title": "تذكير بالدفع",
            "body": "لديك دفعة بمبلغ {amount} مستحقة في {date}.",
        },
    },
    "payment_overdue": {
        "en": {
            "title": "Payment Overdue",
            "body": "Your balance of {amount} is overdue. Please pay as soon as possible.",
        },
        "ar": {
            "title": "دفعة متأخرة",
            "body": "رصيدك المستحق البالغ {amount} متأخر. يرجى السداد في أقرب وقت.",
        },
    },
}


def _get_user_lang(user) -> str:
    """Return the user's preferred language, defaulting to 'en'."""
    return getattr(user, "preferred_language", "en") or "en"


def _get_content(message_key: str, lang: str, **kwargs) -> tuple[str, str]:
    """Return (title, body) for a notification in the given language."""
    content = NOTIFICATION_CONTENT.get(message_key, {})
    lang_content = content.get(lang, content.get("en", {}))
    title = lang_content.get("title", message_key)
    body = lang_content.get("body", "")
    try:
        body = body.format(**kwargs)
    except (KeyError, IndexError):
        pass
    return title, body


# ── Core notification creation ───────────────────────────────────────────────


def notify_user(
    user,
    notification_type: str,
    title: str,
    body: str,
    channel: str = "in_app",
    metadata: dict | None = None,
    sender=None,
    message_key: str | None = None,
) -> Notification:
    """Create a single in-app notification for *user*."""
    return Notification.objects.create(
        user=user,
        sender=sender,
        notification_type=notification_type,
        channel=channel,
        title=title,
        body=body,
        message_key=message_key,
        metadata=metadata or {},
    )


def notify_expense_created(expense, apartments: list) -> None:
    """
    Notify each apartment owner when an expense is added.
    Called from ExpenseViewSet.perform_create — failures are silent.
    """
    for apt in apartments:
        if apt.owner_id:
            lang = _get_user_lang(apt.owner)
            title, body = _get_content(
                "expense_added", lang, title=expense.title
            )
            notify_user(
                user=apt.owner,
                notification_type=NotificationType.EXPENSE_ADDED,
                title=title,
                body=body,
                message_key="expense_added",
                metadata={"expense_id": str(expense.id)},
            )


def notify_payment_confirmed(payment) -> None:
    """
    Notify the apartment owner when a payment is recorded.
    Called from PaymentViewSet.perform_create — failures are silent.
    """
    if payment.apartment.owner_id:
        lang = _get_user_lang(payment.apartment.owner)
        title, body = _get_content(
            "payment_confirmed", lang, amount=str(payment.amount_paid)
        )
        notify_user(
            user=payment.apartment.owner,
            notification_type=NotificationType.PAYMENT_CONFIRMED,
            title=title,
            body=body,
            message_key="payment_confirmed",
            metadata={
                "payment_id": str(payment.id),
                "amount": str(payment.amount_paid),
            },
        )
