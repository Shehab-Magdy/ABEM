"""Audit log API client — Sprint 8."""
from __future__ import annotations

from core.api_client import APIClient


class AuditAPI:
    """Thin wrappers around the /audit/ REST endpoint."""

    ENDPOINT = "/audit/"

    def __init__(self, client: APIClient) -> None:
        self._c = client

    def list(self, **params):
        """
        GET /api/v1/audit/

        Optional query params:
          entity     – filter by entity type (e.g. "expense", "payment", "user")
          user_id    – filter by actor UUID
          action     – filter by action string (e.g. "create", "update")
          date_from  – ISO date lower bound on created_at
          date_to    – ISO date upper bound on created_at
        """
        return self._c.get(self.ENDPOINT, params=params or None)

    def get(self, log_id: str):
        """GET /api/v1/audit/{id}/"""
        return self._c.get(f"{self.ENDPOINT}{log_id}/")
