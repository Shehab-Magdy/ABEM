"""
Thin wrapper around the /apartments/ REST endpoints.

All methods return the raw requests.Response so callers can inspect
the status code, headers, and body without this layer making assertions.
"""
from __future__ import annotations

from core.api_client import APIClient


class ApartmentAPI:
    """Stateless helpers for /api/v1/apartments/."""

    ENDPOINT = "/apartments/"

    def __init__(self, client: APIClient) -> None:
        self._c = client

    # ── CRUD ───────────────────────────────────────────────────────────────────

    def create(
        self,
        building_id: str,
        unit_number: str,
        floor: int,
        unit_type: str = "apartment",
        size_sqm: float | None = None,
        owner_id: str | None = None,
        status: str = "vacant",
        **extra,
    ):
        """POST /apartments/  → 201 with apartment object."""
        payload: dict = {
            "building_id": building_id,
            "unit_number": unit_number,
            "floor": floor,
            "type": unit_type,
        }
        if size_sqm is not None:
            payload["size_sqm"] = size_sqm
        if owner_id is not None:
            payload["owner_id"] = owner_id
        payload["status"] = status
        payload.update(extra)
        return self._c.post(self.ENDPOINT, json=payload)

    def list(
        self,
        building_id: str | None = None,
        unit_type: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        **filters,
    ):
        """GET /apartments/ with optional query filters."""
        params: dict = {}
        if building_id is not None:
            params["building_id"] = building_id
        if unit_type is not None:
            params["unit_type"] = unit_type
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["page_size"] = page_size
        params.update(filters)
        return self._c.get(self.ENDPOINT, params=params)

    def get(self, apartment_id: str):
        """GET /apartments/{id}/"""
        return self._c.get(f"{self.ENDPOINT}{apartment_id}/")

    def update(self, apartment_id: str, **fields):
        """PATCH /apartments/{id}/"""
        return self._c.patch(f"{self.ENDPOINT}{apartment_id}/", json=fields)

    def delete(self, apartment_id: str):
        """DELETE /apartments/{id}/"""
        return self._c.delete(f"{self.ENDPOINT}{apartment_id}/")

    # ── Sign-up wizard helpers ─────────────────────────────────────────────────

    def available(self, building_id: str):
        """
        GET /apartments/available/?building_id={id}
        Returns unowned apartments for a building.
        Used in the owner sign-up wizard so the user can pick their unit.
        """
        return self._c.get(
            f"{self.ENDPOINT}available/",
            params={"building_id": building_id},
        )

    def claim(self, apartment_id: str):
        """
        POST /apartments/{id}/claim/
        Owner-role user claims a vacant apartment during sign-up.
        Sets owner=request.user, status=occupied, auto-joins the building.

        Expected responses:
          200 – apartment object with owner set
          403 – caller is not owner-role
          404 – apartment not found
          409 – apartment already owned
        """
        return self._c.post(f"{self.ENDPOINT}{apartment_id}/claim/")
