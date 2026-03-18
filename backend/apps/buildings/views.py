"""Building views — Sprint 2."""
from django.db import models
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from django_filters.rest_framework import DjangoFilterBackend

from django.utils.translation import gettext_lazy as _
from apps.audit.mixins import log_action
from apps.authentication.models import User
from apps.authentication.permissions import IsAdminRole

from .models import Building, UserBuilding
from .serializers import AssignUserSerializer, BuildingSerializer


class BuildingViewSet(ModelViewSet):
    """
    CRUD for buildings with multi-tenant scoping.

    Permissions:
      - Admin: full CRUD on all buildings.
      - Owner: read-only, limited to buildings they are members of.
      - Unauthenticated: 401 on every endpoint.
    """

    serializer_class = BuildingSerializer
    http_method_names = ["get", "post", "patch", "delete", "options", "head"]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["name", "address", "city"]
    ordering_fields = ["name", "created_at", "num_floors"]
    ordering = ["name"]

    # ── Scoping ────────────────────────────────────────────────────────────────

    def get_queryset(self):
        qs = Building.objects.filter(deleted_at__isnull=True)
        # Owners only see active buildings; admins see active + inactive (so they can reactivate)
        if not self.request.user.role == "admin":
            qs = qs.filter(is_active=True)
        return qs.filter(
            models.Q(admin=self.request.user)
            | models.Q(co_admins=self.request.user)
            | models.Q(members=self.request.user)
        ).distinct()

    # ── Permissions ────────────────────────────────────────────────────────────

    def get_permissions(self):
        write_actions = ("create", "partial_update", "update", "destroy", "assign_user", "deactivate", "activate")
        if self.action in write_actions:
            return [IsAuthenticated(), IsAdminRole()]
        return [IsAuthenticated()]

    # ── Write helpers ──────────────────────────────────────────────────────────

    def perform_create(self, serializer):
        # Use admin from payload if provided, else default to the creating user
        if "admin" not in serializer.validated_data:
            building = serializer.save(admin=self.request.user)
        else:
            building = serializer.save()
        # Always add the creating user as a member
        UserBuilding.objects.get_or_create(user=self.request.user, building=building)
        # Also add the assigned admin as a member if different from creator
        if building.admin != self.request.user:
            UserBuilding.objects.get_or_create(user=building.admin, building=building)
        log_action(
            user=self.request.user,
            action="create",
            entity="building",
            entity_id=building.pk,
            request=self.request,
        )

    def perform_update(self, serializer):
        old = {
            field: getattr(serializer.instance, field)
            for field in serializer.validated_data
        }
        instance = serializer.save()
        changes = {
            field: {
                "before": str(old.get(field, "")),
                "after": str(getattr(instance, field, "")),
            }
            for field in serializer.validated_data
        }
        log_action(
            user=self.request.user,
            action="update",
            entity="building",
            entity_id=instance.pk,
            changes=changes,
            request=self.request,
        )

    def perform_destroy(self, instance):
        log_action(
            user=self.request.user,
            action="delete",
            entity="building",
            entity_id=instance.pk,
            request=self.request,
        )
        instance.deleted_at = timezone.now()
        instance.is_active = False
        instance.save()

    # ── Custom actions ─────────────────────────────────────────────────────────

    @action(
        detail=True,
        methods=["post"],
        url_path="assign-user",
        permission_classes=[IsAuthenticated, IsAdminRole],
    )
    def assign_user(self, request, pk=None):
        """
        POST /buildings/{id}/assign-user/
        Body: {"user_id": "<uuid>"}
        Assigns an Owner-role user to this building.
        """
        building = self.get_object()
        serializer = AssignUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = User.objects.get(pk=serializer.validated_data["user_id"])
        _, created = UserBuilding.objects.get_or_create(user=user, building=building)

        log_action(
            user=request.user,
            action="update",
            entity="building",
            entity_id=building.pk,
            changes={"assigned_user": {"before": None, "after": str(user.pk)}},
            request=request,
        )

        http_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(
            {"detail": _("User '%(email)s' assigned to building '%(name)s'.") % {"email": user.email, "name": building.name}},
            status=http_status,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="deactivate",
        permission_classes=[IsAuthenticated, IsAdminRole],
    )
    def deactivate(self, request, pk=None):
        building = self.get_object()
        building.is_active = False
        building.save(update_fields=["is_active"])
        log_action(
            user=request.user,
            action="deactivate",
            entity="building",
            entity_id=building.pk,
            request=request,
        )
        return Response({"detail": _("Building '%(name)s' deactivated.") % {"name": building.name}})

    @action(
        detail=True,
        methods=["post"],
        url_path="activate",
        permission_classes=[IsAuthenticated, IsAdminRole],
    )
    def activate(self, request, pk=None):
        building = self.get_object()
        building.is_active = True
        building.save(update_fields=["is_active"])
        log_action(
            user=request.user,
            action="activate",
            entity="building",
            entity_id=building.pk,
            request=request,
        )
        return Response({"detail": _("Building '%(name)s' activated.") % {"name": building.name}})

    @action(
        detail=False,
        methods=["get"],
        url_path="directory",
        permission_classes=[IsAuthenticated],
    )
    def directory(self, request):
        """
        GET /buildings/directory/
        Returns active buildings the requesting user administers or is a member of.
        Used in the sign-up wizard so an owner can pick their building and unit.
        """
        user = request.user
        buildings = (
            Building.objects
            .filter(deleted_at__isnull=True, is_active=True)
            .filter(models.Q(admin=user) | models.Q(co_admins=user) | models.Q(members=user))
            .distinct()
            .order_by("name")
            .values("id", "name", "city", "country", "address", "num_floors")
        )
        return Response(list(buildings))

    @action(
        detail=True,
        methods=["get"],
        url_path="apartments",
        permission_classes=[IsAuthenticated],
    )
    def list_apartments(self, request, pk=None):
        """
        GET /buildings/{id}/apartments/
        Returns all active apartments belonging to this building.
        Admin sees all; Owner sees only their own apartment.
        """
        building = self.get_object()
        from apps.apartments.models import Apartment
        from apps.apartments.serializers import ApartmentSerializer

        qs = Apartment.objects.filter(building=building)
        if request.user.role == "owner":
            qs = qs.filter(owner=request.user)

        page = self.paginate_queryset(qs)
        serializer = ApartmentSerializer(
            page if page is not None else qs,
            many=True,
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)
