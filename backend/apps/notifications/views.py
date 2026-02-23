"""Notification views – stubs to be implemented in Sprint 6."""
from rest_framework.viewsets import ModelViewSet
from .models import Notification


class NotificationViewSet(ModelViewSet):
    queryset = Notification.objects.none()
    # TODO Sprint 6: user-scoped list, mark-read action, preferences
