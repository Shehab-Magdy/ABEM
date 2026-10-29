"""API tests for the token refresh endpoint."""

import pytest
from playwright.sync_api import APIRequestContext

from config.settings import settings
from utils.jwt_helpers import decode_token_unverified, get_token_role


@pytest.mark.api
@pytest.mark.auth
class TestTokenRefresh:
    """POST /api/v1/auth/refresh/ tests."""

    def _login(self, ctx: APIRequestContext) -> dict:
        resp = ctx.post(
            "/api/v1/auth/login/",
            data={"email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD},
        )
        assert resp.status == 200
        return resp.json()

    def test_refresh_with_valid_token(self, api_context: APIRequestContext):
        tokens = self._login(api_context)
        resp = api_context.post(
            "/api/v1/auth/refresh/",
            data={"refresh": tokens["refresh"]},
        )
        assert resp.status == 200
        body = resp.json()
        assert "access" in body

    def test_refresh_with_invalid_token(self, api_context: APIRequestContext):
        resp = api_context.post(
            "/api/v1/auth/refresh/",
            data={"refresh": "invalid.token.value"},
        )
        assert resp.status == 401

    def test_refresh_token_rotation(self, api_context: APIRequestContext):
        """After refresh, the old refresh token should be blacklisted."""
        tokens = self._login(api_context)
        old_refresh = tokens["refresh"]

        # First refresh succeeds
        resp1 = api_context.post(
            "/api/v1/auth/refresh/",
            data={"refresh": old_refresh},
        )
        assert resp1.status == 200

        # Reusing old refresh should fail (blacklisted)
        resp2 = api_context.post(
            "/api/v1/auth/refresh/",
            data={"refresh": old_refresh},
        )
        assert resp2.status == 401

    def test_refreshed_access_token_has_valid_claims(
        self, api_context: APIRequestContext
    ):
        tokens = self._login(api_context)
        resp = api_context.post(
            "/api/v1/auth/refresh/",
            data={"refresh": tokens["refresh"]},
        )
        new_access = resp.json()["access"]
        claims = decode_token_unverified(new_access)
        assert claims.get("role") == "admin"
        assert "user_id" in claims
        assert "exp" in claims
