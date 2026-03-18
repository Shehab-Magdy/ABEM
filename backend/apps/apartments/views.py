"""Apartment views — Sprint 2 + Sprint 4 balance endpoint."""
from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from django_filters.rest_framework import DjangoFilterBackend

from django.utils.translation import gettext_lazy as _
from apps.audit.mixins import log_action
from apps.authentication.permissions import IsAdminRole

from .models import Apartment, UnitInvitation
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

        # Owners see apartments where they are the primary owner OR in the owners M2M
        from django.db.models import Q
        return qs.filter(
            Q(owner=self.request.user) | Q(owners=self.request.user)
        ).distinct()

    # ── Permissions ────────────────────────────────────────────────────────────

    def get_permissions(self):
        if self.action == "invite_validate":
            return [AllowAny()]
        write_actions = ("create", "partial_update", "update", "destroy", "invite")
        if self.action in write_actions:
            return [IsAuthenticated(), IsAdminRole()]
        return [IsAuthenticated()]

    # ── Write helpers ──────────────────────────────────────────────────────────

    def perform_create(self, serializer):
        instance = serializer.save()
        # If an owner was set on creation, auto-link them to the building
        if instance.owner is not None:
            from apps.buildings.models import UserBuilding
            UserBuilding.objects.get_or_create(user=instance.owner, building=instance.building)
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
        # If an owner was assigned, auto-link them to the building
        if "owner" in serializer.validated_data and instance.owner is not None:
            from apps.buildings.models import UserBuilding
            UserBuilding.objects.get_or_create(user=instance.owner, building=instance.building)
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
                {"detail": _("building_id query parameter is required.")},
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
        Any authenticated user (admin or owner) claims an unowned apartment.
        Sets owner = request.user, status = occupied, and links user to building.
        """
        try:
            apartment = Apartment.objects.select_related("building").get(pk=pk)
        except Apartment.DoesNotExist:
            return Response({"detail": _("Apartment not found.")}, status=404)

        if apartment.owner is not None:
            return Response(
                {"detail": _("This apartment is already assigned to an owner.")},
                status=409,
            )

        apartment.owner = request.user
        apartment.status = "occupied"
        apartment.save(update_fields=["owner", "status", "updated_at"])
        apartment.owners.add(request.user)

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

    # ── Unit invitation ────────────────────────────────────────────────────────

    @action(detail=True, methods=["post"], url_path="invite",
            permission_classes=[IsAuthenticated, IsAdminRole])
    def invite(self, request, pk=None):  # noqa: ARG002
        """
        POST /api/v1/apartments/{id}/invite/
        Admin creates (or re-creates) an invite token for a unit.
        Body: {"email": "owner@example.com"}
        Returns: {token, invited_email, expires_at}
        """
        apartment = self.get_object()
        email = request.data.get("email", "").strip().lower()
        if not email:
            return Response({"detail": _("email is required.")}, status=400)

        # Invalidate any existing unused invites for this unit+email
        UnitInvitation.objects.filter(
            apartment=apartment, invited_email=email, used_at__isnull=True
        ).update(expires_at=timezone.now())

        invite = UnitInvitation.objects.create(
            apartment=apartment,
            invited_email=email,
            invited_by=request.user,
            expires_at=timezone.now() + timedelta(days=30),
        )
        return Response({
            "token": str(invite.token),
            "registration_code": invite.registration_code,
            "invited_email": invite.invited_email,
            "expires_at": invite.expires_at,
        }, status=201)

    @action(detail=False, methods=["get"], url_path="invite/validate",
            permission_classes=[AllowAny], authentication_classes=[])
    def invite_validate(self, request):
        """
        GET /api/v1/apartments/invite/validate/?token={token}
        GET /api/v1/apartments/invite/validate/?code={code}
        Public endpoint — validates an invite token or registration code and returns unit/building info.
        """
        token = request.query_params.get("token")
        code = request.query_params.get("code")
        if not token and not code:
            return Response({"detail": _("token or code is required.")}, status=400)
        try:
            if token:
                invite = UnitInvitation.objects.select_related(
                    "apartment__building"
                ).get(token=token)
            else:
                invite = UnitInvitation.objects.select_related(
                    "apartment__building"
                ).get(registration_code=code.upper())
        except UnitInvitation.DoesNotExist:
            return Response({"detail": _("Invalid invite link or code.")}, status=404)

        if not invite.is_valid:
            return Response({"detail": _("This invite link has expired or already been used.")}, status=410)

        apt = invite.apartment
        return Response({
            "apartment_id": str(apt.id),
            "unit_number": apt.unit_number,
            "unit_type": apt.unit_type,
            "building_id": str(apt.building.id),
            "building_name": apt.building.name,
            "building_city": apt.building.city,
            "invited_email": invite.invited_email,
        })

    @action(detail=False, methods=["post"], url_path="invite/use",
            permission_classes=[IsAuthenticated])
    def invite_use(self, request):
        """
        POST /api/v1/apartments/invite/use/
        Authenticated user redeems an invite token or registration code to claim the unit.
        Body: {"token": "..."} or {"code": "..."}
        """
        token = request.data.get("token", "").strip()
        code = request.data.get("code", "").strip().upper()
        if not token and not code:
            return Response({"detail": _("token or code is required.")}, status=400)
        try:
            if token:
                invite = UnitInvitation.objects.select_related(
                    "apartment__building"
                ).get(token=token)
            else:
                invite = UnitInvitation.objects.select_related(
                    "apartment__building"
                ).get(registration_code=code)
        except UnitInvitation.DoesNotExist:
            return Response({"detail": _("Invalid invite.")}, status=404)

        if not invite.is_valid:
            return Response({"detail": _("This invite link has expired or already been used.")}, status=410)

        apt = invite.apartment
        if apt.owners.filter(pk=request.user.pk).exists():
            return Response({"detail": _("You are already an owner of this unit.")}, status=409)

        # Only set primary owner if not yet assigned; otherwise just add to M2M
        if apt.owner is None:
            apt.owner = request.user
            apt.status = "occupied"
            apt.save(update_fields=["owner", "status", "updated_at"])
        apt.owners.add(request.user)

        invite.used_at = timezone.now()
        invite.save(update_fields=["used_at"])

        from apps.buildings.models import UserBuilding
        UserBuilding.objects.get_or_create(user=request.user, building=apt.building)

        log_action(
            user=request.user,
            action="claim",
            entity="apartment",
            entity_id=apt.pk,
            changes={"owner": {"before": None, "after": str(request.user.pk)}, "via": "invite"},
            request=request,
        )
        return Response(ApartmentSerializer(apt).data)

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

        if request.user.role != "admin" and apt.owner != request.user and not apt.owners.filter(pk=request.user.pk).exists():
            return Response(
                {"detail": _("You do not have permission to view this apartment's balance.")},
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
