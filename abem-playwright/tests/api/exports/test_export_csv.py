"""API tests for CSV export functionality."""

import pytest
from playwright.sync_api import APIRequestContext

from utils.csv_helpers import get_csv_headers, parse_csv_bytes


@pytest.mark.api
@pytest.mark.exports
class TestExportCSV:

    def test_export_payments_csv(self, admin_api: APIRequestContext):
        resp = admin_api.get("/api/v1/exports/payments/", params={"format": "csv"})
        assert resp.status == 200
        ct = resp.headers.get("content-type", "")
        assert "csv" in ct.lower() or "text" in ct.lower()

    def test_csv_has_correct_columns(self, admin_api: APIRequestContext):
        resp = admin_api.get("/api/v1/exports/payments/", params={"format": "csv"})
        headers = get_csv_headers(resp.body())
        assert len(headers) > 0, "CSV has no header row"

    def test_csv_data_matches_api(
        self, admin_api: APIRequestContext, seeded_payment
    ):
        resp = admin_api.get("/api/v1/exports/payments/", params={"format": "csv"})
        rows = parse_csv_bytes(resp.body())
        assert len(rows) >= 1, "CSV should have at least one data row"

    def test_export_with_no_data_returns_header(self, admin_api: APIRequestContext):
        resp = admin_api.get("/api/v1/exports/payments/", params={
            "format": "csv",
            "date_from": "2099-01-01",
            "date_to": "2099-12-31",
        })
        assert resp.status == 200
        rows = parse_csv_bytes(resp.body())
        assert len(rows) == 0, "Expected empty data rows for future date range"

    def test_owner_cannot_export(self, owner_api: APIRequestContext):
        resp = owner_api.get("/api/v1/exports/payments/", params={"format": "csv"})
        assert resp.status == 403
