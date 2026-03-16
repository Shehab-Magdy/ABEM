"""Payment serializers – Sprint 4."""
from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.apartments.models import Apartment
from apps.buildings.models import Building
from apps.expenses.models import ApartmentExpense, Expense

from .models import AssetSale, BuildingAsset, Payment


class AssetSaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetSale
        fields = ["id", "sale_date", "sale_price", "buyer_name", "buyer_contact", "notes", "created_at"]
        read_only_fields = ["id", "created_at"]


class BuildingAssetSerializer(serializers.ModelSerializer):
    building_id = serializers.PrimaryKeyRelatedField(
        source="building",
        queryset=Building.objects.filter(is_active=True, deleted_at__isnull=True),
    )
    sale = AssetSaleSerializer(read_only=True)

    class Meta:
        model = BuildingAsset
        fields = [
            "id", "building_id", "name", "description", "asset_type",
            "acquisition_date", "acquisition_value",
            "is_sold", "sale", "created_at",
        ]
        read_only_fields = ["id", "is_sold", "created_at"]


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for recording and listing payments.

    Write fields:  apartment_id, expense_ids (optional list), amount_paid,
                   payment_method, payment_date, notes.
    Read-only:     id, balance_before, balance_after, remaining_balance,
                   recorded_by, created_at.
    """

    apartment_id = serializers.PrimaryKeyRelatedField(
        source="apartment",
        queryset=Apartment.objects.all(),
    )
    expense_ids = serializers.PrimaryKeyRelatedField(
        source="expenses",
        queryset=Expense.objects.filter(deleted_at__isnull=True),
        many=True,
        required=False,
    )

    # Alias balance_after as remaining_balance for the API response
    remaining_balance = serializers.DecimalField(
        source="balance_after",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )

    recorded_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "apartment_id",
            "expense_ids",
            "amount_paid",
            "payment_method",
            "payment_date",
            "notes",
            "balance_before",
            "balance_after",
            "remaining_balance",
            "recorded_by",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "balance_before",
            "balance_after",
            "remaining_balance",
            "recorded_by",
            "created_at",
        ]

    # ── Field-level validation ──────────────────────────────────────────────────

    def validate_amount_paid(self, value: Decimal) -> Decimal:
        if value <= Decimal("0.00"):
            raise serializers.ValidationError("amount_paid must be greater than zero.")
        return value

    # ── Cross-field validation ──────────────────────────────────────────────────

    def validate(self, data: dict) -> dict:
        expenses = data.get("expenses", [])
        apartment = data.get("apartment")

        if expenses and apartment:
            for expense in expenses:
                assigned = ApartmentExpense.objects.filter(
                    expense=expense, apartment=apartment
                ).exists()
                if not assigned:
                    raise serializers.ValidationError(
                        f"Expense '{expense.title}' has not been assigned to the specified apartment."
                    )

        return data
