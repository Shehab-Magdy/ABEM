"""Expense serializers – Sprint 3."""
from __future__ import annotations

from rest_framework import serializers

from apps.buildings.models import Building

from .models import (
    ApartmentExpense,
    Expense,
    ExpenseCategory,
    MediaFile,
    RecurringConfig,
    RecurringFrequency,
    SplitType,
)


# ── Category ───────────────────────────────────────────────────────────────────

class ExpenseCategorySerializer(serializers.ModelSerializer):
    building_id = serializers.PrimaryKeyRelatedField(
        source="building",
        queryset=Building.objects.filter(is_active=True, deleted_at__isnull=True),
    )
    parent_id = serializers.PrimaryKeyRelatedField(
        source="parent",
        queryset=ExpenseCategory.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = ExpenseCategory
        fields = ["id", "building_id", "name", "description", "icon", "color", "parent_id", "is_active", "created_at"]
        read_only_fields = ["id", "is_active", "created_at"]


# ── Nested read-only serializers ───────────────────────────────────────────────

class ApartmentExpenseSerializer(serializers.ModelSerializer):
    """Read-only share row returned inside expense detail."""
    apartment_id = serializers.UUIDField(source="apartment.id", read_only=True)
    unit_number = serializers.CharField(source="apartment.unit_number", read_only=True)

    class Meta:
        model = ApartmentExpense
        fields = ["id", "apartment_id", "unit_number", "share_amount"]


class RecurringConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurringConfig
        fields = ["id", "frequency", "next_due", "is_active"]
        read_only_fields = ["id"]


class MediaFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaFile
        fields = ["id", "url", "mime_type", "file_size_bytes", "created_at"]
        read_only_fields = ["id", "url", "mime_type", "file_size_bytes", "created_at"]


# ── Expense ────────────────────────────────────────────────────────────────────

class ExpenseSerializer(serializers.ModelSerializer):
    building_id = serializers.PrimaryKeyRelatedField(
        source="building",
        queryset=Building.objects.filter(is_active=True, deleted_at__isnull=True),
    )
    category_id = serializers.PrimaryKeyRelatedField(
        source="category",
        queryset=ExpenseCategory.objects.filter(is_active=True),
    )

    # Read-only nested data returned on retrieve / list
    apartment_shares = ApartmentExpenseSerializer(
        source="apartment_expenses", many=True, read_only=True
    )
    recurring_config = RecurringConfigSerializer(read_only=True)
    attachments = serializers.SerializerMethodField()

    # Write-only: frequency for creating the recurring config
    frequency = serializers.ChoiceField(
        choices=RecurringFrequency.choices,
        write_only=True,
        required=False,
        allow_null=True,
        default=None,
    )

    # Write-only: apartment UUIDs for CUSTOM split type
    custom_split_apartments = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        default=list,
    )

    class Meta:
        model = Expense
        fields = [
            "id",
            "building_id",
            "category_id",
            "title",
            "description",
            "amount",
            "expense_date",
            "due_date",
            "split_type",
            "is_recurring",
            "frequency",
            "custom_split_apartments",
            "apartment_shares",
            "recurring_config",
            "attachments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    # ── Field-level validation ─────────────────────────────────────────────────

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("amount must be greater than 0.")
        return value

    # ── Object-level validation ────────────────────────────────────────────────

    def validate(self, data):
        is_recurring = data.get("is_recurring", getattr(self.instance, "is_recurring", False))
        frequency = data.get("frequency")
        if is_recurring and not frequency:
            raise serializers.ValidationError(
                {"frequency": "frequency is required when is_recurring is true."}
            )
        return data

    # ── Helpers ────────────────────────────────────────────────────────────────

    def get_attachments(self, obj):
        files = MediaFile.objects.filter(entity_type="expense", entity_id=obj.pk)
        return MediaFileSerializer(files, many=True).data

    # ── Write ──────────────────────────────────────────────────────────────────

    def create(self, validated_data):
        from .utils import run_split_engine

        frequency = validated_data.pop("frequency", None)
        custom_apartment_ids = validated_data.pop("custom_split_apartments", [])

        expense = super().create(validated_data)

        if expense.is_recurring and frequency:
            _create_recurring_config(expense, frequency)

        run_split_engine(expense, custom_apartment_ids)
        return expense

    def update(self, instance, validated_data):
        from .utils import run_split_engine

        frequency = validated_data.pop("frequency", None)
        custom_apartment_ids = validated_data.pop("custom_split_apartments", [])

        expense = super().update(instance, validated_data)

        # Re-calculate shares after any field change
        expense.apartment_expenses.all().delete()
        run_split_engine(expense, custom_apartment_ids)

        # Update or create recurring config if frequency is provided
        if frequency:
            if hasattr(expense, "recurring_config"):
                expense.recurring_config.frequency = frequency
                expense.recurring_config.save(update_fields=["frequency"])
            elif expense.is_recurring:
                _create_recurring_config(expense, frequency)

        return expense


# ── Private helpers ────────────────────────────────────────────────────────────

def _create_recurring_config(expense: Expense, frequency: str) -> RecurringConfig:
    from dateutil.relativedelta import relativedelta

    base = expense.expense_date
    if frequency == RecurringFrequency.MONTHLY:
        next_due = base + relativedelta(months=1)
    elif frequency == RecurringFrequency.QUARTERLY:
        next_due = base + relativedelta(months=3)
    else:  # annual
        next_due = base + relativedelta(years=1)

    return RecurringConfig.objects.create(
        expense=expense,
        frequency=frequency,
        next_due=next_due,
    )
