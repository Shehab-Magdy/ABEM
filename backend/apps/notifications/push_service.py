"""Bilingual FCM push notification content helper.

Provides get_push_content() which returns locale-aware title and body
strings for Firebase Cloud Messaging push notifications.
Amounts are formatted with the appropriate digit system (Western for
English, Arabic-Indic for Arabic) using the babel library.
"""
from __future__ import annotations

try:
    from babel.numbers import format_currency as _babel_format_currency
except ImportError:  # pragma: no cover – babel is optional in dev
    _babel_format_currency = None

# ── Push content templates ───────────────────────────────────────────────────

_PUSH_CONTENT = {
    "payment_reminder": {
        "en": {
            "title": "Payment Due",
            "body": "You have a payment of {amount} due on {date}",
        },
        "ar": {
            "title": "تذكير بالدفع",
            "body": "لديك دفعة بمبلغ {amount} مستحقة في {date}",
        },
    },
    "expense_added": {
        "en": {
            "title": "New Expense",
            "body": "{category} expense of {amount} has been added to {building}",
        },
        "ar": {
            "title": "مصروف جديد",
            "body": "تم إضافة مصروف {category} بمبلغ {amount} في {building}",
        },
    },
    "payment_confirmed": {
        "en": {
            "title": "Payment Confirmed",
            "body": "Your payment of {amount} has been recorded. Remaining: {balance}",
        },
        "ar": {
            "title": "تم تأكيد الدفعة",
            "body": "تم تسجيل دفعتك بمبلغ {amount}. الرصيد المتبقي: {balance}",
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
    "broadcast": {
        "en": {"title": "{subject}", "body": "{message}"},
        "ar": {"title": "{subject}", "body": "{message}"},
    },
}


def format_amount(amount, lang: str = "en") -> str:
    """Format a monetary amount with locale-appropriate digits and currency."""
    try:
        value = float(amount)
    except (TypeError, ValueError):
        return str(amount)
    if _babel_format_currency:
        locale = "ar_EG" if lang == "ar" else "en_EG"
        return _babel_format_currency(value, "EGP", locale=locale)
    return f"{value:,.2f} EGP"


def get_push_content(
    notification_type: str,
    lang: str = "en",
    **kwargs,
) -> dict[str, str]:
    """Return {"title": ..., "body": ...} for an FCM push notification.

    All keyword arguments are interpolated into the template strings.
    Amount kwargs are auto-formatted with locale-aware digits.
    """
    if lang not in ("en", "ar"):
        lang = "en"

    content = _PUSH_CONTENT.get(notification_type, {})
    lang_content = content.get(lang, content.get("en", {}))

    title_tpl = lang_content.get("title", notification_type)
    body_tpl = lang_content.get("body", "")

    # Auto-format amount fields
    for key in ("amount", "balance"):
        if key in kwargs:
            kwargs[key] = format_amount(kwargs[key], lang)

    try:
        title = title_tpl.format(**kwargs)
        body = body_tpl.format(**kwargs)
    except (KeyError, IndexError):
        title = title_tpl
        body = body_tpl

    return {"title": title, "body": body}
