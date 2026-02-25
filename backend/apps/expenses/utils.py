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


def run_split_engine(expense, custom_apartment_ids: list | None = None) -> None:
    """Create ApartmentExpense records for a given expense.

    Determines which apartments receive a share based on ``expense.split_type``,
    calculates raw per-unit share, rounds it UP to the nearest 5, then bulk-inserts
    ApartmentExpense rows.

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
    elif expense.split_type == SplitType.CUSTOM and custom_apartment_ids:
        qs = qs.filter(pk__in=[str(aid) for aid in custom_apartment_ids])

    apartments = list(qs)
    if not apartments:
        return

    raw_share = expense.amount / Decimal(len(apartments))
    share_amount = round_up_to_nearest_5(raw_share)

    ApartmentExpense.objects.bulk_create(
        [
            ApartmentExpense(
                apartment=apt,
                expense=expense,
                share_amount=share_amount,
            )
            for apt in apartments
        ]
    )
