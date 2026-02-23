"""Building views – stubs to be fully implemented in Sprint 2."""
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from .models import Building


class BuildingViewSet(ModelViewSet):
    queryset = Building.objects.none()
    # TODO Sprint 2: add serializer, permissions, queryset scoped to tenant
