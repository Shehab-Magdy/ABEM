"""Apartment views — Sprint 2."""
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from django_filters.rest_framework import DjangoFilterBackend

from apps.audit.mixins import log_action
from apps.authentication.permissions import IsAdminRole

from .models import Apartment
from .serializers import ApartmentSerializer


class ApartmentViewSet(ModelViewSet):
    """
    CRUD for apartment units with multi-tenant scoping.

    Permissions:
      - Admin: full CRUD on all apartments.
      - Owner: read-only on their own apartment only.
      - Unauthenticated: 401.
    """

    serializer_class = ApartmentSerializer
    http_method_names = ["get", "post", "patch", "delete", "options", "head"]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["unit_type", "status", "owner"]
    search_fields = ["unit_number"]
    ordering_fields = ["floor", "unit_number", "created_at"]
    ordering = ["building", "floor", "unit_number"]

    # ── Scoping ────────────────────────────────────────────────────────────────

    def get_queryset(self):
        qs = Apartment.objects.select_related("building", "owner")

        if self.request.user.role == "admin":
            # Admin may optionally filter by building_id query param
            building_id = self.request.query_params.get("building_id")
            if building_id:
                qs = qs.filter(building_id=building_id)
            return qs

        # Owners see only the apartments assigned to them
        return qs.filter(owner=self.request.user)

    # ── Permissions ────────────────────────────────────────────────────────────

    def get_permissions(self):
        write_actions = ("create", "partial_update", "update", "destroy")
        if self.action in write_actions:
            return [IsAuthenticated(), IsAdminRole()]
        return [IsAuthenticated()]

    # ── Write helpers ──────────────────────────────────────────────────────────

    def perform_create(self, serializer):
        instance = serializer.save()
        log_action(
            user=self.request.user,
            action="create",
            entity="apartment",
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
            field: {
                "before": str(old.get(field, "")),
                "after": str(getattr(instance, field, "")),
            }
            for field in serializer.validated_data
        }
        log_action(
            user=self.request.user,
            action="update",
            entity="apartment",
            entity_id=instance.pk,
            changes=changes,
            request=self.request,
        )

    def perform_destroy(self, instance):
        log_action(
            user=self.request.user,
            action="delete",
            entity="apartment",
            entity_id=instance.pk,
            request=self.request,
        )
        instance.delete()
