"""Building views — Sprint 2."""
from django.db import models, transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from django_filters.rest_framework import DjangoFilterBackend

from django.utils.translation import gettext_lazy as _
from apps.audit.mixins import log_action
from apps.authentication.models import User
from apps.authentication.permissions import IsAdminRole
from apps.authentication.serializers import UserSerializer

from .models import Building, BuildingCoAdmin, UserBuilding
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
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    http_method_names = ["get", "post", "patch", "delete", "options", "head"]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["name", "address", "city"]
    ordering_fields = ["name", "created_at", "num_floors"]
    ordering = ["name"]

    # ── Scoping ────────────────────────────────────────────────────────────────

    def get_queryset(self):
        qs = Building.objects.filter(deleted_at__isnull=True).prefetch_related(
            "co_admins", "userbuilding_set"
        )
        # Owners only see active buildings; admins see active + inactive (so they can reactivate)
        if not self.request.user.role == "admin":
            qs = qs.filter(is_active=True)
        if self.request.user.role == "admin":
            # Admins only manage buildings they administer (primary admin or co-admin)
            return qs.filter(
                models.Q(admin=self.request.user) | models.Q(co_admins=self.request.user)
            ).distinct()
        return qs.filter(members=self.request.user).distinct()

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
        # Dedicated audit entry when starting_balance is changed
        if "starting_balance" in serializer.validated_data and old.get("starting_balance") != instance.starting_balance:
            log_action(
                user=self.request.user,
                action="building.starting_balance_set",
                entity="building",
                entity_id=instance.pk,
                changes={
                    "starting_balance": {
                        "before": str(old.get("starting_balance", "")),
                        "after": str(instance.starting_balance),
                    },
                },
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
        ub, created = UserBuilding.objects.get_or_create(user=user, building=building)

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

    @action(detail=True, methods=["post"], url_path="transfer-admin", permission_classes=[IsAuthenticated, IsAdminRole])
    def transfer_admin(self, request, pk=None):
        """
        POST /buildings/{id}/transfer-admin/ {"user_id": ...}
        The primary administrator hands the building to one of its co-admins. The previous
        primary admin stays on as a co-admin; payments, expenses and the audit log are untouched.
        """
        building = self.get_object()
        if building.admin_id != request.user.pk:
            return Response({"detail": _("Only the building's primary administrator can hand it over.")}, status=403)

        target = building.co_admins.filter(pk=request.data.get("user_id"), role="admin", is_active=True).first() \
            if request.data.get("user_id") else None
        if target is None:
            return Response(
                {"detail": _("Choose one of the building's co-admins. Add them as a co-admin first.")}, status=400
            )

        with transaction.atomic():
            BuildingCoAdmin.objects.filter(building=building, user=target).delete()
            BuildingCoAdmin.objects.get_or_create(building=building, user=request.user)
            building.admin = target
            building.save(update_fields=["admin", "updated_at"])
            UserBuilding.objects.get_or_create(user=target, building=building)

        log_action(
            user=request.user, action="transfer_admin", entity="building", entity_id=building.pk,
            changes={"admin": {"before": str(request.user.pk), "after": str(target.pk)}}, request=request,
        )
        return Response(self.get_serializer(building).data)

    @action(detail=True, methods=["get"], url_path="statement", permission_classes=[IsAuthenticated])
    def statement(self, request, pk=None):
        """
        GET /buildings/{id}/statement/?month=YYYY-MM[&file_format=pdf]
        Monthly statement: opening balance, money received, expenses, closing balance and which units
        paid. Read-only; visible to the building's admins and residents. Units are shown by number only.
        """
        from django.http import HttpResponse

        from .statement import build_statement, parse_month, render_statement_pdf

        building = self.get_object()
        try:
            first_day = parse_month(request.query_params.get("month"))
        except (ValueError, TypeError):
            return Response({"detail": _("month must look like 2026-10.")}, status=400)

        data = build_statement(building, first_day)
        if (request.query_params.get("file_format") or "").lower() == "pdf":
            lang = getattr(request.user, "preferred_language", None) or "ar"
            try:
                pdf = render_statement_pdf(data, lang)
            except Exception as exc:  # WeasyPrint or its system libraries missing
                return Response({"detail": f"PDF generation failed: {exc}"}, status=503)
            response = HttpResponse(pdf, content_type="application/pdf")
            response["Content-Disposition"] = f'inline; filename="statement_{data["month"]}.pdf"'
            return response

        def money(value):
            return str(value)

        return Response({
            "building": data["building"],
            "month": data["month"],
            "opening_balance": money(data["opening_balance"]),
            "total_received": money(data["total_received"]),
            "total_expenses": money(data["total_expenses"]),
            "closing_balance": money(data["closing_balance"]),
            "received": [{**r, "amount": money(r["amount"])} for r in data["received"]],
            "expenses": [{**e, "amount": money(e["amount"])} for e in data["expenses"]],
            "units": [{**u, "balance_due": money(u["balance_due"])} for u in data["units"]],
            "units_paid": data["units_paid"],
            "units_total": data["units_total"],
        })

    @action(detail=True, methods=["get"], url_path="treasury", permission_classes=[IsAuthenticated])
    def treasury(self, request, pk=None):
        """
        GET /buildings/{id}/treasury/
        The building's current balance (خزينة العمارة): starting balance + payments received
        + asset sales - expenses. Read-only; visible to the building's admins and its residents.
        """
        from decimal import Decimal

        from django.db.models import Sum

        from apps.apartments.models import Apartment
        from apps.expenses.models import ApartmentExpense, Expense
        from apps.payments.models import AssetSale, Payment

        building = self.get_object()
        zero = Decimal("0.00")
        received = Payment.objects.filter(apartment__building=building).aggregate(s=Sum("amount_paid"))["s"] or zero
        sales = AssetSale.objects.filter(asset__building=building).aggregate(s=Sum("sale_price"))["s"] or zero
        spent = (
            Expense.objects.filter(building=building, deleted_at__isnull=True).aggregate(s=Sum("amount"))["s"] or zero
        )
        billed_ids = list(
            ApartmentExpense.objects.filter(expense__building=building, expense__deleted_at__isnull=True)
            .values_list("apartment_id", flat=True)
            .distinct()
        )
        paid_units = Apartment.objects.filter(id__in=billed_ids, balance__lte=0).count()

        return Response({
            "building_id": str(building.pk),
            "balance": str(building.starting_balance + received + sales - spent),
            "starting_balance": str(building.starting_balance),
            "total_received": str(received + sales),
            "total_expenses": str(spent),
            "units_billed": len(billed_ids),
            "units_paid": paid_units,
        })

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

    @action(
        detail=True,
        methods=["get"],
        url_path="members",
        permission_classes=[IsAuthenticated],
    )
    def members(self, request, pk=None):
        """
        GET /buildings/{id}/members/
        Returns active admin and owner users belonging to the building.
        """
        building = self.get_object()
        recipients = (
            User.objects.filter(
                userbuilding__building=building,
                is_active=True,
                role__in=["admin", "owner"],
            )
            .order_by("first_name", "last_name")
            .distinct()
        )
        serializer = UserSerializer(recipients, many=True, context={"request": request})
        return Response(serializer.data)
