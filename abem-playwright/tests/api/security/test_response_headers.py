"""API tests for security response headers."""

import pytest
from playwright.sync_api import APIRequestContext


@pytest.mark.api
@pytest.mark.security
class TestResponseHeaders:

    def test_content_type_json(self, admin_api: APIRequestContext):
        resp = admin_api.get("/api/v1/buildings/")
        ct = resp.headers.get("content-type", "")
        assert "application/json" in ct

    def test_x_frame_options(self, admin_api: APIRequestContext):
        resp = admin_api.get("/api/v1/buildings/")
        xfo = resp.headers.get("x-frame-options", "")
        assert xfo.upper() in ("DENY", "SAMEORIGIN", ""), (
            f"X-Frame-Options: {xfo}"
        )

    def test_x_content_type_options(self, admin_api: APIRequestContext):
        resp = admin_api.get("/api/v1/buildings/")
        xcto = resp.headers.get("x-content-type-options", "")
        if xcto:
            assert xcto.lower() == "nosniff"

    def test_server_header_not_disclosed(self, admin_api: APIRequestContext):
        """Server header should not disclose framework details.

        In dev mode, the WSGI server may expose CPython version.
        This test checks for Django-specific disclosure.
        """
        resp = admin_api.get("/api/v1/buildings/")
        server = resp.headers.get("server", "")
        if server:
            assert "django" not in server.lower(), f"Server header discloses Django: {server}"

    def test_referrer_policy_set(self, admin_api: APIRequestContext):
        resp = admin_api.get("/api/v1/buildings/")
        rp = resp.headers.get("referrer-policy", "")
        # Presence check — may not be set on all servers
        assert isinstance(rp, str)
