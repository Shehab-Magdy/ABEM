"""Serializers for the buildings app — Sprint 2."""
import math

from rest_framework import serializers

from apps.authentication.models import User
from .models import Building, UserBuilding


class BuildingSerializer(serializers.ModelSerializer):
    """
    Full CRUD serializer for Building.

    Read:  returns id, tenant_id, name, address, city, country,
           num_floors, num_apartments, num_stores, is_active, created_at, updated_at.
    Write: accepts the same fields; num_apartments and num_stores are persisted
           and trigger auto-creation of vacant Apartment/store records.
    """

    tenant_id = serializers.UUIDField(source="id", read_only=True)
    num_apartments = serializers.IntegerField(
        required=False,
        default=0,
        min_value=0,
        help_text="Number of apartment units in the building.",
    )
    num_stores = serializers.IntegerField(
        required=False,
        default=0,
        min_value=0,
        help_text="Number of store/commercial units in the building.",
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
            "num_stores",
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

    DEFAULT_CATEGORIES = [
        ("Maintenance", "Repairs and upkeep"),
        ("Utilities", "Electricity, water, and gas"),
        ("Cleaning", "Cleaning and janitorial services"),
        ("Security", "Security personnel and systems"),
        ("Management", "Administrative and management fees"),
        ("Other", "Miscellaneous expenses"),
    ]

    def _create_default_categories(self, building):
        """Auto-create default expense categories for a new building."""
        from apps.expenses.models import ExpenseCategory

        categories = [
            ExpenseCategory(building=building, name=name, description=desc)
            for name, desc in self.DEFAULT_CATEGORIES
        ]
        ExpenseCategory.objects.bulk_create(categories, ignore_conflicts=True)

    @staticmethod
    def _apt_floor(i, total_apts, num_floors):
        """Return floor (1-based) for apartment i (1-based), distributed evenly."""
        apts_per_floor = math.ceil(total_apts / num_floors) if num_floors > 0 else total_apts
        return math.ceil(i / apts_per_floor) if apts_per_floor else 1

    def _create_units(self, building):
        """Auto-create vacant apartment and store records for a new building."""
        # Import here to avoid circular-import at module level
        from apps.apartments.models import Apartment

        num_floors = max(building.num_floors, 1)
        units = []
        for i in range(1, building.num_apartments + 1):
            units.append(Apartment(
                building=building,
                unit_number=f"A{i}",
                floor=self._apt_floor(i, building.num_apartments, num_floors),
                unit_type="apartment",
                status="vacant",
            ))
        for i in range(1, building.num_stores + 1):
            units.append(Apartment(
                building=building,
                unit_number=f"S{i}",
                floor=0,  # ground floor for commercial units
                unit_type="store",
                status="vacant",
            ))
        if units:
            Apartment.objects.bulk_create(units)

    def create(self, validated_data):
        building = super().create(validated_data)
        self._create_units(building)
        self._create_default_categories(building)
        return building

    def update(self, instance, validated_data):
        old_apts = instance.num_apartments
        old_stores = instance.num_stores
        building = super().update(instance, validated_data)

        # Auto-create newly added units only (never delete existing ones)
        from apps.apartments.models import Apartment
        new_apts = building.num_apartments - old_apts
        new_stores = building.num_stores - old_stores

        units = []
        num_floors = max(building.num_floors, 1)
        if new_apts > 0:
            existing = set(
                Apartment.objects.filter(building=building, unit_type="apartment")
                .values_list("unit_number", flat=True)
            )
            for i in range(1, building.num_apartments + 1):
                if f"A{i}" not in existing:
                    units.append(Apartment(
                        building=building, unit_number=f"A{i}",
                        floor=self._apt_floor(i, building.num_apartments, num_floors),
                        unit_type="apartment", status="vacant",
                    ))
        if new_stores > 0:
            existing = set(
                Apartment.objects.filter(building=building, unit_type="store")
                .values_list("unit_number", flat=True)
            )
            for i in range(1, building.num_stores + 1):
                if f"S{i}" not in existing:
                    units.append(Apartment(
                        building=building, unit_number=f"S{i}",
                        floor=0, unit_type="store", status="vacant",
                    ))
        if units:
            Apartment.objects.bulk_create(units)
        return building


class AssignUserSerializer(serializers.Serializer):
    """Validates the payload for POST /buildings/{id}/assign-user/."""

    user_id = serializers.UUIDField()

    def validate_user_id(self, value):
        try:
            user = User.objects.get(pk=value, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        return value
