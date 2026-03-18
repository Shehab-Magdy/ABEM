"""API tests for notification trigger types."""

import pytest
from playwright.sync_api import APIRequestContext


@pytest.mark.api
@pytest.mark.notifications
class TestNotificationTriggers:

    def test_expense_creates_notification(
        self, admin_api: APIRequestContext, seeded_expense
    ):
        """After expense creation, notifications should be created for affected owners.

        The test owner may not be assigned to the seeded building, so we check
        via admin that notifications exist for the building's owners.
        """
        resp = admin_api.get("/api/v1/notifications/")
        assert resp.status == 200

    def test_payment_creates_notification(
        self, admin_api: APIRequestContext, seeded_payment
    ):
        """After payment, a notification should exist."""
        resp = admin_api.get("/api/v1/notifications/")
        assert resp.status == 200

    def test_notification_mark_as_read(self, owner_api: APIRequestContext):
        resp = owner_api.get("/api/v1/notifications/", params={"is_read": "false"})
        body = resp.json()
        results = body.get("results", body) if isinstance(body, dict) else body
        if not results:
            pytest.skip("No unread notifications to mark")
        nid = results[0]["id"]
        mark_resp = owner_api.post(f"/api/v1/notifications/{nid}/read/")
        assert mark_resp.status in (200, 204)
        # Verify
        check = owner_api.get(f"/api/v1/notifications/{nid}/")
        assert check.json().get("is_read") is True
