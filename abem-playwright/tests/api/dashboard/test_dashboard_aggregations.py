"""API tests for dashboard aggregations."""

import time

import pytest
from playwright.sync_api import APIRequestContext


@pytest.mark.api
@pytest.mark.dashboard
class TestDashboardAggregations:

    def test_admin_dashboard_returns_data(self, admin_api: APIRequestContext):
        resp = admin_api.get("/api/v1/dashboard/admin/")
        assert resp.status == 200
        body = resp.json()
        assert isinstance(body, dict)

    def test_admin_dashboard_building_filter(
        self, admin_api: APIRequestContext, seeded_building
    ):
        bid = seeded_building["building"]["id"]
        resp = admin_api.get("/api/v1/dashboard/admin/", params={"building_id": bid})
        assert resp.status == 200

    def test_owner_dashboard_returns_data(self, owner_api: APIRequestContext):
        resp = owner_api.get("/api/v1/dashboard/owner/")
        assert resp.status == 200

    def test_owner_cannot_access_admin_dashboard(self, owner_api: APIRequestContext):
        resp = owner_api.get("/api/v1/dashboard/admin/")
        assert resp.status == 403

    def test_dashboard_responds_within_1s(self, admin_api: APIRequestContext):
        start = time.time()
        resp = admin_api.get("/api/v1/dashboard/admin/")
        elapsed_ms = (time.time() - start) * 1000
        assert resp.status == 200
        assert elapsed_ms < 1000, (
            f"Dashboard took {elapsed_ms:.0f}ms, exceeds 1000ms threshold"
        )
