"""Recurring expenses: create the next copy of each one that is due."""
from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.utils import timezone

from apps.audit.mixins import log_job_run

from .models import Expense, RecurringConfig, RecurringFrequency, SplitType
from .utils import run_split_engine

_STEP = {
    RecurringFrequency.MONTHLY: relativedelta(months=1),
    RecurringFrequency.QUARTERLY: relativedelta(months=3),
    RecurringFrequency.ANNUAL: relativedelta(years=1),
}


def generate_recurring_expenses() -> int:
    """Create the next copy of every recurring expense that is due. Returns how many were created.

    The original expense stays the template (it keeps its RecurringConfig); each copy is a
    normal one-off expense dated on the due date and split like the template.
    """
    today = timezone.localdate()
    created = 0
    runs: dict = {}
    due = RecurringConfig.objects.filter(is_active=True, next_due__lte=today).select_related("expense")
    for config in due:
        template = config.expense
        if template.deleted_at is not None:
            continue
        with transaction.atomic():
            # Catch up if beat was down: one copy per missed period
            while config.next_due <= today:
                copy = Expense.objects.create(
                    building=template.building,
                    category=template.category,
                    title=template.title,
                    description=template.description,
                    amount=template.amount,
                    expense_date=config.next_due,
                    split_type=template.split_type,
                    is_recurring=False,
                    created_by=template.created_by,
                )
                weights = None
                if template.split_type == SplitType.CUSTOM:
                    weights = {str(s.apartment_id): s.share_amount for s in template.apartment_expenses.all()}
                run_split_engine(copy, None, weights)
                config.next_due = config.next_due + _STEP[config.frequency]
                created += 1
                runs.setdefault(template.building_id, {"created": 0})["created"] += 1
            config.save(update_fields=["next_due"])
    log_job_run("generate_recurring", runs)
    return created
