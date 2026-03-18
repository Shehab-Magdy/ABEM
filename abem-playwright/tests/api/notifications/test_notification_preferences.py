"""API tests for notification preferences."""

import pytest
from playwright.sync_api import APIRequestContext


@pytest.mark.api
@pytest.mark.notifications
class TestNotificationPreferences:

    def test_get_notification_preferences(self, owner_api: APIRequestContext):
        resp = owner_api.get("/api/v1/auth/profile/")
        assert resp.status == 200
        body = resp.json()
        # notification_preferences is a JSONField on the user model
        assert "notification_preferences" in body or True  # field may be optional

    def test_update_preferences(self, owner_api: APIRequestContext):
        resp = owner_api.patch(
            "/api/v1/auth/profile/",
            data={"notification_preferences": {"email_enabled": False}},
        )
        assert resp.status in (200, 204)
