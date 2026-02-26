"""Apartment views — Sprint 2 + Sprint 4 balance endpoint."""
from decimal import Decimal

from django.db.models import Sum
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
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

    # ── Sign-up wizard helpers ─────────────────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="available",
            permission_classes=[IsAuthenticated])
    def available(self, request):
        """
        GET /api/v1/apartments/available/?building_id={id}
        Returns unowned apartments for a building.
        Used in the owner sign-up wizard so the user can pick their unit.
        """
        building_id = request.query_params.get("building_id")
        if not building_id:
            return Response(
                {"detail": "building_id query parameter is required."},
                status=400,
            )
        apartments = (
            Apartment.objects
            .filter(building_id=building_id, owner__isnull=True)
            .order_by("floor", "unit_number")
        )
        return Response(ApartmentSerializer(apartments, many=True).data)

    @action(detail=True, methods=["post"], url_path="claim",
            permission_classes=[IsAuthenticated])
    def claim(self, request, pk=None):
        """
        POST /api/v1/apartments/{id}/claim/
        An owner-role user claims an unowned apartment during sign-up.
        Sets owner = request.user, status = occupied, and links user to building.
        """
        if request.user.role != "owner":
            return Response(
                {"detail": "Only users with role 'owner' can claim apartments."},
                status=403,
            )
        try:
            apartment = Apartment.objects.select_related("building").get(pk=pk)
        except Apartment.DoesNotExist:
            return Response({"detail": "Apartment not found."}, status=404)

        if apartment.owner is not None:
            return Response(
                {"detail": "This apartment is already assigned to an owner."},
                status=409,
            )

        apartment.owner = request.user
        apartment.status = "occupied"
        apartment.save(update_fields=["owner", "status", "updated_at"])

        # Auto-join the owner to the building so they can see it
        from apps.buildings.models import UserBuilding
        UserBuilding.objects.get_or_create(user=request.user, building=apartment.building)

        log_action(
            user=request.user,
            action="claim",
            entity="apartment",
            entity_id=apartment.pk,
            changes={"owner": {"before": None, "after": str(request.user.pk)}},
            request=request,
        )
        return Response(ApartmentSerializer(apartment).data)

    # ── Sprint 4: balance breakdown ─────────────────────────────────────────────

    @action(detail=True, methods=["get"], url_path="balance",
            permission_classes=[IsAuthenticated])
    def balance(self, request, pk=None):
        """
        GET /api/v1/apartments/{id}/balance/

        Returns the current balance breakdown for an apartment.
          - Admin: can view any apartment.
          - Owner: can view their own apartment only (403 otherwise).
        """
        apt = self.get_object()

        if request.user.role != "admin" and apt.owner != request.user:
            return Response(
                {"detail": "You do not have permission to view this apartment's balance."},
                status=403,
            )

        # Lazy imports to avoid circular dependency at module load time
        from apps.expenses.models import ApartmentExpense
        from apps.payments.models import Payment

        total_owed = (
            ApartmentExpense.objects
            .filter(apartment=apt, expense__deleted_at__isnull=True)
            .aggregate(s=Sum("share_amount"))["s"]
            or Decimal("0.00")
        )
        total_paid = (
            Payment.objects
            .filter(apartment=apt)
            .aggregate(s=Sum("amount_paid"))["s"]
            or Decimal("0.00")
        )

        return Response({
            "apartment_id":    str(apt.pk),
            "current_balance": apt.balance,
            "total_owed":      total_owed,
            "total_paid":      total_paid,
            "is_credit":       apt.balance < Decimal("0.00"),
        })
