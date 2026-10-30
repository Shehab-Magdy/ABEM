"""API tests for pagination and filtering across all list endpoints."""

import pytest
from playwright.sync_api import APIRequestContext


@pytest.mark.api
@pytest.mark.pagination
class TestListPaginationFilters:

    def test_buildings_paginated(self, admin_api: APIRequestContext):
        resp = admin_api.get("/api/v1/buildings/")
        body = resp.json()
        assert "count" in body
        assert "results" in body

    def test_high_page_returns_empty(self, admin_api: APIRequestContext):
        resp = admin_api.get("/api/v1/buildings/", params={"page": 999})
        assert resp.status in (200, 404)
        if resp.status == 200:
            body = resp.json()
            assert len(body.get("results", [])) == 0

    def test_expenses_filter_by_building(
        self, admin_api: APIRequestContext, seeded_building
    ):
        bid = seeded_building["building"]["id"]
        resp = admin_api.get("/api/v1/expenses/", params={"building_id": bid})
        assert resp.status == 200

    def test_expenses_filter_by_date_range(self, admin_api: APIRequestContext):
        resp = admin_api.get("/api/v1/expenses/", params={
            "date_from": "2026-01-01", "date_to": "2026-12-31",
        })
        assert resp.status == 200

    def test_apartments_filter_by_type(
        self, admin_api: APIRequestContext, seeded_building
    ):
        bid = seeded_building["building"]["id"]
        resp = admin_api.get("/api/v1/apartments/", params={
            "building_id": bid, "unit_type": "store",
        })
        assert resp.status == 200
        results = resp.json().get("results", resp.json())
        for apt in results:
            assert apt.get("type", apt.get("unit_type")) == "store"

    def test_notifications_filter_unread(self, owner_api: APIRequestContext):
        resp = owner_api.get("/api/v1/notifications/", params={"is_read": "false"})
        assert resp.status == 200

    def test_default_page_size(self, admin_api: APIRequestContext):
        resp = admin_api.get("/api/v1/buildings/")
        body = resp.json()
        assert len(body.get("results", [])) <= 20

    def test_audit_filter_by_entity(self, admin_api: APIRequestContext):
        resp = admin_api.get("/api/v1/audit/", params={"entity": "expense"})
        assert resp.status == 200
