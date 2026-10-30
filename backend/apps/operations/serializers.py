from rest_framework import serializers

from apps.buildings.models import Building

from .models import Contractor, Obligation


class ContractorSerializer(serializers.ModelSerializer):
    building_id = serializers.PrimaryKeyRelatedField(source="building", queryset=Building.objects.all())

    class Meta:
        model = Contractor
        fields = ["id", "building_id", "name", "trade", "phone", "notes", "contract_start", "contract_end", "is_active"]
        read_only_fields = ["id"]


class ObligationSerializer(serializers.ModelSerializer):
    building_id = serializers.PrimaryKeyRelatedField(source="building", queryset=Building.objects.all())
    contractor_id = serializers.PrimaryKeyRelatedField(source="contractor", queryset=Contractor.objects.all(), required=False, allow_null=True)
    contractor_name = serializers.CharField(source="contractor.name", read_only=True, default="")

    class Meta:
        model = Obligation
        fields = [
            "id", "building_id", "title", "due_date", "repeat", "contractor_id", "contractor_name", "notes",
            "remind_days", "is_active", "last_done_on",
        ]
        read_only_fields = ["id", "last_done_on"]

    def validate(self, data):
        building = data.get("building") or getattr(self.instance, "building", None)
        contractor = data.get("contractor")
        if contractor is not None and building is not None and contractor.building_id != building.pk:
            raise serializers.ValidationError({"contractor_id": "This contractor works for another building."})
        return data
