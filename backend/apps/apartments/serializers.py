"""Serializers for the apartments app — Sprint 2."""
from rest_framework import serializers

from apps.buildings.models import Building
from apps.authentication.models import User
from .models import Apartment, UnitType


class ApartmentSerializer(serializers.ModelSerializer):
    """
    Full CRUD serializer for Apartment.

    API field naming follows the SRS contract:
      - `type`     → model field `unit_type`
      - `size_sqm` → model field `size_sqm` (also accepted as write param)
      - `building_id` → FK to Building
      - `owner_id`    → FK to User (nullable)

    Floor is validated against the parent building's num_floors.
    Balance is read-only (always initialised to 0.00 on creation).
    """

    # Expose FK IDs directly instead of nested objects
    building_id = serializers.PrimaryKeyRelatedField(
        source="building",
        queryset=Building.objects.filter(is_active=True, deleted_at__isnull=True),
    )
    owner_id = serializers.PrimaryKeyRelatedField(
        source="owner",
        queryset=User.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )

    # Map `type` in the API to `unit_type` in the model
    type = serializers.ChoiceField(
        source="unit_type",
        choices=UnitType.choices,
    )

    class Meta:
        model = Apartment
        fields = [
            "id",
            "building_id",
            "owner_id",
            "unit_number",
            "floor",
            "type",
            "size_sqm",
            "status",
            "balance",
        ]
        read_only_fields = ["id", "balance"]

    def validate(self, data):
        """Cross-field: floor must not exceed the building's num_floors."""
        building = data.get("building", getattr(self.instance, "building", None))
        floor = data.get("floor", getattr(self.instance, "floor", None))

        if building is not None and floor is not None:
            if floor > building.num_floors:
                raise serializers.ValidationError(
                    {
                        "floor": (
                            f"Floor {floor} exceeds the building's maximum "
                            f"of {building.num_floors} floor(s)."
                        )
                    }
                )
        return data
