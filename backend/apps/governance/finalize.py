"""When a poll about an expense ends, its outcome settles the expense."""
from __future__ import annotations

from django.utils import timezone

from apps.expenses.approval import approve, reject

from .models import Poll
from .results import poll_results


def apply_poll_outcome(poll: Poll) -> bool:
    """Approve or reject the poll's expense by its result. Returns True if the poll was settled.

    Only a clear result acts: "passed" with the first option (approve) or the second (reject). A tie, too few
    votes or no quorum leaves the expense pending so the chair can decide or call another vote.
    """
    if poll.expense_id is None or poll.finalized_at is not None:
        return False
    results = poll_results(poll)
    options = list(poll.options.all())  # ordered: [approve, reject]
    if results["outcome"] == "passed" and len(options) >= 2:
        winner = results["winning_option_id"]
        if winner == str(options[0].pk):
            approve(poll.expense, None, "Approved by a vote of the residents")
        elif winner == str(options[1].pk):
            reject(poll.expense, None, "Rejected by a vote of the residents")
    poll.finalized_at = timezone.now()
    poll.save(update_fields=["finalized_at"])
    return True


def finalize_polls(now=None) -> int:
    """Settle every expense poll whose time is up (run daily; safe to repeat)."""
    now = now or timezone.now()
    due = Poll.objects.filter(expense__isnull=False, finalized_at__isnull=True).select_related("expense", "building")
    return sum(1 for p in due if (p.closed_at or p.closes_at) <= now and apply_poll_outcome(p))
