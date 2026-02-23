"""Custom JWT token with role and tenant_ids claims."""
from rest_framework_simplejwt.tokens import RefreshToken


class CustomRefreshToken(RefreshToken):
    """
    Extends the default RefreshToken to embed user_id, role, and
    tenant_ids (all building UUIDs the user may access) into the
    access token payload, enabling client-side RBAC without extra
    API round-trips.
    """

    @classmethod
    def for_user(cls, user):
        token = super().for_user(user)

        token["user_id"] = str(user.id)
        token["role"] = user.role

        # Union of buildings administered + buildings the user is a member of
        admin_ids = set(
            user.administered_buildings.values_list("id", flat=True)
        )
        member_ids = set(
            user.buildings.values_list("id", flat=True)
        )
        token["tenant_ids"] = [str(uid) for uid in admin_ids | member_ids]

        return token
