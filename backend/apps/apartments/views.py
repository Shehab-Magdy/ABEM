"""Apartment views – stubs to be fully implemented in Sprint 2."""
from rest_framework.viewsets import ModelViewSet
from .models import Apartment


class ApartmentViewSet(ModelViewSet):
    queryset = Apartment.objects.none()
    # TODO Sprint 2: serializer, permissions, balance endpoint
