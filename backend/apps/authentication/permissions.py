"""Custom DRF permission classes for RBAC."""
from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """Allow access only to users with the Admin role."""

    message = "You do not have permission to perform this action. Admin role required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "admin"
        )


class IsOwnerOrAdmin(BasePermission):
    """Allow access to Admins or the object's owner."""

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role == "admin":
            return True
        # For objects that have a direct `user` or `owner` FK
        owner = getattr(obj, "user", None) or getattr(obj, "owner", None)
        return owner == request.user
