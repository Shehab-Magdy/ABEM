"""Late fees on overdue subscription shares, and waiving them."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.apartments.models import Apartment
from apps.audit.mixins import log_job_run

from .models import ApartmentExpense, Expense, ExpenseCategory, ExpenseKind, LateFee, SplitType
from .utils import paid_toward_expense

CATEGORY_NAME = "غرامات التأخير"


def _fee_amount(plan, remaining: Decimal) -> Decimal:
    if plan.late_fee_type == "fixed":
        return plan.late_fee_value.quantize(Decimal("0.01"))
    return (remaining * plan.late_fee_value / Decimal("100")).quantize(Decimal("0.01"))


def apply_late_fees(today: date | None = None) -> int:
    """Add one late fee to each subscription share still unpaid after its due date + grace days.

    Returns how many fees were created. A share is charged at most once, however often this runs.
    """
    from apps.plans.services import billing_allowed

    today = today or timezone.localdate()
    created = 0
    runs: dict = {}
    shares = (
        ApartmentExpense.objects.filter(
            expense__kind=ExpenseKind.SUBSCRIPTION,
            expense__deleted_at__isnull=True,
            expense__subscription_run__plan__is_active=True,
            expense__subscription_run__plan__late_fee_type__in=["fixed", "percent"],
            expense__due_date__lt=today,
            late_fee__isnull=True,
        )
        .select_related("expense__subscription_run__plan", "apartment__building")
    )
    for share in shares:
        plan = share.expense.subscription_run.plan
        if not billing_allowed(plan.building, today):
            continue
        if share.expense.due_date + timedelta(days=plan.grace_days) >= today:
            continue
        remaining = share.share_amount - paid_toward_expense(share.expense, share.apartment_id)
        if remaining <= 0:
            continue
        fee = _fee_amount(plan, remaining)
        if fee <= 0:
            continue
        with transaction.atomic():
            category, _ = ExpenseCategory.objects.get_or_create(building=plan.building, name=CATEGORY_NAME)
            charge = Expense.objects.create(
                building=plan.building, category=category, title=f"{CATEGORY_NAME} — {share.expense.title}",
                amount=fee, expense_date=today, due_date=today, kind=ExpenseKind.LATE_FEE,
                split_type=SplitType.CUSTOM, created_by=plan.building.admin,
            )
            ApartmentExpense.objects.create(apartment=share.apartment, expense=charge, share_amount=fee)
            Apartment.objects.filter(pk=share.apartment_id).update(balance=F("balance") + fee)
            LateFee.objects.create(share=share, expense=charge)
        created += 1
        run = runs.setdefault(plan.building_id, {"created": 0, "total": Decimal("0.00")})
        run["created"] += 1
        run["total"] += fee
    log_job_run("apply_late_fees", {b: {**r, "total": str(r["total"])} for b, r in runs.items()})
    return created


def waive_late_fee(fee: LateFee, user, reason: str = "") -> LateFee:
    """Take a late fee back off the unit: reverse the balance, hide the charge, record who and why."""
    with transaction.atomic():
        fee = LateFee.objects.select_for_update().get(pk=fee.pk)
        if fee.waived_at:
            return fee
        for share in fee.expense.apartment_expenses.all():
            Apartment.objects.filter(pk=share.apartment_id).update(balance=F("balance") - share.share_amount)
        fee.expense.apartment_expenses.all().delete()
        fee.expense.deleted_at = timezone.now()
        fee.expense.save(update_fields=["deleted_at"])
        fee.waived_at, fee.waived_by, fee.waived_reason = timezone.now(), user, reason[:200]
        fee.save()
    return fee
