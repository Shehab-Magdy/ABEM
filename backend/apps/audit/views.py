"""Audit log views – stubs to be implemented in Sprint 8."""
from rest_framework.viewsets import ReadOnlyModelViewSet
from .models import AuditLog


class AuditLogViewSet(ReadOnlyModelViewSet):
    queryset = AuditLog.objects.none()
    # TODO Sprint 8: admin-only, filterable by entity/user/date
