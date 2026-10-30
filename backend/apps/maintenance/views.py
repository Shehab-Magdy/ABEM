from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.authentication.permissions import IsAdminRole
from apps.buildings.models import UserBuilding
from apps.buildings.scoping import ensure_manages, managed_buildings
from apps.notifications.models import NotificationType
from apps.notifications.services import notify_user

from .models import MaintenanceReport, ReportStatus, WorkOrder
from .serializers import MaintenanceReportSerializer, WorkOrderSerializer


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


class WorkOrderViewSet(ModelViewSet):
    """
    POST  /maintenance/work-orders/        {report_id, contractor_id?, scheduled_on?, notes?} - take a report on
    PATCH /maintenance/work-orders/{id}/   status (assigned / in_progress / done), completed_on, expense_id (the cost), notes
    The report follows the order (in progress / done) and the resident who reported it is told when it is done.
    Admins and board members of the building write; the order is visible on the report to everyone who sees it.
    """

    serializer_class = WorkOrderSerializer
    http_method_names = ["get", "post", "patch", "options", "head"]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = WorkOrder.objects.select_related("report__building", "contractor", "expense")
        if user.role == "admin":
            return qs.filter(report__building__in=managed_buildings(user))
        return qs.filter(report__building__members=user).distinct()

    def _check(self, building):
        user = self.request.user
        board = UserBuilding.objects.filter(user=user, building=building).exclude(board_role="").exists()
        if not (managed_buildings(user).filter(pk=building.pk).exists() or board):
            raise PermissionDenied(_("Only the building's admins and board can manage work orders."))

    def perform_create(self, serializer):
        report = serializer.validated_data["report"]
        self._check(report.building)  # permission first, so outsiders learn nothing about the report
        if WorkOrder.objects.filter(report=report).exists():
            raise ValidationError({"report_id": _("This report already has a work order.")})
        serializer.save(created_by=self.request.user)
        if report.status == "open":
            report.status = "in_progress"
            report.save(update_fields=["status", "updated_at"])

    def perform_update(self, serializer):
        order = serializer.instance
        self._check(order.report.building)
        order = serializer.save()
        report = order.report
        if order.status == "done":
            order.completed_on = order.completed_on or timezone.localdate()
            order.save(update_fields=["completed_on"])
            if report.status != "done":
                report.status = "done"
                report.save(update_fields=["status", "updated_at"])
                self._tell_reporter(report)
        elif order.status == "in_progress" and report.status == "open":
            report.status = "in_progress"
            report.save(update_fields=["status", "updated_at"])

    def _tell_reporter(self, report):
        if report.reporter_id and report.reporter.is_active:
            ar = getattr(report.reporter, "preferred_language", "ar") == "ar"
            notify_user(
                user=report.reporter, notification_type=NotificationType.ANNOUNCEMENT,
                title="تم إنجاز بلاغ الصيانة" if ar else "Your maintenance report is done",
                body=report.get_category_display(), metadata={"report_id": str(report.pk)},
            )
