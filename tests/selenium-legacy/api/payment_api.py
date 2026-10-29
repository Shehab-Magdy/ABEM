"""
Thin wrappers around the /payments/ REST endpoints.

All methods return the raw requests.Response so callers can inspect
the status code, headers, and body without this layer making assertions.
"""
from __future__ import annotations

from core.api_client import APIClient


class PaymentAPI:
    """Stateless helpers for /api/v1/payments/ and the balance endpoint."""

    ENDPOINT = "/payments/"

    def __init__(self, client: APIClient) -> None:
        self._c = client

    # ── CRUD (no update/delete — payments are immutable) ───────────────────────

    def create(self, **payload):
        """
        POST /payments/  → 201 with payment record + balance snapshots.

        Required kwargs: apartment_id, amount_paid, payment_date, payment_method.
        Optional kwargs: expense_id, notes.
        Accepts any kwargs to allow negative tests to omit required fields.
        """
        return self._c.post(self.ENDPOINT, json=payload)

    def list(self, apartment_id: str | None = None, **params):
        """GET /payments/?apartment_id=  → paginated list."""
        if apartment_id is not None:
            params["apartment_id"] = apartment_id
        return self._c.get(self.ENDPOINT, params=params or None)

    def get(self, payment_id: str):
        """GET /payments/{id}/"""
        return self._c.get(f"{self.ENDPOINT}{payment_id}/")

    # ── Balance endpoint (on apartments resource) ──────────────────────────────

    def get_balance(self, apartment_id: str):
        """GET /apartments/{id}/balance/"""
        return self._c.get(f"/apartments/{apartment_id}/balance/")
