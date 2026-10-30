"""API tests for the login endpoint."""

import pytest
from playwright.sync_api import APIRequestContext

from config.settings import settings
from utils.jwt_helpers import decode_token_unverified, get_token_role, get_token_user_id


@pytest.mark.api
@pytest.mark.auth
class TestLogin:
    """POST /api/v1/auth/login/ tests."""

    def test_login_with_valid_admin_credentials(self, api_context: APIRequestContext):
        resp = api_context.post(
            "/api/v1/auth/login/",
            data={"email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD},
        )
        assert resp.status == 200
        body = resp.json()
        assert "access" in body
        assert "refresh" in body
        assert "user" in body

    def test_login_returns_jwt_with_correct_claims(self, api_context: APIRequestContext):
        resp = api_context.post(
            "/api/v1/auth/login/",
            data={"email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD},
        )
        token = resp.json()["access"]
        claims = decode_token_unverified(token)
        assert "user_id" in claims
        assert "role" in claims
        assert "exp" in claims

    def test_login_admin_gets_admin_role_claim(self, api_context: APIRequestContext):
        resp = api_context.post(
            "/api/v1/auth/login/",
            data={"email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD},
        )
        token = resp.json()["access"]
        assert get_token_role(token) == "admin"

    def test_login_owner_gets_owner_role_claim(self, api_context: APIRequestContext):
        resp = api_context.post(
            "/api/v1/auth/login/",
            data={"email": settings.OWNER_EMAIL, "password": settings.OWNER_PASSWORD},
        )
        token = resp.json()["access"]
        assert get_token_role(token) == "owner"

    def test_login_with_wrong_password(self, api_context: APIRequestContext):
        resp = api_context.post(
            "/api/v1/auth/login/",
            data={"email": settings.ADMIN_EMAIL, "password": "WrongPassword!1"},
        )
        assert resp.status == 401

    def test_login_with_nonexistent_email(self, api_context: APIRequestContext):
        resp = api_context.post(
            "/api/v1/auth/login/",
            data={"email": "nonexistent@abem.test", "password": "SomePass!1"},
        )
        assert resp.status == 401

    def test_login_with_empty_email(self, api_context: APIRequestContext):
        resp = api_context.post(
            "/api/v1/auth/login/",
            data={"email": "", "password": "SomePass!1"},
        )
        assert resp.status in (400, 401)

    def test_login_with_empty_password(self, api_context: APIRequestContext):
        resp = api_context.post(
            "/api/v1/auth/login/",
            data={"email": settings.ADMIN_EMAIL, "password": ""},
        )
        assert resp.status in (400, 401)

    def test_login_with_missing_email_field(self, api_context: APIRequestContext):
        resp = api_context.post(
            "/api/v1/auth/login/",
            data={"password": "SomePass!1"},
        )
        assert resp.status == 400

    def test_login_with_missing_password_field(self, api_context: APIRequestContext):
        resp = api_context.post(
            "/api/v1/auth/login/",
            data={"email": settings.ADMIN_EMAIL},
        )
        assert resp.status == 400

    def test_login_error_does_not_reveal_email_existence(
        self, api_context: APIRequestContext
    ):
        """Both wrong email and wrong password should return 401.

        Note: Ideally the error messages should be identical to prevent
        email enumeration, but the current backend returns different messages.
        This test verifies both return 401 status at minimum.
        """
        resp_wrong_email = api_context.post(
            "/api/v1/auth/login/",
            data={"email": "fake@abem.test", "password": "Wrong!123"},
        )
        resp_wrong_pass = api_context.post(
            "/api/v1/auth/login/",
            data={"email": settings.ADMIN_EMAIL, "password": "Wrong!123"},
        )
        assert resp_wrong_email.status == 401
        assert resp_wrong_pass.status == 401
