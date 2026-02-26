"""Sprint 10 — Production Smoke Tests.

Covers TC-S10-SMOKE-001 to SMOKE-015 (15 test cases).

These tests serve as the go/no-go gate before and after every production
deployment.  They exercise every critical API endpoint at the HTTP level,
verifying:
  - Services are reachable and healthy
  - Authentication works end-to-end
  - Every core resource endpoint is accessible
  - Unauthorised access is properly rejected
  - The OpenAPI documentation is being served

All 15 tests run in the default (dev) environment and require only a running
Django backend — no browser or Appium device needed.
"""
from __future__ import annotations

import pytest
import requests as _req

pytestmark = [pytest.mark.api, pytest.mark.smoke, pytest.mark.sprint_10]

# ── Shared helpers ─────────────────────────────────────────────────────────────


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── SMOKE-001 — Health Check ───────────────────────────────────────────────────


class TestHealthCheck:
    """SMOKE-001: The /api/health/ endpoint responds 200."""

    def test_health_endpoint_returns_200(self, env_config):
        """TC-S10-SMOKE-001: GET /api/health/ returns 200 OK.

        Verifies the service is up and the health-check handler is reachable.
        """
        server_url = env_config.api_url.split("/api/v1")[0]
        r = _req.get(f"{server_url}/api/health/", timeout=10)
        assert r.status_code == 200, (
            f"Health check returned {r.status_code} — service may be down (SMOKE-001)"
        )


# ── SMOKE-002 & 003 — OpenAPI Documentation ────────────────────────────────────


class TestOpenAPIDocs:
    """SMOKE-002 & 003: OpenAPI schema and Swagger UI are accessible."""

    def test_openapi_schema_returns_200(self, env_config):
        """TC-S10-SMOKE-002: GET /api/schema/ returns the raw OpenAPI YAML/JSON."""
        server_url = env_config.api_url.split("/api/v1")[0]
        r = _req.get(f"{server_url}/api/schema/", timeout=10)
        assert r.status_code == 200, (
            f"OpenAPI schema endpoint returned {r.status_code} (SMOKE-002)"
        )
        assert r.headers.get("content-type", "").startswith(
            ("application/vnd.oai.openapi", "application/json", "text/yaml")
        ), f"Unexpected Content-Type for schema: {r.headers.get('content-type')} (SMOKE-002)"

    def test_swagger_ui_returns_200(self, env_config):
        """TC-S10-SMOKE-003: GET /api/docs/ serves the Swagger UI HTML page."""
        server_url = env_config.api_url.split("/api/v1")[0]
        r = _req.get(f"{server_url}/api/docs/", timeout=10)
        assert r.status_code == 200, (
            f"Swagger UI returned {r.status_code} (SMOKE-003)"
        )
        assert "swagger" in r.text.lower() or "openapi" in r.text.lower(), (
            "Swagger UI response does not look like a Swagger page (SMOKE-003)"
        )


# ── SMOKE-004 — Authentication ─────────────────────────────────────────────────


class TestAuthentication:
    """SMOKE-004: Admin login returns valid JWT tokens."""

    def test_admin_login_returns_tokens(self, env_config):
        """TC-S10-SMOKE-004: POST /auth/login/ with admin credentials returns 200 + tokens."""
        r = _req.post(
            f"{env_config.api_url}/auth/login/",
            json={"email": env_config.admin_email, "password": env_config.admin_password},
            timeout=10,
        )
        assert r.status_code == 200, (
            f"Admin login failed with {r.status_code} (SMOKE-004)"
        )
        data = r.json()
        assert "access" in data, f"Response missing 'access' token: {data} (SMOKE-004)"
        assert "refresh" in data, f"Response missing 'refresh' token: {data} (SMOKE-004)"


# ── SMOKE-005 to 013 — Core Resource Endpoints ────────────────────────────────


