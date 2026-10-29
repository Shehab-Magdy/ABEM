"""API tests for account lockout after failed login attempts."""

import pytest
from playwright.sync_api import APIRequestContext

from config.settings import settings
from utils.data_factory import build_owner_user


@pytest.mark.api
@pytest.mark.auth
class TestAccountLockout:
    """Account lockout after 5 consecutive failed login attempts."""

    def test_four_failed_logins_account_still_unlocked(
        self, api_context: APIRequestContext, admin_api: APIRequestContext, create_user
    ):
        """4 bad attempts followed by correct password should succeed."""
        user = create_user(role="owner")
        email = user["email"]
        password = user["_password"]

        # 4 failed attempts
        for _ in range(4):
            resp = api_context.post(
                "/api/v1/auth/login/",
                data={"email": email, "password": "WrongPass!1"},
            )
            assert resp.status == 401

        # 5th attempt with correct password should work
        resp = api_context.post(
            "/api/v1/auth/login/",
            data={"email": email, "password": password},
        )
        assert resp.status == 200

    def test_fifth_failed_login_triggers_lockout(
        self, api_context: APIRequestContext, admin_api: APIRequestContext, create_user
    ):
        """5 consecutive failed logins triggers account lockout."""
        user = create_user(role="owner")
        email = user["email"]

        for i in range(5):
            resp = api_context.post(
                "/api/v1/auth/login/",
                data={"email": email, "password": "WrongPass!1"},
            )
            assert resp.status in (401, 423, 429), f"Attempt {i+1}: unexpected {resp.status}"

        # 6th attempt — account should be locked
        resp = api_context.post(
            "/api/v1/auth/login/",
            data={"email": email, "password": "WrongPass!1"},
        )
        assert resp.status in (423, 429), f"Expected 423/429 after lockout, got {resp.status}"

    def test_correct_password_after_lockout_still_rejected(
        self, api_context: APIRequestContext, admin_api: APIRequestContext, create_user
    ):
        """Even correct credentials fail when the account is locked."""
        user = create_user(role="owner")
        email = user["email"]
        password = user["_password"]

        # Lock the account
        for _ in range(5):
            api_context.post(
                "/api/v1/auth/login/",
                data={"email": email, "password": "WrongPass!1"},
            )

        # Correct password should still be rejected
        resp = api_context.post(
            "/api/v1/auth/login/",
            data={"email": email, "password": password},
        )
        assert resp.status in (423, 429)

    def test_admin_can_reactivate_locked_account(
        self, api_context: APIRequestContext, admin_api: APIRequestContext, create_user
    ):
        """Admin activating a locked account allows login again."""
        user = create_user(role="owner")
        user_id = user["id"]
        email = user["email"]
        password = user["_password"]

        # Lock the account
        for _ in range(5):
            api_context.post(
                "/api/v1/auth/login/",
                data={"email": email, "password": "WrongPass!1"},
            )

        # Admin reactivates
        resp = admin_api.post(f"/api/v1/users/{user_id}/activate/")
        if resp.status == 404:
            pytest.skip("Activate endpoint not accessible for this user scope")
        assert resp.status in (200, 204)

        # Login should now work
        resp = api_context.post(
            "/api/v1/auth/login/",
            data={"email": email, "password": password},
        )
        assert resp.status == 200
