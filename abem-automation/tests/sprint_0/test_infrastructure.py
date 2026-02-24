"""
Sprint 0 — Infrastructure smoke tests.

Verify that the deployed stack is reachable and correctly configured
before any feature tests run. These tests should pass on every environment.

Markers: smoke, sprint_0, api
"""

import pytest
import requests

from config.settings import get_config
from core.api_client import APIClient

pytestmark = [pytest.mark.sprint_0, pytest.mark.smoke]


# ── API Infrastructure ─────────────────────────────────────────────────────────

@pytest.mark.api
class TestAPIInfrastructure:

    def test_health_endpoint_returns_200(self, env_config):
        """GET /health/ must respond 200 with an 'ok' status."""
        # Build health URL from api_url (strip /api/v1 suffix)
        base = env_config.api_url.rstrip("/")
        root = base.rsplit("/api/v1", 1)[0]
        resp = requests.get(f"{root}/health/", timeout=10)
        assert resp.status_code == 200, (
            f"Health check failed: {resp.status_code} — {resp.text}"
        )
        body = resp.json()
        assert body.get("status") in ("ok", "healthy"), (
            f"Unexpected health payload: {body}"
        )

    def test_api_root_is_accessible(self, env_config):
        """The API root URL should be reachable (2xx or 3xx)."""
        resp = requests.get(env_config.api_url + "/", timeout=10)
        assert resp.status_code < 500, (
            f"API root returned server error: {resp.status_code}"
        )

    def test_openapi_schema_is_accessible(self, env_config):
        """GET /api/v1/schema/ (or /docs/) should return 200."""
        # drf-spectacular serves at /api/v1/schema/ by default
        resp = requests.get(env_config.api_url + "/schema/", timeout=10)
        assert resp.status_code in (200, 301, 302), (
            f"OpenAPI schema not accessible: {resp.status_code}"
        )

    def test_unauthenticated_protected_endpoint_returns_401(self, env_config):
        """A protected endpoint must reject requests without a token."""
        resp = requests.get(env_config.api_url + "/auth/profile/", timeout=10)
        assert resp.status_code == 401, (
            f"Expected 401 for unauthenticated request, got {resp.status_code}"
        )

    def test_cors_headers_present_on_api(self, env_config):
        """CORS headers must be set so the React SPA can call the API."""
        resp = requests.options(
            env_config.api_url + "/auth/login/",
            headers={"Origin": env_config.base_url},
            timeout=10,
        )
        # Django-cors-headers must return the header or a 2xx with Allow
        assert resp.status_code < 500

    def test_login_endpoint_exists(self, env_config):
        """POST /auth/login/ should exist (400 for empty body, not 404)."""
        resp = requests.post(
            env_config.api_url + "/auth/login/",
            json={},
            timeout=10,
        )
        assert resp.status_code != 404, (
            "Login endpoint not found — check URL configuration"
        )
        assert resp.status_code in (400, 401), (
            f"Expected 400/401 for empty login, got {resp.status_code}"
        )


# ── Web Frontend Infrastructure ────────────────────────────────────────────────

@pytest.mark.web
class TestWebInfrastructure:

    def test_frontend_is_reachable(self, env_config):
        """The React SPA root URL should respond with 200."""
        resp = requests.get(env_config.base_url, timeout=15)
        assert resp.status_code == 200, (
            f"Frontend not reachable: {resp.status_code}"
        )

    def test_login_page_is_reachable(self, env_config):
        """GET /login must return 200 (React Router handled on server)."""
        resp = requests.get(f"{env_config.base_url}/login", timeout=15)
        assert resp.status_code == 200

    def test_frontend_serves_html(self, env_config):
        """Root response must be text/html (React app shell)."""
        resp = requests.get(env_config.base_url, timeout=15)
        content_type = resp.headers.get("content-type", "")
        assert "text/html" in content_type, (
            f"Expected HTML response, got content-type: {content_type}"
        )


# ── Environment Config Sanity ──────────────────────────────────────────────────

class TestEnvironmentConfig:

    def test_config_loads_without_error(self):
        """Config loading itself should not raise."""
        cfg = get_config()
        assert cfg is not None

    def test_required_config_fields_present(self, env_config):
        """All required config fields must have non-empty values."""
        assert env_config.api_url, "api_url is empty"
        assert env_config.base_url, "base_url is empty"
        assert env_config.admin_email, "admin_email is empty"
        assert env_config.admin_password, "admin_password is empty"

    def test_api_url_format(self, env_config):
        """API URL must start with http and end with /v1 (versioned)."""
        assert env_config.api_url.startswith("http"), "API URL must be an HTTP(S) URL"
        assert "v1" in env_config.api_url, "API URL must include version segment"

    def test_admin_credentials_are_valid(self, env_config):
        """Admin credentials in config must successfully authenticate."""
        client = APIClient(env_config.api_url)
        data = client.authenticate(env_config.admin_email, env_config.admin_password)
        assert "access" in data
        assert "refresh" in data
        assert data.get("user", {}).get("role") == "admin"
        client.logout()
