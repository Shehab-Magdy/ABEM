from rest_framework import serializers

from apps.buildings.models import Building
from apps.expenses.models import Expense
from apps.operations.models import Contractor

from .models import MaintenanceReport, WorkOrder


class MaintenanceReportSerializer(serializers.ModelSerializer):
    building_id = serializers.PrimaryKeyRelatedField(source="building", queryset=Building.objects.all())
    building_name = serializers.CharField(source="building.name", read_only=True)
    reporter_name = serializers.SerializerMethodField()

    class Meta:
        model = MaintenanceReport
        fields = [
            "id", "building_id", "building_name", "category", "description",
            "status", "reporter_name", "created_at", "work_order", "can_manage",
        ]
        read_only_fields = ["id", "status", "created_at"]

    work_order = serializers.SerializerMethodField()
    can_manage = serializers.SerializerMethodField()

    def get_can_manage(self, obj):
        """True when the viewer is a building admin or board member who may take the report on."""
        from apps.buildings.models import UserBuilding
        from apps.buildings.scoping import managed_buildings

        user = getattr(self.context.get("request"), "user", None)
        if not user or not user.is_authenticated:
            return False
        return managed_buildings(user).filter(pk=obj.building_id).exists() or UserBuilding.objects.filter(
            user=user, building_id=obj.building_id
        ).exclude(board_role="").exists()

    def get_work_order(self, obj):
        """What happened to the report: who is doing it, when, and what it cost (visible to everyone who sees the report)."""
        order = getattr(obj, "work_order", None)
        if order is None:
            return None
        return {
            "id": str(order.pk),
            "status": order.status,
            "contractor_id": str(order.contractor_id) if order.contractor_id else None,
            "contractor_name": order.contractor.name if order.contractor else "",
            "scheduled_on": str(order.scheduled_on) if order.scheduled_on else None,
            "completed_on": str(order.completed_on) if order.completed_on else None,
            "notes": order.notes,
            "expense_id": str(order.expense_id) if order.expense_id else None,
            "cost": str(order.expense.amount) if order.expense else None,
        }

    def get_reporter_name(self, obj):
        return obj.reporter.get_full_name() if obj.reporter else ""


class WorkOrderSerializer(serializers.ModelSerializer):
    report_id = serializers.PrimaryKeyRelatedField(source="report", queryset=MaintenanceReport.objects.all())
    contractor_id = serializers.PrimaryKeyRelatedField(source="contractor", queryset=Contractor.objects.all(), required=False, allow_null=True)
    expense_id = serializers.PrimaryKeyRelatedField(source="expense", queryset=Expense.objects.filter(deleted_at__isnull=True), required=False, allow_null=True)

    class Meta:
        model = WorkOrder
        fields = ["id", "report_id", "contractor_id", "scheduled_on", "status", "completed_on", "notes", "expense_id"]
        read_only_fields = ["id"]

    def validate(self, data):
        report = data.get("report") or self.instance.report
        building_id = report.building_id
        contractor, expense = data.get("contractor"), data.get("expense")
        if contractor is not None and contractor.building_id != building_id:
            raise serializers.ValidationError({"contractor_id": "This contractor works for another building."})
        if expense is not None and (expense.building_id != building_id or expense.kind != "cost"):
            raise serializers.ValidationError({"expense_id": "Link a cost recorded for this building."})
        return data
