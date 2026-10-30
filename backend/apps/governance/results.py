"""Counting a poll: eligible units, turnout, quorum and majority."""
from __future__ import annotations

from apps.apartments.models import Apartment


def eligible_units(building):
    """Units that can vote: those with at least one owner (renters do not vote)."""
    units = Apartment.objects.filter(building=building).select_related("owner").prefetch_related("owners")
    return [a for a in units if a.owner_id or any(o.role != "renter" for o in a.owners.all())]


def can_vote_for(user, apartment) -> bool:
    if user.role == "renter":
        return False
    return apartment.owner_id == user.pk or apartment.owners.filter(pk=user.pk).exists()


def poll_results(poll) -> dict:
    eligible = len(eligible_units(poll.building))
    options = list(poll.options.all())
    counts = {o.pk: o.votes.count() for o in options}
    cast = sum(counts.values())
    turnout = round(100 * cast / eligible) if eligible else 0
    quorum_met = turnout >= poll.quorum_percent

    outcome, winner = "no_votes", None
    if cast:
        top = max(counts.values())
        leaders = [o for o in options if counts[o.pk] == top]
        needed = (2 * cast + 2) // 3 if poll.majority == "two_thirds" else cast // 2 + 1  # ceil(2/3 cast) / strictly more than half
        if not quorum_met:
            outcome = "no_quorum"
        elif len(leaders) == 1 and top >= needed:
            outcome, winner = "passed", leaders[0]
        else:
            outcome = "no_majority"
    return {
        "eligible_units": eligible,
        "votes_cast": cast,
        "turnout_percent": turnout,
        "quorum_met": quorum_met,
        "outcome": outcome,
        "winning_option_id": str(winner.pk) if winner else None,
        "options": [{"id": str(o.pk), "text": o.text, "votes": counts[o.pk]} for o in options],
    }
