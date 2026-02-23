"""Audit logging utilities used across all apps."""
from .models import AuditLog


def log_action(*, user, action, entity, entity_id, changes=None, request=None):
    """
    Create an immutable AuditLog entry.

    Args:
        user:      The User performing the action (may be None for system events).
        action:    Verb string – 'create' | 'update' | 'delete' | 'login' | 'logout'.
        entity:    Model name in snake_case, e.g. 'user', 'expense', 'payment'.
        entity_id: UUID of the affected record.
        changes:   Dict of {'field': {'before': x, 'after': y}} for update actions.
        request:   DRF/Django request object (used to extract IP + user-agent).
    """
    ip_address = None
    user_agent = ""

    if request is not None:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        ip_address = forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR")
        user_agent = request.META.get("HTTP_USER_AGENT", "")

    AuditLog.objects.create(
        user=user,
        action=action,
        entity=entity,
        entity_id=entity_id,
        changes=changes or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )


class AuditLogMixin:
    """
    DRF ViewSet mixin that auto-logs create / update / destroy actions.
    Subclasses set `audit_entity` to the entity name string.
    """

    audit_entity: str = ""

    def perform_create(self, serializer):
        instance = serializer.save()
        log_action(
            user=self.request.user,
            action="create",
            entity=self.audit_entity or instance.__class__.__name__.lower(),
            entity_id=instance.pk,
            request=self.request,
        )

    def perform_update(self, serializer):
        old = {
            field: getattr(serializer.instance, field)
            for field in serializer.validated_data
        }
        instance = serializer.save()
        changes = {
            field: {"before": str(old.get(field, "")), "after": str(getattr(instance, field, ""))}
            for field in serializer.validated_data
        }
        log_action(
            user=self.request.user,
            action="update",
            entity=self.audit_entity or instance.__class__.__name__.lower(),
            entity_id=instance.pk,
            changes=changes,
            request=self.request,
        )

    def perform_destroy(self, instance):
        log_action(
            user=self.request.user,
            action="delete",
            entity=self.audit_entity or instance.__class__.__name__.lower(),
            entity_id=instance.pk,
            request=self.request,
        )
        instance.delete()
