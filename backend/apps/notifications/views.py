"""Notification views – Sprint 6."""
from __future__ import annotations

import uuid

from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.authentication.models import User
from apps.authentication.permissions import IsAdminRole
from apps.buildings.models import Building, UserBuilding

from django.utils.translation import gettext_lazy as _
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
        qs = Notification.objects.filter(user=self.request.user).select_related("sender")
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
        return Response(NotificationSerializer(notification, context={"request": request}).data)

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
            deleted_at__isnull=True,
        )

        # All owner-role members of this building
        owners = (
            User.objects.filter(
                userbuilding__building=building,
                role="owner",
            )
            .distinct()
        )

        group_id = uuid.uuid4()
        created = 0
        for owner in owners:
            notify_user(
                user=owner,
                notification_type=NotificationType.ANNOUNCEMENT,
                title=serializer.validated_data["subject"],
                body=serializer.validated_data["message"],
                metadata={"building_id": str(building.id)},
                sender=request.user,
                broadcast_group=group_id,
            )
            created += 1

        return Response(
            {"created": created, "building_id": str(building.id)},
            status=201,
        )

    @action(
        detail=True,
        methods=["get"],
        url_path="read-by",
        permission_classes=[IsAuthenticated, IsAdminRole],
    )
    def read_by(self, request, pk=None):
        """
        GET /api/v1/notifications/{id}/read-by/
        Admin-only: returns who has read this broadcast announcement.
        """
        notification = self.get_object()
        if not notification.broadcast_group:
            return Response(
                {"total_recipients": 1, "read_count": int(notification.is_read), "read_by": []},
            )

        related = Notification.objects.filter(broadcast_group=notification.broadcast_group)
        total = related.count()
        read_notifications = related.filter(is_read=True).select_related("user")

        read_users = []
        for n in read_notifications:
            profile_url = None
            if n.user.profile_picture:
                profile_url = request.build_absolute_uri(n.user.profile_picture.url)
            read_users.append({
                "id": str(n.user.id),
                "first_name": n.user.first_name,
                "last_name": n.user.last_name,
                "profile_picture": profile_url,
            })

        return Response({
            "total_recipients": total,
            "read_count": len(read_users),
            "read_by": read_users,
        })

    @action(
        detail=False,
        methods=["post"],
        url_path="send",
        permission_classes=[IsAuthenticated],
    )
    def send(self, request):
        """
        POST /api/v1/notifications/send/
        Any authenticated user can send a message to building members.
        Body: {building_id, title, message,
               recipient_type: "all"|"admins"|"owners"|"individual",
               recipient_ids: []}
        """
        # Enforce messaging restrictions
        if request.user.messaging_blocked:
            return Response(
                {"detail": _("You have been blocked from sending messages.")},
                status=403,
            )

        building_id = request.data.get("building_id")
        title = request.data.get("title", "").strip()
        message = request.data.get("message", "").strip()
        recipient_type = request.data.get("recipient_type", "all")
        recipient_ids = request.data.get("recipient_ids", [])

        if not building_id:
            return Response({"detail": _("building_id is required.")}, status=400)
        if not title or not message:
            return Response({"detail": _("title and message are required.")}, status=400)

        # Verify the sender is a member or admin of this building
        is_member = UserBuilding.objects.filter(
            user=request.user, building_id=building_id
        ).exists()
        if not is_member:
            return Response(
                {"detail": _("You are not a member of this building.")}, status=403
            )

        building = get_object_or_404(Building, pk=building_id, deleted_at__isnull=True)

        if recipient_type == "all":
            recipients = User.objects.filter(
                userbuilding__building=building
            ).distinct()
        elif recipient_type == "admins":
            recipients = User.objects.filter(
                userbuilding__building=building, role="admin"
            ).distinct()
        elif recipient_type == "owners":
            recipients = User.objects.filter(
                userbuilding__building=building, role="owner"
            ).distinct()
        elif recipient_type == "individual":
            if request.user.individual_messaging_blocked:
                return Response(
                    {"detail": _("You have been blocked from sending individual messages.")},
                    status=403,
                )
            if not recipient_ids:
                return Response({"detail": _("recipient_ids is required for individual send.")}, status=400)
            recipients = User.objects.filter(
                pk__in=recipient_ids,
                userbuilding__building=building,
            ).distinct()
        else:
            return Response({"detail": _("Invalid recipient_type.")}, status=400)

        created = 0
        for recipient in recipients:
            if recipient == request.user:
                continue  # don't send to yourself
            notify_user(
                user=recipient,
                notification_type=NotificationType.MESSAGE,
                title=title,
                body=message,
                metadata={"building_id": str(building.id), "sender_id": str(request.user.pk)},
                sender=request.user,
            )
            created += 1

        return Response({"created": created, "building_id": str(building.id)}, status=201)
