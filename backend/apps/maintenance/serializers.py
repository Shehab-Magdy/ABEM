from rest_framework import serializers

from apps.buildings.models import Building

from .models import MaintenanceReport


class MaintenanceReportSerializer(serializers.ModelSerializer):
    building_id = serializers.PrimaryKeyRelatedField(source="building", queryset=Building.objects.all())
    building_name = serializers.CharField(source="building.name", read_only=True)
    reporter_name = serializers.SerializerMethodField()

    class Meta:
        model = MaintenanceReport
        fields = [
            "id", "building_id", "building_name", "category", "description",
            "status", "reporter_name", "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]

    def get_reporter_name(self, obj):
        return obj.reporter.get_full_name() if obj.reporter else ""
