"""Bilingual email dispatch service for ABEM notifications.

Selects the correct HTML template based on the recipient's preferred
language and formats amounts/dates using the babel library.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

try:
    from babel.numbers import format_currency as babel_format_currency
    from babel.dates import format_date as babel_format_date
except ImportError:
    babel_format_currency = None
    babel_format_date = None

logger = logging.getLogger(__name__)

# ── Email subjects (bilingual) ───────────────────────────────────────────────

_SUBJECTS = {
    "payment_reminder": {
        "en": "Payment Due — {building_name}",
        "ar": "تذكير بموعد السداد — {building_name}",
    },
    "expense_added": {
        "en": "New Expense Added — {building_name}",
        "ar": "تم إضافة مصروف جديد — {building_name}",
    },
    "payment_confirmation": {
        "en": "Payment Confirmed — {building_name}",
        "ar": "تأكيد استلام الدفعة — {building_name}",
    },
    "payment_overdue": {
        "en": "Payment Overdue — {building_name}",
        "ar": "تنبيه: دفعة متأخرة السداد — {building_name}",
    },
}


def _format_amount(amount, lang: str) -> str:
    """Format a monetary amount with locale-appropriate digits."""
    try:
        value = float(Decimal(str(amount)))
    except (TypeError, ValueError):
        return str(amount)
    if babel_format_currency:
        locale = "ar_EG" if lang == "ar" else "en_EG"
        return babel_format_currency(value, "EGP", locale=locale)
    return f"{value:,.2f} EGP"


def _format_date(date, lang: str) -> str:
    """Format a date with locale-appropriate representation."""
    if babel_format_date:
        locale = "ar_EG" if lang == "ar" else "en"
        return babel_format_date(date, format="long", locale=locale)
    return str(date)


def send_notification_email(
    template_name: str,
    recipient_email: str,
    context: dict[str, Any],
    lang: str = "en",
) -> bool:
    """Send a notification email using the correct language template.

    Args:
        template_name: Base template name (e.g. "payment_reminder")
        recipient_email: Email address to send to
        context: Template context variables (amount, date, owner_name, etc.)
        lang: Language code ("en" or "ar"), defaults to "en"

    Returns:
        True if sent successfully, False otherwise.
    """
    if lang not in ("en", "ar"):
        lang = "en"

    # Format monetary amounts and dates
    for key in ("amount", "share_amount", "remaining_balance"):
        if key in context and context[key] is not None:
            context[key] = _format_amount(context[key], lang)

    for key in ("date", "due_date"):
        if key in context and context[key] is not None:
            context[key] = _format_date(context[key], lang)

    # Resolve subject
    subject_tpl = _SUBJECTS.get(template_name, {}).get(lang, template_name)
    subject = subject_tpl.format(**{k: v for k, v in context.items() if isinstance(v, str)})

    # Render HTML body
    html_template = f"emails/{template_name}_{lang}.html"
    try:
        html_body = render_to_string(html_template, context)
    except Exception:
        logger.exception("Failed to render email template %s", html_template)
        return False

    # Send
    email = EmailMessage(
        subject=subject,
        body=html_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient_email],
    )
    email.content_subtype = "html"
    email.extra_headers = {"Content-Language": lang}

    try:
        email.send()
        return True
    except Exception:
        logger.exception("Failed to send email to %s", recipient_email)
        return False
