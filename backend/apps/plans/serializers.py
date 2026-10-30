from rest_framework import serializers

from apps.buildings.models import Building

from .models import FEATURES, Plan, PlanPayment


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            "code", "name_ar", "name_en", "price_monthly", "price_yearly",
            "max_units", "features", "is_active", "sort_order",
        ]

    def validate_features(self, value):
        unknown = [f for f in value if f not in FEATURES]
        if unknown:
            raise serializers.ValidationError(f"Unknown features: {', '.join(unknown)}")
        return value

    def validate(self, data):
        for field in ("price_monthly", "price_yearly"):
            if data.get(field) is not None and data[field] < 0:
                raise serializers.ValidationError({field: "Price cannot be negative."})
        return data


class PlanPaymentSerializer(serializers.ModelSerializer):
    building_name = serializers.CharField(source="building.name", read_only=True)
    plan_name = serializers.SerializerMethodField()
    building_id = serializers.PrimaryKeyRelatedField(source="building", queryset=Building.objects.filter(deleted_at__isnull=True))
    plan_code = serializers.PrimaryKeyRelatedField(source="plan", queryset=Plan.objects.filter(is_active=True))

    class Meta:
        model = PlanPayment
        fields = [
            "id", "building_id", "building_name", "plan_code", "plan_name", "period",
            "amount", "reference", "status", "created_at", "reviewed_at",
        ]
        read_only_fields = ["id", "amount", "status", "created_at", "reviewed_at"]

    def get_plan_name(self, obj):
        return {"ar": obj.plan.name_ar, "en": obj.plan.name_en}
