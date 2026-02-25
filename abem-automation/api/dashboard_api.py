"""Dashboard API client — Sprint 5."""
from __future__ import annotations

from core.api_client import APIClient


class DashboardAPI:
    ADMIN_ENDPOINT = "/dashboard/admin/"
    OWNER_ENDPOINT = "/dashboard/owner/"

    def __init__(self, client: APIClient):
        self._c = client

    def get_admin(
        self,
        building_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ):
        """GET /api/v1/dashboard/admin/ with optional filters."""
        params: dict = {}
        if building_id:
            params["building_id"] = building_id
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        return self._c.get(self.ADMIN_ENDPOINT, params=params or None)

    def get_owner(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
    ):
        """GET /api/v1/dashboard/owner/ with optional date filters."""
        params: dict = {}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        return self._c.get(self.OWNER_ENDPOINT, params=params or None)
