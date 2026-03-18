"""API tests for admin broadcast notifications."""

import pytest
from playwright.sync_api import APIRequestContext

from utils.data_factory import build_broadcast


@pytest.mark.api
@pytest.mark.notifications
class TestNotificationBroadcast:

    def test_admin_broadcast(self, admin_api: APIRequestContext, seeded_building):
        bid = seeded_building["building"]["id"]
        resp = admin_api.post(
            "/api/v1/notifications/broadcast/",
            data=build_broadcast(bid),
        )
        assert resp.status in (200, 201)

    def test_owner_cannot_broadcast(
        self, owner_api: APIRequestContext, seeded_building
    ):
        bid = seeded_building["building"]["id"]
        resp = owner_api.post(
            "/api/v1/notifications/broadcast/",
            data=build_broadcast(bid),
        )
        assert resp.status == 403