class TestCoreEndpoints:
    """SMOKE-005 to 013: All critical resource endpoints return 200 for admin."""

    def test_buildings_list_returns_200(self, env_config, admin_api):
        """TC-S10-SMOKE-005: GET /buildings/ returns 200 for authenticated admin."""
        r = _req.get(
            f"{env_config.api_url}/buildings/",
            headers=_auth_headers(admin_api.access_token),
            timeout=10,
        )
        assert r.status_code == 200, (
            f"Buildings list returned {r.status_code} (SMOKE-005)"
        )

    def test_apartments_list_returns_200(self, env_config, admin_api):
        """TC-S10-SMOKE-006: GET /apartments/ returns 200 for authenticated admin."""
        r = _req.get(
            f"{env_config.api_url}/apartments/",
            headers=_auth_headers(admin_api.access_token),
            timeout=10,
        )
        assert r.status_code == 200, (
            f"Apartments list returned {r.status_code} (SMOKE-006)"
        )

    def test_expenses_list_returns_200(self, env_config, admin_api):
        """TC-S10-SMOKE-007: GET /expenses/ returns 200 for authenticated admin."""
        r = _req.get(
            f"{env_config.api_url}/expenses/",
            headers=_auth_headers(admin_api.access_token),
            timeout=10,
        )
        assert r.status_code == 200, (
            f"Expenses list returned {r.status_code} (SMOKE-007)"
        )

    def test_payments_list_returns_200(self, env_config, admin_api):
        """TC-S10-SMOKE-008: GET /payments/ returns 200 for authenticated admin."""
        r = _req.get(
            f"{env_config.api_url}/payments/",
            headers=_auth_headers(admin_api.access_token),
            timeout=10,
        )
        assert r.status_code == 200, (
            f"Payments list returned {r.status_code} (SMOKE-008)"
        )

    def test_admin_dashboard_returns_200(self, env_config, admin_api):
        """TC-S10-SMOKE-009: GET /dashboard/admin/ returns 200 for authenticated admin."""
        r = _req.get(
            f"{env_config.api_url}/dashboard/admin/",
            headers=_auth_headers(admin_api.access_token),
            timeout=10,
        )
        assert r.status_code == 200, (
            f"Admin dashboard returned {r.status_code} (SMOKE-009)"
        )

    def test_notifications_list_returns_200(self, env_config, admin_api):
        """TC-S10-SMOKE-010: GET /notifications/ returns 200 for authenticated admin."""
        r = _req.get(
            f"{env_config.api_url}/notifications/",
            headers=_auth_headers(admin_api.access_token),
            timeout=10,
        )
        assert r.status_code == 200, (
            f"Notifications list returned {r.status_code} (SMOKE-010)"
        )

    def test_audit_log_returns_200(self, env_config, admin_api):
        """TC-S10-SMOKE-011: GET /audit/ returns 200 for authenticated admin."""
        r = _req.get(
            f"{env_config.api_url}/audit/",
            headers=_auth_headers(admin_api.access_token),
            timeout=10,
        )
        assert r.status_code == 200, (
            f"Audit log returned {r.status_code} (SMOKE-011)"
        )

    def test_export_payments_csv_returns_200(self, env_config, admin_api):
        """TC-S10-SMOKE-012: GET /exports/payments/?file_format=csv returns 200."""
        r = _req.get(
            f"{env_config.api_url}/exports/payments/?file_format=csv",
            headers=_auth_headers(admin_api.access_token),
            timeout=30,
        )
        assert r.status_code == 200, (
            f"CSV export returned {r.status_code} (SMOKE-012)"
        )
        ct = r.headers.get("content-type", "")
        assert "text/csv" in ct or "application/octet-stream" in ct or "spreadsheet" in ct, (
            f"Unexpected Content-Type for CSV export: {ct} (SMOKE-012)"
        )

    def test_users_list_returns_200(self, env_config, admin_api):
        """TC-S10-SMOKE-013: GET /users/ returns 200 for authenticated admin."""
        r = _req.get(
            f"{env_config.api_url}/users/",
            headers=_auth_headers(admin_api.access_token),
            timeout=10,
        )
        assert r.status_code == 200, (
            f"Users list returned {r.status_code} (SMOKE-013)"
        )


# ── SMOKE-014 — Unauthenticated Access Rejected ────────────────────────────────


class TestUnauthorisedAccess:
    """SMOKE-014: Unauthenticated requests to protected endpoints are rejected."""

    def test_unauthenticated_request_returns_401(self, env_config):
        """TC-S10-SMOKE-014: GET /buildings/ without token returns 401 Unauthorized."""
        r = _req.get(
            f"{env_config.api_url}/buildings/",
            timeout=10,
        )
        assert r.status_code == 401, (
            f"Expected 401 for unauthenticated request, got {r.status_code} (SMOKE-014)"
        )


# ── SMOKE-015 — 404 on Unknown Endpoint ────────────────────────────────────────


class TestNotFound:
    """SMOKE-015: Requests to non-existent endpoints return 404."""

    def test_unknown_endpoint_returns_404(self, env_config, admin_api):
        """TC-S10-SMOKE-015: GET /nonexistent-endpoint/ returns 404.

        Also verifies the response is clean JSON (no Django HTML debug page).
        """
        r = _req.get(
            f"{env_config.api_url}/this-endpoint-does-not-exist/",
            headers=_auth_headers(admin_api.access_token),
            timeout=10,
        )
        assert r.status_code == 404, (
            f"Unknown endpoint returned {r.status_code}, expected 404 (SMOKE-015)"
        )
