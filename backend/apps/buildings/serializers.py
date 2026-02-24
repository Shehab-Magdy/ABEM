"""Serializers for the buildings app — Sprint 2."""
from rest_framework import serializers

from apps.authentication.models import User
from .models import Building, UserBuilding


class BuildingSerializer(serializers.ModelSerializer):
    """
    Full CRUD serializer for Building.

    Read:  returns id, tenant_id (= id), name, address, city, country,
           num_floors, is_active, created_at, updated_at.
    Write: accepts name, address, city, country, num_floors,
           and optional num_apartments (validated >= 0, not persisted).
    """

    # tenant_id mirrors the building UUID (each building is its own tenant)
    tenant_id = serializers.UUIDField(source="id", read_only=True)
    # num_apartments: request-only hint; validated but not stored in Building
    num_apartments = serializers.IntegerField(
        write_only=True,
        required=False,
        default=0,
        min_value=0,
        help_text="Non-negative count of apartments. Validated but not persisted.",
    )

    class Meta:
        model = Building
        fields = [
            "id",
            "tenant_id",
            "name",
            "address",
            "city",
            "country",
            "num_floors",
            "num_apartments",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "tenant_id", "is_active", "created_at", "updated_at"]

    def validate_num_floors(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "num_floors must be a positive integer greater than 0."
            )
        return value

    def create(self, validated_data):
        validated_data.pop("num_apartments", None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop("num_apartments", None)
        return super().update(instance, validated_data)


class AssignUserSerializer(serializers.Serializer):
    """Validates the payload for POST /buildings/{id}/assign-user/."""

    user_id = serializers.UUIDField()

    def validate_user_id(self, value):
        try:
            user = User.objects.get(pk=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        if user.role != "owner":
            raise serializers.ValidationError(
                "Only users with the 'owner' role can be assigned to a building."
            )
        return value
