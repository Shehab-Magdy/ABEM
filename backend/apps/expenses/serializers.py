"""Expense serializers – Sprint 3."""
from __future__ import annotations

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

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
    payment_status = serializers.SerializerMethodField()
    total_paid = serializers.SerializerMethodField()

    class Meta:
        model = ApartmentExpense
        fields = ["id", "apartment_id", "unit_number", "share_amount", "payment_status", "total_paid"]

    def get_total_paid(self, obj):
        """Sum of payments linked to this expense for this apartment."""
        from apps.payments.models import Payment
        from django.db.models import Sum
        result = Payment.objects.filter(
            apartment_id=obj.apartment_id,
            expenses=obj.expense,
        ).aggregate(total=Sum("amount_paid"))
        return str(result["total"] or 0)

    def get_payment_status(self, obj):
        """
        Derived payment status for this apartment's share of the expense.
        - "paid"    if is_manually_paid or cumulative payments >= share_amount
        - "partial" if cumulative payments > 0 but < share_amount
        - "unpaid"  if no payments
        """
        if obj.expense.is_manually_paid:
            return "paid"
        from apps.payments.models import Payment
        from django.db.models import Sum
        from decimal import Decimal
        result = Payment.objects.filter(
            apartment_id=obj.apartment_id,
            expenses=obj.expense,
        ).aggregate(total=Sum("amount_paid"))
        total_paid = result["total"] or Decimal("0.00")
        if total_paid >= obj.share_amount:
            return "paid"
        elif total_paid > Decimal("0.00"):
            return "partial"
        return "unpaid"


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

    # The requesting user's per-unit share; None when the user is admin
    my_share_amount = serializers.SerializerMethodField()

    # The requesting user's derived payment status; None when the user is admin
    my_payment_status = serializers.SerializerMethodField()

    # Write-only: frequency for creating the recurring config
    frequency = serializers.ChoiceField(
        choices=RecurringFrequency.choices,
        write_only=True,
        required=False,
        allow_null=True,
        default=None,
    )

    # Write-only: apartment UUIDs for CUSTOM split type (equal shares within subset)
    custom_split_apartments = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        default=list,
    )

    # Write-only: {apartment_id: weight} for weighted CUSTOM split
    # weight 1.0 = full share, 0.5 = half share, etc.
    custom_split_weights = serializers.DictField(
        child=serializers.DecimalField(max_digits=6, decimal_places=4, min_value=0),
        write_only=True,
        required=False,
        default=dict,
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
            "custom_split_weights",
            "apartment_shares",
            "recurring_config",
            "attachments",
            "my_share_amount",
            "my_payment_status",
            "is_manually_paid",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    # ── Field-level validation ─────────────────────────────────────────────────

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(_("amount must be greater than 0."))
        return value

    # ── Object-level validation ────────────────────────────────────────────────

    def validate(self, data):
        is_recurring = data.get("is_recurring", getattr(self.instance, "is_recurring", False))
        frequency = data.get("frequency")
        if is_recurring and not frequency:
            raise serializers.ValidationError(
                {"frequency": _("frequency is required when is_recurring is true.")}
            )
        return data

    # ── Helpers ────────────────────────────────────────────────────────────────

    def get_attachments(self, obj):
        files = MediaFile.objects.filter(entity_type="expense", entity_id=obj.pk)
        return MediaFileSerializer(files, many=True).data

    def get_my_share_amount(self, obj):
        request = self.context.get("request")
        if not request or request.user.role == "admin":
            return None
        share = obj.apartment_expenses.filter(
            apartment__owners=request.user
        ).first()
        if share is None:
            share = obj.apartment_expenses.filter(
                apartment__owner=request.user
            ).first()
        return str(share.share_amount) if share else None

    def get_my_payment_status(self, obj):
        """
        Derived payment status for the requesting owner's share.
        Returns None for admin users.
        When is_manually_paid is True, always returns "paid".
        """
        if obj.is_manually_paid:
            return "paid"
        request = self.context.get("request")
        if not request or request.user.role == "admin":
            return None
        share = obj.apartment_expenses.filter(
            apartment__owners=request.user
        ).first()
        if share is None:
            share = obj.apartment_expenses.filter(
                apartment__owner=request.user
            ).first()
        if share is None:
            return None

        from apps.payments.models import Payment
        from django.db.models import Sum
        from decimal import Decimal
        result = Payment.objects.filter(
            apartment_id=share.apartment_id,
            expenses=obj,
        ).aggregate(total=Sum("amount_paid"))
        total_paid = result["total"] or Decimal("0.00")
        if total_paid >= share.share_amount:
            return "paid"
        elif total_paid > Decimal("0.00"):
            return "partial"
        return "unpaid"

    # ── Write ──────────────────────────────────────────────────────────────────

    def create(self, validated_data):
        from .utils import run_split_engine

        frequency = validated_data.pop("frequency", None)
        custom_apartment_ids = validated_data.pop("custom_split_apartments", [])
        custom_weights = validated_data.pop("custom_split_weights", {})

        expense = super().create(validated_data)

        if expense.is_recurring and frequency:
            _create_recurring_config(expense, frequency)

        run_split_engine(expense, custom_apartment_ids, custom_weights or None)
        return expense

    def update(self, instance, validated_data):
        from .utils import run_split_engine
        from apps.apartments.models import Apartment
        from django.db.models import F

        frequency = validated_data.pop("frequency", None)
        custom_apartment_ids = validated_data.pop("custom_split_apartments", [])
        custom_weights = validated_data.pop("custom_split_weights", {})

        # Reverse the balance increments from the previous split before recalculating
        for ae in instance.apartment_expenses.all():
            Apartment.objects.filter(pk=ae.apartment_id).update(
                balance=F("balance") - ae.share_amount
            )
        instance.apartment_expenses.all().delete()

        expense = super().update(instance, validated_data)

        # Re-calculate shares after any field change
        run_split_engine(expense, custom_apartment_ids, custom_weights or None)

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
