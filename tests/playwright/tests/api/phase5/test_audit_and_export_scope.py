"""API tests: audit-log list is scoped to the caller's buildings (and filterable by entity / paged), and the
whole-building XLSX export is admin-only and tenant scoped."""

import io
import zipfile

import pytest

from fixtures.phase5 import API, unwrap

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@pytest.mark.api
@pytest.mark.phase5
@pytest.mark.tenant_isolation
class TestAuditLogScope:
    def test_reversal_is_visible_to_the_buildings_admin_only(self, admin_api, second_admin_api, reversible_payment):
        pid = reversible_payment["payment"]["id"]
        assert admin_api.post(f"{API}/payments/{pid}/reverse/", data={"reason": "Scope"}).status == 201
        mine = unwrap(admin_api.get(f"{API}/audit/", params={"entity": "payment", "page_size": 200}).json())
        assert any(r["entity_id"] == pid for r in mine)
        theirs = unwrap(second_admin_api.get(f"{API}/audit/", params={"page_size": 500}).json())
        assert not any(r["entity_id"] == pid for r in theirs)

    def test_other_admin_sees_nothing_about_this_building(self, admin_api, second_admin_api, billed_unit):
        bid = billed_unit["building"]["id"]
        theirs = unwrap(second_admin_api.get(f"{API}/audit/", params={"page_size": 500}).json())
        assert not any(r["entity_id"] == bid or bid in str(r.get("changes")) for r in theirs)

    def test_entity_filter_only_returns_that_entity(self, admin_api, billed_unit):
        rows = unwrap(admin_api.get(f"{API}/audit/", params={"entity": "expense", "page_size": 100}).json())
        assert rows and all(r["entity"] == "expense" for r in rows)

    def test_page_and_page_size(self, admin_api, billed_unit):
        resp = admin_api.get(f"{API}/audit/", params={"page": 1, "page_size": 2})
        assert resp.status == 200
        body = resp.json()
        assert len(body["results"]) <= 2
        assert {"count", "next", "previous", "results"} <= set(body)

    def test_owner_cannot_read_the_audit_log(self, member_owner):
        assert member_owner["api"].get(f"{API}/audit/").status == 403

    def test_unauthenticated(self, unauthenticated_api):
        assert unauthenticated_api.get(f"{API}/audit/").status == 401


@pytest.mark.api
@pytest.mark.exports
@pytest.mark.phase5
class TestBuildingExport:
    def test_admin_downloads_an_xlsx_workbook(self, admin_api, reversible_payment):
        bid = reversible_payment["building"]["id"]
        resp = admin_api.get(f"{API}/exports/building/{bid}/")
        assert resp.status == 200, resp.text()
        assert XLSX in resp.headers.get("content-type", "")
        assert "attachment" in resp.headers.get("content-disposition", "").lower()
        body = resp.body()
        assert body[:2] == b"PK", "an xlsx file is a zip archive"
        with zipfile.ZipFile(io.BytesIO(body)) as z:
            assert "xl/workbook.xml" in z.namelist()

    def test_workbook_has_several_sheets(self, admin_api, billed_unit):
        resp = admin_api.get(f"{API}/exports/building/{billed_unit['building']['id']}/")
        assert resp.status == 200
        with zipfile.ZipFile(io.BytesIO(resp.body())) as z:
            sheets = [n for n in z.namelist() if n.startswith("xl/worksheets/sheet")]
        assert len(sheets) >= 3

    @pytest.mark.tenant_isolation
    def test_other_admin_gets_404(self, second_admin_api, billed_unit):
        resp = second_admin_api.get(f"{API}/exports/building/{billed_unit['building']['id']}/")
        assert resp.status == 404

    @pytest.mark.rbac
    def test_owner_is_forbidden(self, member_owner):
        resp = member_owner["api"].get(f"{API}/exports/building/{member_owner['building']['id']}/")
        assert resp.status == 403

    def test_unauthenticated_is_401(self, unauthenticated_api, billed_unit):
        assert unauthenticated_api.get(f"{API}/exports/building/{billed_unit['building']['id']}/").status == 401

    def test_unknown_building_is_404(self, admin_api):
        assert admin_api.get(f"{API}/exports/building/00000000-0000-0000-0000-000000000000/").status == 404
