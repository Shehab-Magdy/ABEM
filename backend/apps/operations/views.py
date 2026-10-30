from django.db.models import Q
from django.utils.translation import gettext as _
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.buildings.models import Building, UserBuilding
from apps.buildings.scoping import managed_buildings

from .models import Contractor, Obligation
from .serializers import ContractorSerializer, ObligationSerializer
from .services import mark_done


def _visible_buildings(user):
    if user.role == "admin":
        return managed_buildings(user)
    return Building.objects.filter(members=user, deleted_at__isnull=True)


def _can_write(user, building) -> bool:
    """Admins of the building and every board member keep the contractors and the obligations calendar."""
    building_id = getattr(building, "pk", building)
    return managed_buildings(user).filter(pk=building_id).exists() or UserBuilding.objects.filter(
        user=user, building_id=building_id
    ).exclude(board_role="").exists()


class _BuildingRecords(ModelViewSet):
    """Members read, admins and the board write; nothing outside the user's buildings is visible."""

    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "options", "head"]
    model = None

    def get_queryset(self):
        qs = self.model.objects.filter(building__in=_visible_buildings(self.request.user)).select_related("building")
        if building_id := self.request.query_params.get("building_id"):
            qs = qs.filter(building_id=building_id)
        return qs

    def _check(self, building):
        if not _can_write(self.request.user, building):
            raise PermissionDenied(_("Only the building's admins and board can change this."))

    def perform_create(self, serializer):
        self._check(serializer.validated_data["building"])
        serializer.save()

    def perform_update(self, serializer):
        self._check(serializer.instance.building)
        serializer.save()

    def perform_destroy(self, instance):
        self._check(instance.building)
        instance.delete()


class ContractorViewSet(_BuildingRecords):
    model = Contractor
    serializer_class = ContractorSerializer


class ObligationViewSet(_BuildingRecords):
    model = Obligation
    serializer_class = ObligationSerializer

    def get_queryset(self):
        qs = super().get_queryset().select_related("contractor")
        if self.request.query_params.get("active") == "true":
            qs = qs.filter(is_active=True)
        return qs

    @action(detail=True, methods=["post"], url_path="done")
    def done(self, request, pk=None):
        obligation = self.get_object()
        self._check(obligation.building)
        return Response(self.get_serializer(mark_done(obligation)).data)
