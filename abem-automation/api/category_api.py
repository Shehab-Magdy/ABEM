"""
Thin wrappers around the /expenses/categories/ REST endpoints.

All methods return the raw requests.Response.
"""
from __future__ import annotations

from core.api_client import APIClient


class CategoryAPI:
    """Stateless helpers for /api/v1/expenses/categories/."""

    ENDPOINT = "/expenses/categories/"

    def __init__(self, client: APIClient) -> None:
        self._c = client

    def create(self, **payload):
        """
        POST /expenses/categories/  → 201 with category object.
        Typical valid kwargs: building_id, name, description.
        """
        return self._c.post(self.ENDPOINT, json=payload)

    def list(self, building_id: str | None = None, **params):
        """GET /expenses/categories/?building_id=  → paginated list."""
        if building_id is not None:
            params["building_id"] = building_id
        return self._c.get(self.ENDPOINT, params=params or None)

    def get(self, category_id: str):
        """GET /expenses/categories/{id}/"""
        return self._c.get(f"{self.ENDPOINT}{category_id}/")

    def update(self, category_id: str, **fields):
        """PATCH /expenses/categories/{id}/"""
        return self._c.patch(f"{self.ENDPOINT}{category_id}/", json=fields)

    def delete(self, category_id: str):
        """DELETE /expenses/categories/{id}/"""
        return self._c.delete(f"{self.ENDPOINT}{category_id}/")
