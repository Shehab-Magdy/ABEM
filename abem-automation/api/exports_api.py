"""Export API client — Sprint 8."""
from __future__ import annotations

from core.api_client import APIClient


class ExportsAPI:
    """Thin wrappers around the /exports/ REST endpoints."""

    def __init__(self, client: APIClient) -> None:
        self._c = client

    def export_payments(self, fmt: str = "csv", **params):
        """
        GET /api/v1/exports/payments/?format=csv|xlsx

        Optional query params:
          apartment_id  – filter by apartment UUID
          date_from     – ISO date lower bound on payment_date
          date_to       – ISO date upper bound on payment_date
        """
        params["file_format"] = fmt
        return self._c.get("/exports/payments/", params=params)

    def export_expenses(self, fmt: str = "csv", **params):
        """
        GET /api/v1/exports/expenses/?file_format=csv|xlsx

        Optional query params:
          building_id  – filter by building UUID
          date_from    – ISO date lower bound on expense_date
          date_to      – ISO date upper bound on expense_date
        """
        params["file_format"] = fmt
        return self._c.get("/exports/expenses/", params=params)
