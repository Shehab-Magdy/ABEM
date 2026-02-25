"""Notification service helpers – Sprint 6.

All functions create in-app Notification records.
Email / push integrations are no-ops in development (no external deps required for tests).
"""
from __future__ import annotations

from .models import Notification, NotificationType


def notify_user(
    user,
    notification_type: str,
    title: str,
    body: str,
    channel: str = "in_app",
    metadata: dict | None = None,
) -> Notification:
    """Create a single in-app notification for *user*."""
    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        channel=channel,
        title=title,
        body=body,
        metadata=metadata or {},
    )


def notify_expense_created(expense, apartments: list) -> None:
    """
    Notify each apartment owner when an expense is added.
    Called from ExpenseViewSet.perform_create — failures are silent.
    """
    for apt in apartments:
        if apt.owner_id:
            notify_user(
                user=apt.owner,
                notification_type=NotificationType.EXPENSE_ADDED,
                title="New Expense Added",
                body=f"Expense '{expense.title}' has been added to your account.",
                metadata={"expense_id": str(expense.id)},
            )


def notify_payment_confirmed(payment) -> None:
    """
    Notify the apartment owner when a payment is recorded.
    Called from PaymentViewSet.perform_create — failures are silent.
    """
    if payment.apartment.owner_id:
        notify_user(
            user=payment.apartment.owner,
            notification_type=NotificationType.PAYMENT_CONFIRMED,
            title="Payment Confirmed",
            body=f"Payment of {payment.amount_paid} EGP has been recorded.",
            metadata={
                "payment_id": str(payment.id),
                "amount": str(payment.amount_paid),
            },
        )
