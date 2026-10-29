"""Splitting a payment across the expenses an apartment owes."""
from decimal import Decimal, InvalidOperation

from django.utils.translation import gettext_lazy as _

from apps.expenses.models import ApartmentExpense
from apps.expenses.utils import paid_toward_expense

from .models import PaymentExpense

ZERO = Decimal("0.00")


class AllocationError(ValueError):
    """The requested allocation is not valid for this apartment."""


def unpaid_shares(apartment, only_expense_ids=None):
    """[(expense, remaining)] this apartment still owes, oldest expense first."""
    shares = (
        ApartmentExpense.objects.filter(
            apartment=apartment, expense__deleted_at__isnull=True, expense__is_manually_paid=False
        )
        .select_related("expense")
        .order_by("expense__expense_date", "expense__created_at")
    )
    if only_expense_ids:
        shares = shares.filter(expense_id__in=only_expense_ids)
    rows = []
    for share in shares:
        remaining = share.share_amount - paid_toward_expense(share.expense, apartment.pk)
        if remaining > ZERO:
            rows.append((share.expense, remaining))
    return rows


def auto_allocate(apartment, amount, only_expense_ids=None):
    """Oldest-first: fill each unpaid share in turn. Any leftover stays as credit on the balance."""
    left, rows = amount, []
    for expense, remaining in unpaid_shares(apartment, only_expense_ids):
        if left <= ZERO:
            break
        part = min(left, remaining)
        rows.append((expense, part))
        left -= part
    return rows


def check_manual(apartment, amount, raw_rows):
    """Validate [{"expense_id", "allocated_amount"}] given by the admin -> [(expense, amount)]."""
    owed = {str(expense.pk): (expense, remaining) for expense, remaining in unpaid_shares(apartment)}
    seen, rows, total = set(), [], ZERO
    for raw in raw_rows:
        expense_id = str(raw.get("expense_id"))
        if expense_id in seen:
            raise AllocationError(_("Each expense can appear only once."))
        seen.add(expense_id)
        if expense_id not in owed:
            raise AllocationError(_("An allocated expense is not owed by this apartment (or is already paid)."))
        try:
            value = Decimal(str(raw.get("allocated_amount")))
        except (InvalidOperation, TypeError):
            raise AllocationError(_("Each allocation needs a valid amount."))
        expense, remaining = owed[expense_id]
        if value < ZERO:
            raise AllocationError(_("Allocated amount cannot be negative."))
        if value > remaining:
            raise AllocationError(
                _("Allocation for '%(title)s' (%(value)s) is more than this apartment still owes (%(remaining)s).")
                % {"title": expense.title, "value": value, "remaining": remaining}
            )
        rows.append((expense, value))
        total += value
    if total > amount:
        raise AllocationError(
            _("Total allocated (%(sum)s) cannot exceed amount paid (%(amount)s).") % {"sum": total, "amount": amount}
        )
    return rows


def resolve_allocations(apartment, amount, raw_rows, selected_expense_ids=None):
    """Manual amounts when every row has one; otherwise split automatically, oldest first.

    `selected_expense_ids` (or the expenses named in `raw_rows`) limits the automatic split.
    """
    raw_rows = raw_rows or []
    if raw_rows and all(row.get("allocated_amount") is not None for row in raw_rows):
        return check_manual(apartment, amount, raw_rows)
    chosen = list(selected_expense_ids or []) or [row.get("expense_id") for row in raw_rows if row.get("expense_id")]
    return auto_allocate(apartment, amount, chosen or None)


def record_allocations(payment, rows):
    """Store the allocation rows; expenses linked to the payment but not allocated count as 0."""
    for expense, value in rows:
        PaymentExpense.objects.update_or_create(
            payment=payment, expense=expense, defaults={"allocated_amount": value}
        )
    PaymentExpense.objects.filter(payment=payment, allocated_amount__isnull=True).update(allocated_amount=ZERO)
