"""Payment serializers – Sprint 4."""
from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.apartments.models import Apartment
from apps.expenses.models import ApartmentExpense, Expense

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for recording and listing payments.

    Write fields:  apartment_id, expense_id (optional), amount_paid,
                   payment_method, payment_date, notes.
    Read-only:     id, balance_before, balance_after, remaining_balance,
                   recorded_by, created_at.
    """

    apartment_id = serializers.PrimaryKeyRelatedField(
        source="apartment",
        queryset=Apartment.objects.all(),
    )
    expense_id = serializers.PrimaryKeyRelatedField(
        source="expense",
        queryset=Expense.objects.filter(deleted_at__isnull=True),
        allow_null=True,
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
            "expense_id",
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
        expense = data.get("expense")
        apartment = data.get("apartment")

        if expense and apartment:
            assigned = ApartmentExpense.objects.filter(
                expense=expense, apartment=apartment
            ).exists()
            if not assigned:
                raise serializers.ValidationError(
                    "This expense has not been assigned to the specified apartment."
                )

        return data
