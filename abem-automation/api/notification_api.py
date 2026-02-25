"""Notification API client — Sprint 6."""
from __future__ import annotations

from core.api_client import APIClient


class NotificationAPI:
    ENDPOINT = "/notifications/"

    def __init__(self, client: APIClient) -> None:
        self._c = client

    def list(self, is_read: bool | None = None):
        """GET /api/v1/notifications/ with optional is_read filter."""
        params: dict = {}
        if is_read is not None:
            params["is_read"] = str(is_read).lower()
        return self._c.get(self.ENDPOINT, params=params or None)

    def get(self, notification_id: str):
        """GET /api/v1/notifications/{id}/"""
        return self._c.get(f"{self.ENDPOINT}{notification_id}/")

    def mark_read(self, notification_id: str):
        """POST /api/v1/notifications/{id}/read/"""
        return self._c.post(f"{self.ENDPOINT}{notification_id}/read/")

    def broadcast(self, subject: str, message: str, building_id: str):
        """POST /api/v1/notifications/broadcast/"""
        return self._c.post(
            f"{self.ENDPOINT}broadcast/",
            json={"subject": subject, "message": message, "building_id": building_id},
        )
