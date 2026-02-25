"""Audit log views – Sprint 8."""
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.authentication.permissions import IsAdminRole

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(ReadOnlyModelViewSet):
    """
    Admin-only read-only view of the audit log.

    Supports filtering via query params:
      - entity     – e.g. "expense", "payment", "user"
      - user_id    – UUID of the acting user
      - action     – e.g. "create", "update", "delete"
      - date_from  – ISO date (YYYY-MM-DD), inclusive lower bound on created_at
      - date_to    – ISO date (YYYY-MM-DD), inclusive upper bound on created_at
    """

    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_queryset(self):
        qs = AuditLog.objects.select_related("user")
        p = self.request.query_params

        if entity := p.get("entity"):
            qs = qs.filter(entity=entity)
        if user_id := p.get("user_id"):
            qs = qs.filter(user_id=user_id)
        if action := p.get("action"):
            qs = qs.filter(action=action)
        if d_from := p.get("date_from"):
            qs = qs.filter(created_at__date__gte=d_from)
        if d_to := p.get("date_to"):
            qs = qs.filter(created_at__date__lte=d_to)

        return qs
