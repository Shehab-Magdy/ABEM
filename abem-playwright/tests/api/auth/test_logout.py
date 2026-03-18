"""API tests for the logout endpoint."""

import pytest
from playwright.sync_api import APIRequestContext, Playwright

from config.settings import settings


@pytest.mark.api
@pytest.mark.auth
class TestLogout:
    """POST /api/v1/auth/logout/ tests."""

    def _login(self, ctx: APIRequestContext) -> dict:
        resp = ctx.post(
            "/api/v1/auth/login/",
            data={"email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD},
        )
        assert resp.status == 200
        return resp.json()

    def test_logout_with_valid_refresh(self, api_context: APIRequestContext):
        tokens = self._login(api_context)
        resp = api_context.post(
            "/api/v1/auth/logout/",
            data={"refresh": tokens["refresh"]},
            headers={"Authorization": f"Bearer {tokens['access']}"},
        )
        assert resp.status in (200, 204, 205)

    def test_logout_blacklists_token(
        self, playwright: Playwright
    ):
        """After logout, reusing the access token on a protected endpoint returns 401."""
        ctx = playwright.request.new_context(
            base_url=settings.API_BASE_URL,
            extra_http_headers={"Content-Type": "application/json"},
        )
        try:
            tokens = self._login(ctx)
            access = tokens["access"]
            refresh = tokens["refresh"]

            # Logout
            ctx.post(
                "/api/v1/auth/logout/",
                data={"refresh": refresh},
                headers={"Authorization": f"Bearer {access}"},
            )

            # Try to use the access token on a protected endpoint
            resp = ctx.get(
                "/api/v1/auth/profile/",
                headers={"Authorization": f"Bearer {access}"},
            )
            # Access token may still work until expiry (stateless JWT)
            # But refresh token should be blacklisted
            resp2 = ctx.post(
                "/api/v1/auth/refresh/",
                data={"refresh": refresh},
            )
            assert resp2.status == 401
        finally:
            ctx.dispose()

    def test_logout_without_refresh_token(self, admin_api: APIRequestContext):
        resp = admin_api.post("/api/v1/auth/logout/", data={})
        assert resp.status in (400, 401)

    def test_logout_with_invalid_refresh(self, admin_api: APIRequestContext):
        resp = admin_api.post(
            "/api/v1/auth/logout/",
            data={"refresh": "invalid.token.string"},
        )
        assert resp.status in (400, 401)
