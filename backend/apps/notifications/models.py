"""Notification model."""
import uuid
from django.db import models
from django.conf import settings


class NotificationType(models.TextChoices):
    PAYMENT_DUE = "payment_due", "Payment Due"
    PAYMENT_OVERDUE = "payment_overdue", "Payment Overdue"
    PAYMENT_CONFIRMED = "payment_confirmed", "Payment Confirmed"
    EXPENSE_ADDED = "expense_added", "New Expense Added"
    EXPENSE_UPDATED = "expense_updated", "Expense Updated"
    USER_REGISTERED = "user_registered", "New User Registered"
    ANNOUNCEMENT = "announcement", "Announcement"


class NotificationChannel(models.TextChoices):
    EMAIL = "email", "Email"
    PUSH = "push", "Push Notification"
    IN_APP = "in_app", "In-App"


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
