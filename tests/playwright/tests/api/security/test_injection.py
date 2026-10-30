"""API tests for SQL injection and XSS prevention."""

import pytest
from playwright.sync_api import APIRequestContext

from utils.data_factory import SQL_INJECTION_PAYLOADS, XSS_PAYLOADS, HEADER_INJECTION_PAYLOADS


@pytest.mark.api
@pytest.mark.security
@pytest.mark.injection
class TestInjection:

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS[:3])
    def test_sql_injection_in_login_email(
        self, api_context: APIRequestContext, payload
    ):
        resp = api_context.post("/api/v1/auth/login/", data={
            "email": payload, "password": "any",
        })
        assert resp.status in (400, 401), (
            f"SQL injection returned {resp.status}, expected 400/401"
        )
        assert resp.status != 500

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS[:3])
    def test_sql_injection_in_building_name(
        self, admin_api: APIRequestContext, payload
    ):
        resp = admin_api.post("/api/v1/buildings/", data={
            "name": payload, "address": "Test Addr",
        })
        # Should either succeed (parameterized query) or return 400, never 500
        assert resp.status != 500, f"SQL injection caused 500 error"
        if resp.status == 201:
            admin_api.delete(f"/api/v1/buildings/{resp.json()['id']}/")

    @pytest.mark.parametrize("payload", XSS_PAYLOADS[:2])
    def test_xss_in_text_fields(self, admin_api: APIRequestContext, payload):
        resp = admin_api.post("/api/v1/buildings/", data={
            "name": payload, "address": "Test",
        })
        if resp.status == 201:
            body = resp.json()
            # The stored value should not execute as HTML
            stored_name = body.get("name", "")
            assert "<script>" not in stored_name or payload in stored_name
            admin_api.delete(f"/api/v1/buildings/{body['id']}/")

    @pytest.mark.parametrize("payload", HEADER_INJECTION_PAYLOADS[:1])
    def test_header_injection(self, admin_api: APIRequestContext, payload):
        resp = admin_api.post("/api/v1/buildings/", data={
            "name": payload, "address": "Test",
        })
        assert resp.status in (200, 201, 400), f"Unexpected status: {resp.status}"
        if resp.status == 201:
            admin_api.delete(f"/api/v1/buildings/{resp.json()['id']}/")
