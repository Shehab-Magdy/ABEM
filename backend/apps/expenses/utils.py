"""Expense split engine utilities – Sprint 3."""
from __future__ import annotations

import math
from decimal import Decimal


def round_up_to_nearest_5(amount: Decimal) -> Decimal:
    """Round a Decimal amount UP to the nearest 5 currency units.

    Examples:
        25.00 → 25.00  (already a multiple of 5)
        25.01 → 30.00
        25.25 → 30.00  (101.00 / 4 apartments)
        34.33 → 35.00  (103.00 / 3 apartments)
    """
    return Decimal(str(math.ceil(float(amount) / 5) * 5))


def run_split_engine(
    expense,
    custom_apartment_ids: list | None = None,
    custom_weights: dict | None = None,
) -> None:
    """Create ApartmentExpense records for a given expense.

    Determines which apartments receive a share based on ``expense.split_type``,
    calculates raw per-unit share, rounds it UP to the nearest 5, then bulk-inserts
    ApartmentExpense rows.

    For CUSTOM split with ``custom_weights`` provided (dict of {apt_id: weight}),
    shares are allocated proportionally: share_i = (weight_i / total_weight) * amount.
    A weight of 1.0 is a full share, 0.5 is half a share, etc.

    This function is idempotent only if existing rows are deleted before calling it
    on an update.  On create, it assumes no rows exist yet.
    """
    from apps.apartments.models import Apartment, UnitType
    from .models import ApartmentExpense, SplitType

    qs = Apartment.objects.filter(building=expense.building)

    if expense.split_type == SplitType.EQUAL_APARTMENTS:
        qs = qs.filter(unit_type=UnitType.APARTMENT)
    elif expense.split_type == SplitType.EQUAL_STORES:
        qs = qs.filter(unit_type=UnitType.STORE)
    elif expense.split_type == SplitType.CUSTOM:
        ids = list(custom_weights.keys()) if custom_weights else (custom_apartment_ids or [])
        if ids:
            qs = qs.filter(pk__in=[str(i) for i in ids])

    apartments = list(qs)
    if not apartments:
        return

    # Build per-apartment share amounts
    if expense.split_type == SplitType.CUSTOM and custom_weights:
        total_weight = sum(
            Decimal(str(custom_weights.get(str(apt.pk), 1))) for apt in apartments
        )
        if total_weight == 0:
            total_weight = Decimal(len(apartments))
        shares = {
            apt.pk: round_up_to_nearest_5(
                expense.amount * Decimal(str(custom_weights.get(str(apt.pk), 1))) / total_weight
            )
            for apt in apartments
        }
    else:
        equal_share = round_up_to_nearest_5(expense.amount / Decimal(len(apartments)))
        shares = {apt.pk: equal_share for apt in apartments}

    ApartmentExpense.objects.bulk_create(
        [
            ApartmentExpense(
                apartment=apt,
                expense=expense,
                share_amount=shares[apt.pk],
            )
            for apt in apartments
        ]
    )

    # Increment each apartment's running balance (positive = owes more)
    from django.db.models import F
    for apt in apartments:
        Apartment.objects.filter(pk=apt.pk).update(balance=F("balance") + shares[apt.pk])
