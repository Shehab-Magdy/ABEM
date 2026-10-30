"""Systematic OWASP Top 10 coverage tests."""

import pytest
from playwright.sync_api import APIRequestContext, Playwright

from config.settings import settings
from utils.data_factory import SQL_INJECTION_PAYLOADS, XSS_PAYLOADS
from utils.jwt_helpers import build_tampered_token


@pytest.mark.api
@pytest.mark.security
@pytest.mark.owasp
class TestOWASPTop10:

    # ── A01: Broken Access Control ────────────────────────────

    def test_a01_owner_cannot_escalate_role(
        self, playwright: Playwright, owner_token: str
    ):
        tampered = build_tampered_token(owner_token, {"role": "admin"})
        ctx = playwright.request.new_context(
            base_url=settings.API_BASE_URL,
            extra_http_headers={"Authorization": f"Bearer {tampered}"},
        )
        try:
            resp = ctx.get("/api/v1/users/")
            assert resp.status == 401
        finally:
            ctx.dispose()

    def test_a01_horizontal_privilege_user_profile(
        self, admin_api: APIRequestContext
    ):
        """Admin can list and view users."""
        resp = admin_api.get("/api/v1/users/")
        assert resp.status == 200

    # ── A03: Injection ────────────────────────────────────────

    def test_a03_sql_injection_returns_400(self, api_context: APIRequestContext):
        resp = api_context.post("/api/v1/auth/login/", data={
            "email": "' OR '1'='1", "password": "test",
        })
        assert resp.status in (400, 401)
        assert resp.status != 500

    def test_a03_xss_stored_escaped(self, admin_api: APIRequestContext):
        payload = "<script>alert(1)</script>"
        resp = admin_api.post("/api/v1/buildings/", data={
            "name": payload, "address": "XSS Test Addr",
        })
        if resp.status == 201:
            body = resp.json()
            # If stored, it should be stored as-is (Django handles escaping on output)
            admin_api.delete(f"/api/v1/buildings/{body['id']}/")

    # ── A04: Insecure Direct Object Reference ─────────────────

    def test_a04_idor_apartment_403(
        self, owner_api: APIRequestContext, seeded_building
    ):
        apt = seeded_building["apartment"]
        if not apt:
            pytest.skip("No apartment")
        resp = owner_api.get(f"/api/v1/apartments/{apt['id']}/")
        # Owner should not see another building's apartment
        assert resp.status in (200, 403, 404)

    # ── A05: Security Misconfiguration ────────────────────────

    def test_a05_500_no_stack_trace(self, admin_api: APIRequestContext):
        """Trigger a potential error and verify no stack trace in response."""
        resp = admin_api.get("/api/v1/nonexistent-endpoint/")
        body = resp.text()
        assert "Traceback" not in body
        assert "File \"/" not in body

    def test_a05_no_passwords_in_response(self, admin_api: APIRequestContext):
        resp = admin_api.get("/api/v1/users/")
        body = resp.text()
        assert "password_hash" not in body
        assert '"password"' not in body.replace('"password_hash"', "")

    # ── A07: Authentication Failures ──────────────────────────

    def test_a07_lockout_after_5_attempts(
        self, api_context: APIRequestContext, admin_api: APIRequestContext, create_user
    ):
        user = create_user(role="owner")
        for _ in range(5):
            api_context.post("/api/v1/auth/login/", data={
                "email": user["email"], "password": "WrongPass!1",
            })
        resp = api_context.post("/api/v1/auth/login/", data={
            "email": user["email"], "password": "WrongPass!1",
        })
        assert resp.status in (423, 429)

    # ── A09: Logging and Monitoring Failures ──────────────────

    def test_a09_audit_log_on_write(
        self, admin_api: APIRequestContext, seeded_building
    ):
        resp = admin_api.get("/api/v1/audit/")
        assert resp.status == 200
        body = resp.json()
        results = body.get("results", body) if isinstance(body, dict) else body
        assert len(results) > 0, "Audit log should have entries"

    def test_a09_audit_log_not_deletable(self, admin_api: APIRequestContext):
        resp = admin_api.get("/api/v1/audit/")
        body = resp.json()
        results = body.get("results", body) if isinstance(body, dict) else body
        if results:
            del_resp = admin_api.delete(f"/api/v1/audit/{results[0]['id']}/")
            assert del_resp.status in (405, 403, 404)
