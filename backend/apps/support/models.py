import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class TicketStatus(models.TextChoices):
    OPEN = "open", _("Open")
    CLOSED = "closed", _("Closed")


class SupportTicket(models.Model):
    """A problem report from inside the app, optionally with a screenshot."""
    objects: models.Manager["SupportTicket"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="support_tickets"
    )
    message = models.TextField()
    screenshot = models.ImageField(upload_to="support/", null=True, blank=True)
    page = models.CharField(max_length=255, blank=True, help_text=_("The screen the user was on"))
    status = models.CharField(max_length=10, choices=TicketStatus.choices, default=TicketStatus.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_id} {self.created_at:%Y-%m-%d}: {self.message[:40]}"
