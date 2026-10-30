"""
Thin wrappers around the /expenses/ REST endpoints.

All methods return the raw requests.Response so callers can inspect
the status code, headers, and body without this layer making assertions.
"""
from __future__ import annotations

from core.api_client import APIClient


class ExpenseAPI:
    """Stateless helpers for /api/v1/expenses/."""

    ENDPOINT = "/expenses/"

    def __init__(self, client: APIClient) -> None:
        self._c = client

    # ── CRUD ───────────────────────────────────────────────────────────────────

    def create(self, **payload):
        """
        POST /expenses/  → 201 with expense + apartment_shares.
        Accepts any kwargs to allow negative tests to omit required fields.

        Typical valid kwargs: building_id, category_id, title, amount,
        expense_date, split_type, is_recurring, frequency, custom_split_apartments.
        """
        return self._c.post(self.ENDPOINT, json=payload)

    def list(self, building_id: str | None = None, **params):
        """GET /expenses/?building_id=  → paginated list."""
        if building_id is not None:
            params["building_id"] = building_id
        return self._c.get(self.ENDPOINT, params=params or None)

    def get(self, expense_id: str):
        """GET /expenses/{id}/"""
        return self._c.get(f"{self.ENDPOINT}{expense_id}/")

    def update(self, expense_id: str, **fields):
        """PATCH /expenses/{id}/"""
        return self._c.patch(f"{self.ENDPOINT}{expense_id}/", json=fields)

    def delete(self, expense_id: str):
        """DELETE /expenses/{id}/  (soft delete on backend)."""
        return self._c.delete(f"{self.ENDPOINT}{expense_id}/")

    # ── File upload ────────────────────────────────────────────────────────────

    def upload(self, expense_id: str, file_bytes: bytes, filename: str, mime_type: str):
        """
        POST /expenses/{id}/upload/
        Uploads a bill image/PDF as multipart/form-data.

        Passes Content-Type: None so requests can auto-set the correct
        multipart/form-data boundary instead of the default application/json.
        """
        return self._c.post(
            f"{self.ENDPOINT}{expense_id}/upload/",
            files={"file": (filename, file_bytes, mime_type)},
            headers={"Content-Type": None},  # let requests set multipart boundary
        )
