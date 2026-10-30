"""Tenant scoping helpers: an admin only works with the buildings they manage."""
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied

from .models import Building


def managed_buildings(user):
    """Active buildings the user administers (primary admin or co-admin)."""
    return Building.objects.filter(
        Q(admin=user) | Q(co_admins=user), deleted_at__isnull=True
    ).distinct()


def ensure_manages(user, building):
    """Raise 403 unless `user` administers `building` (a Building or its pk)."""
    building_id = getattr(building, "pk", building)
    if not managed_buildings(user).filter(pk=building_id).exists():
        raise PermissionDenied("You do not manage this building.")


BOARD_ROLES = ("chair", "treasurer", "secretary")


def board_building_ids(user, role):
    """Ids of the buildings where `user` holds the board title `role` (chair / treasurer / secretary)."""
    from .models import UserBuilding

    return UserBuilding.objects.filter(user=user, board_role=role).values_list("building_id", flat=True)


def has_board_role(user, building, role) -> bool:
    building_id = getattr(building, "pk", building)
    return board_building_ids(user, role).filter(building_id=building_id).exists()
