"""Audit log model – immutable, append-only."""
import uuid
from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=50)   # e.g. "create", "update", "delete"
    entity = models.CharField(max_length=50)   # e.g. "expense", "payment", "user"
    entity_id = models.UUIDField(null=True, blank=True)
    changes = models.JSONField(default=dict, blank=True)  # before/after values
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["entity", "entity_id"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.user} {self.action} {self.entity} [{self.entity_id}]"
