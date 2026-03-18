"""API tests for export date range and building scope filters."""

import pytest
from playwright.sync_api import APIRequestContext

from utils.csv_helpers import parse_csv_bytes


@pytest.mark.api
@pytest.mark.exports
class TestExportFilters:

    def test_export_date_range_filter(self, admin_api: APIRequestContext):
        resp = admin_api.get("/api/v1/exports/payments/", params={
            "date_from": "2026-01-01", "date_to": "2026-12-31",
        })
        assert resp.status == 200

    def test_export_building_scope(
        self, admin_api: APIRequestContext, seeded_building
    ):
        bid = seeded_building["building"]["id"]
        resp = admin_api.get("/api/v1/exports/expenses/", params={
            "building_id": bid, "file_format": "csv",
        })
        assert resp.status == 200

    def test_export_empty_date_range(self, admin_api: APIRequestContext):
        resp = admin_api.get("/api/v1/exports/payments/", params={
            "date_from": "2099-01-01", "date_to": "2099-12-31",
        })
        rows = parse_csv_bytes(resp.body())
        assert len(rows) == 0
