"""Apartment views — Sprint 2 + Sprint 4 balance endpoint."""
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from django_filters.rest_framework import DjangoFilterBackend

from django.utils.translation import gettext_lazy as _
from apps.audit.mixins import log_action
from apps.authentication.permissions import IsAdminRole

from apps.buildings.scoping import ensure_manages, managed_buildings

from .models import Apartment, ClaimStatus, UnitClaimRequest, UnitInvitation
from .serializers import ApartmentSerializer, UnitClaimRequestSerializer


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
            # Admins only see units in buildings they manage
            qs = qs.filter(building__in=managed_buildings(self.request.user))
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
        building = serializer.validated_data["building"]
        ensure_manages(self.request.user, building)
        from rest_framework.exceptions import ValidationError

        from apps.plans.services import unit_room

        if not unit_room(building):
            raise ValidationError({"detail": _("Your plan's unit limit is reached. Upgrade the plan to add more units.")})
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

    def _hand_over(self, instance, previous):
        """R-25: the previous owner loses the unit and, unless they hold another one, the building."""
        from apps.buildings.models import UserBuilding
        from apps.notifications.services import building_admins, tell

        instance.owners.remove(previous)
        if instance.owner is not None:
            instance.owners.add(instance.owner)
        still_there = (
            Apartment.objects.filter(building=instance.building)
            .filter(Q(owner=previous) | Q(owners=previous))
            .exists()
        )
        if not still_there and previous.pk not in {u.pk for u in building_admins(instance.building)}:
            UserBuilding.objects.filter(user=previous, building=instance.building).delete()
        log_action(
            user=self.request.user,
            action="owner_changed",
            entity="apartment",
            entity_id=instance.pk,
            changes={
                "before": str(previous.pk),
                "after": str(instance.owner_id) if instance.owner_id else None,
                "balance": str(instance.balance),
            },
            request=self.request,
        )
        for admin in building_admins(instance.building):
            tell(
                admin,
                (
                    "Unit owner changed",
                    f"Unit {instance.unit_number} changed owner. Balance at handover: {instance.balance} EGP.",
                ),
                (
                    "تغيير مالك وحدة",
                    f"تغيّر مالك الوحدة {instance.unit_number}. الرصيد وقت التسليم: {instance.balance} ج.م.",
                ),
                {"apartment_id": str(instance.pk)},
            )

    def perform_update(self, serializer):
        old = {
            field: getattr(serializer.instance, field)
            for field in serializer.validated_data
        }
        previous_owner = serializer.instance.owner
        instance = serializer.save()
        if "owner" in serializer.validated_data and previous_owner and previous_owner.pk != instance.owner_id:
            self._hand_over(instance, previous_owner)
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
        except Apartment.DoesNotExist: # type: ignore[attr-defined]
            return Response({"detail": _("Apartment not found.")}, status=404)

        if request.user.role == "renter":
            return Response(
                {"detail": _("Renters join a unit through an invite from its owner.")}, status=403
            )

        if apartment.owner is not None:
            return Response(
                {"detail": _("This apartment is already assigned to an owner.")},
                status=409,
            )

        # Residents ask; the building's admin approves. Only an admin of this building
        # may take a unit directly (e.g. "claim for myself" on the Buildings page).
        if not managed_buildings(request.user).filter(pk=apartment.building_id).exists():
            try:
                UnitClaimRequest.objects.create(apartment=apartment, user=request.user)
            except IntegrityError:
                return Response({"detail": _("You already asked to claim this unit.")}, status=409)
            return Response(
                {"status": "pending", "detail": _("Request sent. The building admin will review it.")},
                status=202,
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
        Body: {"email": "owner@example.com"}  (email is optional; without it the
        link is a shareable one-time invite for the unit, e.g. via WhatsApp)
        Returns: {token, registration_code, invited_email, expires_at}
        """
        return self._issue_invite(request, self.get_object(), "owner")

    def _issue_invite(self, request, apartment, role):
        """Create a one-time invite for `apartment` (as its owner or as a renter) and return the link data."""
        email = (request.data.get("email") or "").strip().lower()
        if email:
            try:
                validate_email(email)
            except DjangoValidationError:
                return Response({"detail": _("Enter a valid email address.")}, status=400)

        # Invalidate any existing unused invites for this unit, email and role (or email-less
        # shareable invites for this unit when no email is given)
        UnitInvitation.objects.filter(
            apartment=apartment, invited_email=email, invited_role=role, used_at__isnull=True
        ).update(expires_at=timezone.now())

        invite = UnitInvitation.objects.create(
            apartment=apartment,
            invited_email=email,
            invited_role=role,
            invited_by=request.user,
            expires_at=timezone.now() + timedelta(days=30),
        )
        return Response({
            "token": str(invite.token),
            "registration_code": invite.registration_code,
            "invited_email": invite.invited_email,
            "expires_at": invite.expires_at,
        }, status=201)

    @action(detail=True, methods=["post"], url_path="invite-renter",
            permission_classes=[IsAuthenticated])
    def invite_renter(self, request, pk=None):
        """
        POST /api/v1/apartments/{id}/invite-renter/
        The unit's owner (or the building admin) invites a renter to live in the unit.
        Renters see the unit's dues, pay, report problems and read the treasury, but cannot
        invite others or claim units. Same body and result as `invite`.
        """
        if request.user.role == "renter":
            return Response({"detail": _("Renters cannot invite other residents.")}, status=403)
        return self._issue_invite(request, self.get_object(), "renter")

    @action(detail=True, methods=["post"], url_path="remove-renter",
            permission_classes=[IsAuthenticated])
    def remove_renter(self, request, pk=None):
        """
        POST /api/v1/apartments/{id}/remove-renter/ {"user_id": ...}
        The unit's owner (or the building admin) ends a renter's link to the unit.
        """
        if request.user.role == "renter":
            return Response({"detail": _("Renters cannot remove other residents.")}, status=403)
        apartment = self.get_object()
        renter = apartment.owners.filter(pk=request.data.get("user_id"), role="renter").first() \
            if request.data.get("user_id") else None
        if renter is None:
            return Response({"detail": _("That renter does not live in this unit.")}, status=404)
        with transaction.atomic():
            apartment.owners.remove(renter)
            from apps.buildings.models import UserBuilding
            still_there = Apartment.objects.filter(building=apartment.building).filter(
                Q(owner=renter) | Q(owners=renter)
            ).exists()
            if not still_there:
                UserBuilding.objects.filter(user=renter, building=apartment.building).delete()
        log_action(
            user=request.user, action="remove_renter", entity="apartment", entity_id=apartment.pk,
            changes={"renter": str(renter.pk)}, request=request,
        )
        return Response(ApartmentSerializer(apartment).data)

    @action(detail=False, methods=["get"], url_path="invite/validate",
            permission_classes=[AllowAny], authentication_classes=[],
            throttle_classes=[AnonRateThrottle])
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
        except (UnitInvitation.DoesNotExist, DjangoValidationError, ValueError):
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
            # The long token is a secret held by the invitee; the short code is guessable,
            # so only token links reveal the invited email (used to prefill sign-up).
            "invited_email": invite.invited_email if token else "",
            "role": invite.invited_role,
        })

    @action(detail=False, methods=["post"], url_path="invite/use",
            permission_classes=[IsAuthenticated], throttle_classes=[UserRateThrottle])
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
        with transaction.atomic():
            try:
                # Lock the invite row so two people cannot redeem the same link at once
                locked = UnitInvitation.objects.select_for_update()
                invite = locked.get(token=token) if token else locked.get(registration_code=code)
            except (UnitInvitation.DoesNotExist, DjangoValidationError, ValueError):
                return Response({"detail": _("Invalid invite.")}, status=404)

            if not invite.is_valid:
                return Response({"detail": _("This invite link has expired or already been used.")}, status=410)

            # An invite sent to a specific email can only be redeemed by that account.
            # Email-less shareable links are open to whoever opens them first.
            if invite.invited_email and invite.invited_email.lower() != request.user.email.lower():
                return Response(
                    {"detail": _("This invite was sent to a different email address.")}, status=403
                )

            return self._redeem_invite(request, invite)

    def _redeem_invite(self, request, invite):
        apt = Apartment.objects.select_related("building").get(pk=invite.apartment_id)
        if apt.owners.filter(pk=request.user.pk).exists():
            return Response({"detail": _("You are already an owner of this unit.")}, status=409)

        # Only set primary owner if not yet assigned; otherwise just add to M2M.
        # A renter lives in the unit but never becomes its owner.
        if apt.owner is None and invite.invited_role == "owner":
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


class UnitClaimRequestViewSet(ReadOnlyModelViewSet):
    """
    GET  /apartments/claim-requests/               – admins: requests in buildings they manage; residents: their own
    POST /apartments/claim-requests/{id}/approve/  – admin makes the requester an owner of the unit
    POST /apartments/claim-requests/{id}/reject/   – admin declines
    """

    serializer_class = UnitClaimRequestSerializer

    def get_queryset(self):
        qs = UnitClaimRequest.objects.select_related("apartment__building", "user")
        user = self.request.user
        if user.role == "admin":
            qs = qs.filter(apartment__building__in=managed_buildings(user))
        else:
            qs = qs.filter(user=user)
        if status_param := self.request.query_params.get("status"):
            qs = qs.filter(status=status_param)
        return qs

    def get_permissions(self):
        if self.action in ("approve", "reject"):
            return [IsAuthenticated(), IsAdminRole()]
        return [IsAuthenticated()]

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        with transaction.atomic():
            req = UnitClaimRequest.objects.select_for_update().get(pk=self.get_object().pk)
            if req.status != ClaimStatus.PENDING:
                return Response({"detail": _("This request was already reviewed.")}, status=409)
            apt = Apartment.objects.select_for_update().select_related("building").get(pk=req.apartment_id)
            # First approved resident becomes the primary owner; later ones are co-owners
            if apt.owner is None:
                apt.owner = req.user
                apt.status = "occupied"
                apt.save(update_fields=["owner", "status", "updated_at"])
            apt.owners.add(req.user)
            from apps.buildings.models import UserBuilding
            UserBuilding.objects.get_or_create(user=req.user, building=apt.building)
            req.status = ClaimStatus.APPROVED
            req.reviewed_by = request.user
            req.reviewed_at = timezone.now()
            req.save()
        log_action(
            user=request.user, action="claim", entity="apartment", entity_id=apt.pk,
            changes={"owner": {"before": None, "after": str(req.user_id)}, "via": "approval"}, request=request,
        )
        return Response(UnitClaimRequestSerializer(req).data)

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        req = self.get_object()
        if req.status != ClaimStatus.PENDING:
            return Response({"detail": _("This request was already reviewed.")}, status=409)
        req.status = ClaimStatus.REJECTED
        req.reviewed_by = request.user
        req.reviewed_at = timezone.now()
        req.save()
        return Response(UnitClaimRequestSerializer(req).data)
