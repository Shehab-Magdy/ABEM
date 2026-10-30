"""Approval of large costs: a cost above the building's threshold bills no one until it is approved."""
from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.buildings.scoping import has_board_role, managed_buildings

from .models import Expense
from .utils import run_split_engine


def needs_approval(expense: Expense) -> bool:
    threshold = expense.building.approval_threshold
    return expense.kind == "cost" and threshold is not None and expense.amount > threshold


def can_decide(user, building) -> bool:
    """The chair decides. A building with no chair yet is not stuck: its admins decide until one is named."""
    from apps.buildings.models import UserBuilding

    if has_board_role(user, building, "chair"):
        return True
    has_chair = UserBuilding.objects.filter(building=building, board_role="chair").exists()
    return not has_chair and user.role == "admin" and managed_buildings(user).filter(pk=building.pk).exists()


def approve(expense: Expense, user=None, note: str = "") -> Expense:
    """Bill the units now (using the split chosen at creation) and mark the expense approved."""
    with transaction.atomic():
        expense = Expense.objects.select_for_update().get(pk=expense.pk)
        if expense.approval_status != "pending":
            return expense
        split = expense.pending_split or {}
        run_split_engine(expense, split.get("apartments") or None, split.get("weights") or None)
        expense.approval_status, expense.approval_note = "approved", note[:200]
        expense.decided_by, expense.decided_at, expense.pending_split = user, timezone.now(), {}
        expense.save()

    try:  # tell the owners they were billed
        from apps.notifications.services import notify_expense_created

        notify_expense_created(expense, [ae.apartment for ae in expense.apartment_expenses.select_related("apartment__owner")])
    except Exception:
        pass
    return expense


def reject(expense: Expense, user=None, note: str = "") -> Expense:
    with transaction.atomic():
        expense = Expense.objects.select_for_update().get(pk=expense.pk)
        if expense.approval_status != "pending":
            return expense
        expense.approval_status, expense.approval_note = "rejected", note[:200]
        expense.decided_by, expense.decided_at, expense.pending_split = user, timezone.now(), {}
        expense.save()
    return expense
