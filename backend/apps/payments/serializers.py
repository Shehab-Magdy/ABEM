"""Payment serializers – Sprint 4 + NF-02 (manual allocation)."""
from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.apartments.models import Apartment
from apps.buildings.models import Building
from apps.expenses.models import ApartmentExpense, Expense

from .models import AssetSale, BuildingAsset, Payment, PaymentExpense


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


class PaymentExpenseReadSerializer(serializers.ModelSerializer):
    """Read-only representation of a payment-expense allocation."""
    expense_id = serializers.UUIDField(source="expense.id", read_only=True)
    expense_title = serializers.CharField(source="expense.title", read_only=True)

    class Meta:
        model = PaymentExpense
        fields = ["expense_id", "expense_title", "allocated_amount"]


class AllocationInputSerializer(serializers.Serializer):
    """One item in the ``allocations`` list when recording a payment."""
    expense_id = serializers.PrimaryKeyRelatedField(
        queryset=Expense.objects.filter(deleted_at__isnull=True),
    )
    allocated_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True,
    )

    def validate_allocated_amount(self, value):
        if value is not None and value < Decimal("0.00"):
            raise serializers.ValidationError(_("Allocated amount cannot be negative."))
        return value


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for recording and listing payments.

    Write fields:  apartment_id, expense_ids (optional list), amount_paid,
                   payment_method, payment_date, notes, allocations (optional).
    Read-only:     id, balance_before, balance_after, remaining_balance,
                   recorded_by, created_at, allocations (on read).
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

    # Manual allocation list (write-only input)
    allocations = AllocationInputSerializer(many=True, required=False, write_only=True)

    # Read-only allocation details returned on GET
    allocation_details = PaymentExpenseReadSerializer(
        source="payment_expenses", many=True, read_only=True,
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
            "allocations",
            "allocation_details",
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
            raise serializers.ValidationError(_("amount_paid must be greater than zero."))
        return value

    # ── Cross-field validation ──────────────────────────────────────────────────

    def validate(self, data: dict) -> dict:
        expenses = data.get("expenses", [])
        apartment = data.get("apartment")
        allocations = self.initial_data.get("allocations", [])

        if expenses and apartment:
            for expense in expenses:
                assigned = ApartmentExpense.objects.filter(
                    expense=expense, apartment=apartment
                ).exists()
                if not assigned:
                    raise serializers.ValidationError(
                        _(
                            "Expense '%(title)s' has not been assigned to the specified apartment."
                        ) % {"title": expense.title}
                    )

        # Validate allocations against amount_paid
        if allocations:
            amount_paid = data.get("amount_paid", Decimal("0.00"))
            total_allocated = Decimal("0.00")
            for alloc in allocations:
                amt = alloc.get("allocated_amount")
                if amt is not None:
                    total_allocated += Decimal(str(amt))
            if total_allocated > amount_paid:
                raise serializers.ValidationError(
                    _("Total allocated (%(sum)s) cannot exceed amount paid (%(amount)s).") % {
                        "sum": str(total_allocated),
                        "amount": str(amount_paid),
                    }
                )

        return data

    # ── Create override (explicit through table needs manual M2M handling) ────

    def create(self, validated_data):
        """Pop expenses before creating Payment, then create PaymentExpense rows."""
        expenses = validated_data.pop("expenses", [])
        # Remove allocations from validated_data (handled by the view's perform_create)
        validated_data.pop("allocations", None)
        payment = Payment.objects.create(**validated_data)
        # Create through-table rows for linked expenses (without allocation;
        # allocations are set by the view after save if provided).
        for expense in expenses:
            PaymentExpense.objects.get_or_create(payment=payment, expense=expense)
        return payment
