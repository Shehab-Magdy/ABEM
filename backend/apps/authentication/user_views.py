"""
Admin-only user management viewset.
Mounted at /api/v1/users/ via config/urls.py.
"""
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend

from apps.audit.mixins import AuditLogMixin, log_action
from .permissions import IsAdminRole
from .serializers import (
    AdminResetPasswordSerializer,
    RegisterUserSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

User = get_user_model()


class UserViewSet(AuditLogMixin, ModelViewSet):
    """
    Full CRUD for users (Admin only).

    GET    /api/v1/users/            – list all users (paginated, filterable)
    POST   /api/v1/users/            – create a new user
    GET    /api/v1/users/{id}/       – retrieve user details
    PATCH  /api/v1/users/{id}/       – update profile + role
    DELETE /api/v1/users/{id}/       – hard delete (use deactivate for soft disable)
    POST   /api/v1/users/{id}/deactivate/    – deactivate account
    POST   /api/v1/users/{id}/activate/      – reactivate account
    POST   /api/v1/users/{id}/reset-password/ – admin-initiated password reset
    """

    permission_classes = [IsAdminRole]
    audit_entity = "user"

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["role", "is_active"]
    search_fields = ["email", "first_name", "last_name"]
    ordering_fields = ["created_at", "email", "role"]

    def get_queryset(self):
        from apps.buildings.models import Building

        requesting_admin = self.request.user
        building_id = self.request.query_params.get("building_id")
        base = User.objects.filter(is_superuser=False)

        if building_id:
            # Scoped to members of one specific building (used by invite-owner autocomplete)
            return base.filter(buildings__id=building_id).distinct().order_by("-created_at")

        # Default: scope to users in buildings this admin manages (as primary admin or co-admin)
        managed_ids = Building.objects.filter(
            Q(admin=requesting_admin) | Q(co_admins=requesting_admin)
        ).values_list("id", flat=True)

        return base.filter(
            Q(buildings__id__in=managed_ids)
            | Q(administered_buildings__id__in=managed_ids)
            | Q(co_administered_buildings__id__in=managed_ids)
        ).distinct().order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "create":
            return RegisterUserSerializer
        if self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        if self.action == "reset_password":
            return AdminResetPasswordSerializer
        return UserSerializer

    # ── Custom actions ────────────────────────────────────────────────────────

    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request, pk=None):
        user = self.get_object()
        if user == request.user:
            return Response(
                {"detail": "You cannot deactivate your own account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.is_active = False
        user.save(update_fields=["is_active"])
        log_action(
            user=request.user,
            action="deactivate",
            entity="user",
            entity_id=user.id,
            request=request,
        )
        return Response({"detail": f"User {user.email} deactivated."})

    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.failed_login_attempts = 0
        user.locked_until = None
        user.save(update_fields=["is_active", "failed_login_attempts", "locked_until"])
        log_action(
            user=request.user,
            action="activate",
            entity="user",
            entity_id=user.id,
            request=request,
        )
        return Response({"detail": f"User {user.email} activated."})

    @action(detail=True, methods=["post"], url_path="set-messaging-block")
    def set_messaging_block(self, request, pk=None):
        """
        POST /api/v1/users/{id}/set-messaging-block/
        Body: {"messaging_blocked": bool, "individual_messaging_blocked": bool}
        """
        user = self.get_object()
        data = request.data
        update_fields = []

        if "messaging_blocked" in data:
            user.messaging_blocked = bool(data["messaging_blocked"])
            update_fields.append("messaging_blocked")
        if "individual_messaging_blocked" in data:
            user.individual_messaging_blocked = bool(data["individual_messaging_blocked"])
            update_fields.append("individual_messaging_blocked")

        if not update_fields:
            return Response(
                {"detail": "Provide messaging_blocked or individual_messaging_blocked."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.save(update_fields=update_fields)
        log_action(
            user=request.user,
            action="set_messaging_block",
            entity="user",
            entity_id=user.id,
            request=request,
        )
        return Response({
            "messaging_blocked": user.messaging_blocked,
            "individual_messaging_blocked": user.individual_messaging_blocked,
        })

    @action(detail=True, methods=["post"], url_path="reset-password")
    def reset_password(self, request, pk=None):
        user = self.get_object()
        serializer = AdminResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        log_action(
            user=request.user,
            action="reset_password",
            entity="user",
            entity_id=user.id,
            request=request,
        )
        return Response({"detail": f"Password reset for {user.email}."})
