from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .kpis import build_platform_kpis


class IsPlatformOwner(BasePermission):
    """The people who run 3maracom itself (Django superusers), never a building admin."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


class PlatformKpisView(APIView):
    """GET /analytics/platform/ — usage numbers across all buildings, for the platform owners only."""

    permission_classes = [IsAuthenticated, IsPlatformOwner]

    def get(self, request):
        return Response(build_platform_kpis())
