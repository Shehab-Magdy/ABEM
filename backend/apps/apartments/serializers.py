"""Serializers for the apartments app — Sprint 2."""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.buildings.models import Building
from apps.authentication.models import User
from .models import Apartment, UnitClaimRequest, UnitType


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
        # queryset=Building.objects.filter(is_active=True, deleted_at__isnull=True),
        queryset=Building.objects.filter(is_active=True),
    )
    owner_id = serializers.PrimaryKeyRelatedField(
        source="owner",
        queryset=User.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    owner_ids = serializers.PrimaryKeyRelatedField(
        source="owners",
        queryset=User.objects.filter(is_active=True),
        many=True,
        required=False,
    )
    owner_names = serializers.SerializerMethodField(read_only=True)
    renters = serializers.SerializerMethodField(read_only=True)

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
            "owner_ids",
            "owner_names",
            "renters",
            "billing_paused",
            "billing_pause_reason",
            "unit_number",
            "floor",
            "type",
            "size_sqm",
            "status",
            "balance",
        ]
        read_only_fields = ["id", "balance"]

    def get_owner_names(self, obj):
        return [o.get_full_name() or o.email for o in obj.owners.all() if o.role != "renter"]

    def validate(self, data):
        """Cross-field: floor must not exceed the building's num_floors."""
        building = data.get("building", getattr(self.instance, "building", None))
        floor = data.get("floor", getattr(self.instance, "floor", None))

        if building is not None and floor is not None:
            if floor > building.num_floors:
                raise serializers.ValidationError(
                    {
                        "floor": _("Floor %(floor)s exceeds the building's maximum "
                                    "of %(num_floors)s floor(s).") % {
                            "floor": floor,
                            "num_floors": building.num_floors
                        }
                    }
                )
        return data

    def get_renters(self, obj):
        return [
            {"id": str(u.pk), "name": u.get_full_name() or u.email}
            for u in obj.owners.filter(role="renter")
        ]


class UnitClaimRequestSerializer(serializers.ModelSerializer):
    unit_number = serializers.CharField(source="apartment.unit_number", read_only=True)
    building_name = serializers.CharField(source="apartment.building.name", read_only=True)
    user_name = serializers.SerializerMethodField()
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = UnitClaimRequest
        fields = ["id", "unit_number", "building_name", "user_name", "user_email", "status", "created_at"]
        read_only_fields = fields

    def get_user_name(self, obj):
        return obj.user.get_full_name()
