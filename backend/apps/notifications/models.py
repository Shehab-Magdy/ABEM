"""Notification model."""
import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class NotificationType(models.TextChoices):
    PAYMENT_DUE = "payment_due", _("Payment Due")
    PAYMENT_OVERDUE = "payment_overdue", _("Payment Overdue")
    PAYMENT_CONFIRMED = "payment_confirmed", _("Payment Confirmed")
    EXPENSE_ADDED = "expense_added", _("New Expense Added")
    EXPENSE_UPDATED = "expense_updated", _("Expense Updated")
    USER_REGISTERED = "user_registered", _("New User Registered")
    ANNOUNCEMENT = "announcement", _("Announcement")


class NotificationChannel(models.TextChoices):
    EMAIL = "email", _("Email")
    PUSH = "push", _("Push Notification")
    IN_APP = "in_app", _("In-App")


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_notifications",
    )
    notification_type = models.CharField(max_length=30, choices=NotificationType.choices)
    channel = models.CharField(max_length=10, choices=NotificationChannel.choices)
    title = models.CharField(max_length=255)
    body = models.TextField()
    message_key = models.CharField(max_length=100, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)  # extra context (expense_id, amount, etc.)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # auto-purge after 90 days

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.user} – {self.notification_type} ({self.channel})"
