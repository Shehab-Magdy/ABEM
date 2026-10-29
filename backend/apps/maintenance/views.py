from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.authentication.permissions import IsAdminRole
from apps.buildings.scoping import ensure_manages, managed_buildings

from .models import MaintenanceReport, ReportStatus
from .serializers import MaintenanceReportSerializer


class MaintenanceReportViewSet(ModelViewSet):
    """
    POST   /maintenance/        – any member of the building files a report
    GET    /maintenance/        – admins: reports in buildings they manage; residents: their building's reports
    PATCH  /maintenance/{id}/   – admins only, to change the status
    """

    serializer_class = MaintenanceReportSerializer
    http_method_names = ["get", "post", "patch", "options", "head"]

    def get_queryset(self):
        qs = MaintenanceReport.objects.select_related("building", "reporter")
        user = self.request.user
        if user.role == "admin":
            qs = qs.filter(building__in=managed_buildings(user))
        else:
            qs = qs.filter(building__members=user).distinct()
        if status_param := self.request.query_params.get("status"):
            qs = qs.filter(status=status_param)
        return qs

    def get_permissions(self):
        if self.action == "partial_update":
            return [IsAuthenticated(), IsAdminRole()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        building = serializer.validated_data["building"]
        user = self.request.user
        if user.role == "admin":
            ensure_manages(user, building)
        elif not building.members.filter(pk=user.pk).exists():
            raise PermissionDenied("You are not a member of this building.")
        serializer.save(reporter=user)

    def partial_update(self, request, *args, **kwargs):
        """Admins may only change the status."""
        report = self.get_object()
        status_value = request.data.get("status")
        if status_value not in ReportStatus.values:
            from rest_framework.response import Response
            return Response({"detail": "Invalid status."}, status=400)
        report.status = status_value
        report.save(update_fields=["status", "updated_at"])
        return self.retrieve(request, *args, **kwargs)
