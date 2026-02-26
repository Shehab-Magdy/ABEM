"""
Thin wrapper around the /buildings/ REST endpoints.

All methods return the raw requests.Response so callers can inspect
the status code, headers, and body without this layer making assertions.
"""
from __future__ import annotations

from core.api_client import APIClient


class BuildingAPI:
    """Stateless helpers for /api/v1/buildings/."""

    ENDPOINT = "/buildings/"

    def __init__(self, client: APIClient) -> None:
        self._c = client

    # ── CRUD ───────────────────────────────────────────────────────────────────

    def create(self, **payload):
        """
        POST /buildings/  → 201 with building object.
        Accepts any kwargs and forwards them as-is so negative tests can omit
        required fields and let the backend return the validation error.

        Typical valid kwargs: name, address, num_floors, city, country, num_apartments.
        """
        return self._c.post(self.ENDPOINT, json=payload)

    def list(self, search: str | None = None, page: int | None = None, page_size: int | None = None, **filters):
        """GET /buildings/  → paginated list."""
        params: dict = {}
        if search is not None:
            params["search"] = search
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["page_size"] = page_size
        params.update(filters)
        return self._c.get(self.ENDPOINT, params=params)

    def get(self, building_id: str):
        """GET /buildings/{id}/"""
        return self._c.get(f"{self.ENDPOINT}{building_id}/")

    def update(self, building_id: str, **fields):
        """PATCH /buildings/{id}/"""
        return self._c.patch(f"{self.ENDPOINT}{building_id}/", json=fields)

    def delete(self, building_id: str):
        """DELETE /buildings/{id}/  (soft delete on backend)."""
        return self._c.delete(f"{self.ENDPOINT}{building_id}/")

    # ── Custom actions ─────────────────────────────────────────────────────────

    def assign_user(self, building_id: str, user_id: str):
        """POST /buildings/{id}/assign-user/  → 200/201."""
        return self._c.post(
            f"{self.ENDPOINT}{building_id}/assign-user/",
            json={"user_id": user_id},
        )

    def list_apartments(self, building_id: str, **params):
        """GET /buildings/{id}/apartments/  → paginated list."""
        return self._c.get(
            f"{self.ENDPOINT}{building_id}/apartments/",
            params=params or None,
        )

    def directory(self):
        """
        GET /buildings/directory/
        Returns all active buildings to any authenticated user.
        Used by the sign-up wizard so new owners can browse all buildings
        before they are a member of any.
        """
        return self._c.get(f"{self.ENDPOINT}directory/")
