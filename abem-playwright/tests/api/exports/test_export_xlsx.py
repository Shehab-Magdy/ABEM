"""API tests for XLSX export functionality."""

import pytest
from playwright.sync_api import APIRequestContext

from utils.csv_helpers import get_xlsx_row_count, parse_xlsx_bytes


@pytest.mark.api
@pytest.mark.exports
class TestExportXLSX:

    def test_export_expenses_xlsx(
        self, admin_api: APIRequestContext, seeded_building
    ):
        bid = seeded_building["building"]["id"]
        resp = admin_api.get("/api/v1/exports/expenses/", params={
            "file_format": "xlsx", "building_id": bid,
        })
        assert resp.status == 200
        ct = resp.headers.get("content-type", "")
        assert "spreadsheet" in ct.lower() or "xlsx" in ct.lower() or "octet" in ct.lower()

    def test_xlsx_has_data(self, admin_api: APIRequestContext, seeded_expense):
        bid = seeded_expense["building"]["id"]
        resp = admin_api.get("/api/v1/exports/expenses/", params={
            "file_format": "xlsx", "building_id": bid,
        })
        rows = parse_xlsx_bytes(resp.body())
        assert len(rows) >= 1

    def test_xlsx_row_count_matches_api(
        self, admin_api: APIRequestContext, seeded_expense
    ):
        bid = seeded_expense["building"]["id"]
        xlsx_resp = admin_api.get("/api/v1/exports/expenses/", params={
            "file_format": "xlsx", "building_id": bid,
        })
        api_resp = admin_api.get("/api/v1/expenses/", params={"building_id": bid})
        api_count = api_resp.json().get("count", len(api_resp.json().get("results", [])))
        xlsx_count = get_xlsx_row_count(xlsx_resp.body())
        assert xlsx_count == api_count
