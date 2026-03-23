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

from django.utils.translation import gettext_lazy as _
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
            # Members of this building PLUS owner-role users created by the
            # requesting admin who have no building yet (so freshly admin-created
            # owners appear in the invite / assign-owner autocomplete).
            return base.filter(
                Q(buildings__id=building_id)
                | Q(
                    role="owner",
                    created_by=requesting_admin,
                    buildings__isnull=True,
                    administered_buildings__isnull=True,
                    co_administered_buildings__isnull=True,
                )
            ).distinct().order_by("-created_at")

        # Default: scope to users in buildings this admin manages (as primary admin or co-admin)
        # PLUS users this admin created (FE-01)
        managed_ids = Building.objects.filter(
            Q(admin=requesting_admin) | Q(co_admins=requesting_admin)
        ).values_list("id", flat=True)

        return base.filter(
            Q(buildings__id__in=managed_ids)
            | Q(administered_buildings__id__in=managed_ids)
            | Q(co_administered_buildings__id__in=managed_ids)
            | Q(created_by=requesting_admin)
        ).distinct().order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "create":
            return RegisterUserSerializer
        if self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        if self.action == "reset_password":
            return AdminResetPasswordSerializer
        return UserSerializer

    def get_serializer_context(self):
        """Ensure the request object is always available in serializer context."""
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def perform_update(self, serializer):
        """Override to handle non-model virtual fields in audit logging."""
        # Collect old values only for real model fields (skip virtual fields)
        skip_fields = {"buildings", "apartment_ids"}
        model_fields = {
            field: getattr(serializer.instance, field)
            for field in serializer.validated_data
            if field not in skip_fields and hasattr(serializer.instance, field)
        }
        instance = serializer.save()
        changes = {
            field: {"before": str(model_fields.get(field, "")), "after": str(getattr(instance, field, ""))}
            for field in model_fields
        }
        log_action(
            user=self.request.user,
            action="update",
            entity=self.audit_entity or instance.__class__.__name__.lower(),
            entity_id=instance.pk,
            changes=changes,
            request=self.request,
        )

    # ── Custom actions ────────────────────────────────────────────────────────

    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request, pk=None):
        user = self.get_object()
        if user == request.user:
            return Response(
                {"detail": _("You cannot deactivate your own account.")},
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
        return Response({"detail": _("User %(email)s deactivated.") % {"email": user.email}})

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
        return Response({"detail": _("User %(email)s activated.") % {"email": user.email}})

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
                {"detail": _("Provide messaging_blocked or individual_messaging_blocked.")},
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
        user.must_change_password = True
        user.save(update_fields=["password", "must_change_password"])
        log_action(
            user=request.user,
            action="reset_password",
            entity="user",
            entity_id=user.id,
            request=request,
        )
        return Response({"detail": _("Password reset for %(email)s.") % {"email": user.email}})
