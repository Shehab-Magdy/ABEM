"""Notification views – Sprint 6."""
from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.authentication.models import User
from apps.authentication.permissions import IsAdminRole
from apps.buildings.models import Building

from .models import Notification, NotificationType
from .serializers import BroadcastSerializer, NotificationSerializer
from .services import notify_user


class NotificationViewSet(ReadOnlyModelViewSet):
    """
    User-scoped notification centre.

    Endpoints:
      GET  /notifications/              – list (filterable by is_read)
      GET  /notifications/{id}/         – retrieve
      POST /notifications/{id}/read/    – mark as read
      POST /notifications/broadcast/    – admin-only announcement
    """

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "options", "head"]

    # ── Queryset ────────────────────────────────────────────────────────────────

    def get_queryset(self):
        qs = Notification.objects.filter(user=self.request.user)
        is_read = self.request.query_params.get("is_read")
        if is_read is not None:
            qs = qs.filter(is_read=is_read.lower() == "true")
        return qs

    # ── Custom actions ──────────────────────────────────────────────────────────

    @action(detail=True, methods=["post"], url_path="read")
    def mark_read(self, request, pk=None):
        """POST /api/v1/notifications/{id}/read/ — mark a single notification as read."""
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(NotificationSerializer(notification).data)

    @action(
        detail=False,
        methods=["post"],
        url_path="broadcast",
        permission_classes=[IsAuthenticated, IsAdminRole],
    )
    def broadcast(self, request):
        """
        POST /api/v1/notifications/broadcast/
        Admin sends an announcement to all owners of apartments in a building.
        """
        serializer = BroadcastSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        building = get_object_or_404(
            Building,
            pk=serializer.validated_data["building_id"],
            admin=request.user,
            deleted_at__isnull=True,
        )

        owners = (
            User.objects.filter(owned_apartments__building=building)
            .distinct()
        )

        created = 0
        for owner in owners:
            notify_user(
                user=owner,
                notification_type=NotificationType.ANNOUNCEMENT,
                title=serializer.validated_data["subject"],
                body=serializer.validated_data["message"],
                metadata={"building_id": str(building.id)},
            )
            created += 1

        return Response(
            {"created": created, "building_id": str(building.id)},
            status=201,
        )
