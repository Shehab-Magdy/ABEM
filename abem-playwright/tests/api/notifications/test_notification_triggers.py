"""API tests for notification trigger types."""

import pytest
from playwright.sync_api import APIRequestContext


@pytest.mark.api
@pytest.mark.notifications
class TestNotificationTriggers:

    def test_expense_creates_notification(
        self, admin_api: APIRequestContext, owner_api: APIRequestContext, seeded_expense
    ):
        """After expense creation, owner should see an expense_added notification."""
        resp = owner_api.get("/api/v1/notifications/")
        assert resp.status == 200
        body = resp.json()
        results = body.get("results", body) if isinstance(body, dict) else body
        types = [n.get("notification_type", "") for n in results]
        assert "expense_added" in types, f"No expense_added notification found. Types: {types}"

    def test_payment_creates_notification(
        self, admin_api: APIRequestContext, owner_api: APIRequestContext, seeded_payment
    ):
        """After payment, owner should see a payment_confirmed notification."""
        resp = owner_api.get("/api/v1/notifications/")
        body = resp.json()
        results = body.get("results", body) if isinstance(body, dict) else body
        types = [n.get("notification_type", "") for n in results]
        assert "payment_confirmed" in types, f"No payment_confirmed notification. Types: {types}"

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
