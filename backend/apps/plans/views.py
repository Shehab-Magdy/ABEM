from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.views import IsPlatformOwner
from apps.buildings.models import Building
from apps.buildings.scoping import ensure_manages, managed_buildings

from .models import Plan, PlanPayment, PlanPaymentStatus, PlatformSettings
from .serializers import PlanPaymentSerializer, PlanSerializer
from .services import effective_plan, extend


class PlanViewSet(viewsets.ModelViewSet):
    """Everyone signed in can read the plans; only platform owners change prices and limits."""

    serializer_class = PlanSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]
    pagination_class = None

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsPlatformOwner()]

    def get_queryset(self):
        qs = Plan.objects.all()
        return qs if self.request.user.is_superuser else qs.filter(is_active=True)


class CurrentPlanView(APIView):
    """GET /plans/current/?building_id= — the plan a building is on, its limits and use, and where to pay."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        building = Building.objects.filter(pk=request.query_params.get("building_id"), deleted_at__isnull=True).first()
        visible = building and (
            managed_buildings(request.user).filter(pk=building.pk).exists()
            or building.members.filter(pk=request.user.pk).exists()
        )
        if not visible:
            return Response({"detail": _("Not found.")}, status=404)
        plan, paid_until, trial = effective_plan(building)
        return Response({
            "plan": PlanSerializer(plan).data,
            "paid_until": paid_until,
            "on_trial": trial,
            "units": building.apartments.count(),
            "instapay_address": PlatformSettings.load().instapay_address,
        })


class PlanPaymentViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """Building admins report an InstaPay transfer for a plan; platform owners confirm or reject it."""

    serializer_class = PlanPaymentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        qs = PlanPayment.objects.select_related("building", "plan")
        user = self.request.user
        if user.is_superuser:
            return qs
        return qs.filter(building__in=managed_buildings(user)) if user.role == "admin" else qs.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role != "admin":
            raise ValidationError(_("Only a building admin can pay for a plan."))
        building, plan = serializer.validated_data["building"], serializer.validated_data["plan"]
        ensure_manages(user, building)
        period = serializer.validated_data["period"]
        amount = plan.price_yearly if period == "yearly" else plan.price_monthly
        if amount <= 0:
            raise ValidationError(_("This plan is free; there is nothing to pay."))
        serializer.save(created_by=user, amount=amount)

    def _review(self, request, pk, status):
        if not request.user.is_superuser:
            return Response({"detail": _("Not found.")}, status=404)
        with transaction.atomic():
            payment = PlanPayment.objects.select_for_update().get(pk=pk)
            if payment.status != PlanPaymentStatus.PENDING:
                raise ValidationError(_("This payment was already reviewed."))
            payment.status, payment.reviewed_at = status, timezone.now()
            payment.save(update_fields=["status", "reviewed_at"])
            if status == PlanPaymentStatus.CONFIRMED:
                extend(payment.building, payment.plan, payment.period)
        return Response(self.get_serializer(payment).data)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        return self._review(request, pk, PlanPaymentStatus.CONFIRMED)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._review(request, pk, PlanPaymentStatus.REJECTED)


class SettingsView(APIView):
    """GET/PATCH /plans/settings/ — platform owners set the InstaPay address and trial length."""

    permission_classes = [IsAuthenticated, IsPlatformOwner]

    def get(self, request):
        s = PlatformSettings.load()
        return Response({"instapay_address": s.instapay_address, "trial_days": s.trial_days})

    def patch(self, request):
        s = PlatformSettings.load()
        s.instapay_address = str(request.data.get("instapay_address", s.instapay_address))[:120]
        try:
            s.trial_days = max(0, min(90, int(request.data.get("trial_days", s.trial_days))))
        except (TypeError, ValueError):
            raise ValidationError({"trial_days": _("Must be a whole number.")})
        s.save()
        return Response({"instapay_address": s.instapay_address, "trial_days": s.trial_days})
