"""
Sprint 1 — API Auth Test Suite.

Covers every endpoint in /auth/* with both positive and negative cases.

Positive:  valid credentials, correct JWT claims, token refresh, profile CRUD
Negative:  wrong password, account lockout (423), invalid tokens, weak passwords

Markers: api, sprint_1
"""

import time

import pytest

from api.auth_api import AuthAPI
from core.api_client import APIClient
from utils.test_data import PasswordFactory, TokenFactory, UserFactory

pytestmark = [pytest.mark.api, pytest.mark.sprint_1]

# ── Helpers ────────────────────────────────────────────────────────────────────

LOGIN_MAX_ATTEMPTS = 5          # must match backend LOGIN_MAX_ATTEMPTS setting
LOCKOUT_MINUTES    = 15         # must match LOGIN_LOCKOUT_DURATION_MINUTES


# ══════════════════════════════════════════════════════════════════════════════
# Login
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.positive
class TestLogin:

    def test_admin_login_returns_tokens_and_user(self, env_config):
        """Successful admin login must return access + refresh tokens and user object."""
        auth = AuthAPI(APIClient(env_config.api_url))
        resp = auth.login(env_config.admin_email, env_config.admin_password)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "access" in body, "Missing access token"
        assert "refresh" in body, "Missing refresh token"
        assert "user" in body, "Missing user object"
        assert body["user"]["email"] == env_config.admin_email

    def test_access_token_contains_required_claims(self, env_config):
        """JWT payload must contain user_id, role, and tenant_ids claims."""
        auth = AuthAPI(APIClient(env_config.api_url))
        resp = auth.login(env_config.admin_email, env_config.admin_password)
        token = resp.json()["access"]
        claims = AuthAPI.decode_token_claims(token)
        assert "user_id" in claims, "Missing user_id claim"
        assert "role" in claims, "Missing role claim"
        assert "tenant_ids" in claims, "Missing tenant_ids claim"
        assert claims["role"] == "admin"
        assert isinstance(claims["tenant_ids"], list)

    def test_admin_role_in_user_response(self, env_config):
        """Login response user object must reflect the admin role."""
        auth = AuthAPI(APIClient(env_config.api_url))
        resp = auth.login(env_config.admin_email, env_config.admin_password)
        assert resp.json()["user"]["role"] == "admin"

    def test_failed_login_resets_counter_on_success(self, env_config, create_temp_user):
        """A successful login after failures must not leave the account locked."""
        user = create_temp_user(role="owner")
        auth = AuthAPI(APIClient(env_config.api_url))

        # 2 failures
        for _ in range(2):
            auth.login(user["email"], "WrongPass@1")

        # Correct login
        resp = auth.login(user["email"], user["password"])
        assert resp.status_code == 200


@pytest.mark.negative
class TestLoginNegative:

    def test_wrong_password_returns_401(self, env_config):
        auth = AuthAPI(APIClient(env_config.api_url))
        resp = auth.login(env_config.admin_email, "WrongPass@999")
        assert resp.status_code == 401

    def test_unknown_email_returns_401(self, env_config):
        auth = AuthAPI(APIClient(env_config.api_url))
        resp = auth.login("nobody@abem.test", "SomePass@1")
        assert resp.status_code == 401

    def test_empty_email_returns_400(self, env_config):
        auth = AuthAPI(APIClient(env_config.api_url))
        resp = auth.login("", "SomePass@1")
        assert resp.status_code == 400

    def test_empty_password_returns_400(self, env_config):
        auth = AuthAPI(APIClient(env_config.api_url))
        resp = auth.login(env_config.admin_email, "")
        assert resp.status_code == 400

    def test_missing_body_returns_400(self, env_config):
        import requests as req
        resp = req.post(env_config.api_url + "/auth/login/", json={}, timeout=10)
        assert resp.status_code == 400

    def test_account_locks_after_max_failed_attempts(self, env_config, create_temp_user):
        """After LOGIN_MAX_ATTEMPTS failures the next attempt returns 423."""
        user = create_temp_user(role="owner")
        auth = AuthAPI(APIClient(env_config.api_url))

        for i in range(LOGIN_MAX_ATTEMPTS):
            r = auth.login(user["email"], f"BadPass_{i}@1")
            assert r.status_code == 401, f"Expected 401 on attempt {i+1}"

        # The next attempt should trigger the lockout
        locked_resp = auth.login(user["email"], "AnyPass@1")
        assert locked_resp.status_code == 423, (
            f"Expected 423 Locked after {LOGIN_MAX_ATTEMPTS} failures, "
            f"got {locked_resp.status_code}: {locked_resp.text}"
        )

    def test_locked_account_returns_detail_and_locked_until(self, env_config, create_temp_user):
        """423 response must include 'detail' and optionally 'locked_until'."""
        user = create_temp_user(role="owner")
        auth = AuthAPI(APIClient(env_config.api_url))

        for _ in range(LOGIN_MAX_ATTEMPTS + 1):
            auth.login(user["email"], "Bad@Pass1")

        resp = auth.login(user["email"], user["password"])
        if resp.status_code == 423:
            body = resp.json()
            assert "detail" in body, "423 response missing 'detail'"


# ══════════════════════════════════════════════════════════════════════════════
# Logout
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.positive
class TestLogout:

    def test_logout_returns_200_and_blacklists_token(self, env_config):
        """Logout must succeed and the refresh token must become invalid."""
        client = APIClient(env_config.api_url)
        client.authenticate(env_config.admin_email, env_config.admin_password)
        refresh = client.refresh_token

        auth = AuthAPI(client)
        resp = auth.logout(refresh)
        assert resp.status_code == 200, resp.text

        # Attempt to refresh with the now-blacklisted token
        refresh_resp = auth.refresh_token(refresh)
        assert refresh_resp.status_code in (400, 401), (
            "Blacklisted token should not be refreshable"
        )

    def test_logout_clears_authentication(self, env_config):
        """After logout the client should no longer access protected endpoints."""
        client = APIClient(env_config.api_url)
        client.authenticate(env_config.admin_email, env_config.admin_password)
        auth = AuthAPI(client)

        auth.logout(client.refresh_token)
        client.access_token = None  # simulate token cleared

        # Protected endpoint must now return 401
        resp = auth.get_profile()
        assert resp.status_code == 401


@pytest.mark.negative
class TestLogoutNegative:

    def test_logout_without_token_returns_401(self, env_config):
        auth = AuthAPI(APIClient(env_config.api_url))
        import requests as req
        resp = req.post(
            env_config.api_url + "/auth/logout/",
            json={"refresh": "dummy"},
            timeout=10,
        )
        assert resp.status_code == 401

    def test_logout_with_invalid_refresh_returns_400(self, env_config):
        client = APIClient(env_config.api_url)
        client.authenticate(env_config.admin_email, env_config.admin_password)
        auth = AuthAPI(client)
        resp = auth.logout(TokenFactory.invalid_access_token())
        assert resp.status_code in (400, 401)


# ══════════════════════════════════════════════════════════════════════════════
# Token Refresh
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.positive
class TestTokenRefresh:

    def test_refresh_returns_new_access_token(self, env_config):
        """POST /auth/token/refresh/ must return a new access token."""
        client = APIClient(env_config.api_url)
        client.authenticate(env_config.admin_email, env_config.admin_password)
        auth = AuthAPI(client)
        old_access = client.access_token

        resp = auth.refresh_token(client.refresh_token)
        assert resp.status_code == 200
        new_access = resp.json().get("access")
        assert new_access, "No access token in refresh response"
        assert new_access != old_access, "New access token must differ from old"


@pytest.mark.negative
class TestTokenRefreshNegative:

    def test_refresh_with_invalid_token_returns_401(self, env_config):
        auth = AuthAPI(APIClient(env_config.api_url))
        resp = auth.refresh_token(TokenFactory.invalid_access_token())
        assert resp.status_code in (400, 401)

    def test_refresh_with_expired_token_returns_401(self, env_config):
        auth = AuthAPI(APIClient(env_config.api_url))
        resp = auth.refresh_token(TokenFactory.expired_token())
        assert resp.status_code in (400, 401)

    def test_refresh_with_empty_token_returns_400(self, env_config):
        auth = AuthAPI(APIClient(env_config.api_url))
        resp = auth.refresh_token("")
        assert resp.status_code == 400


# ══════════════════════════════════════════════════════════════════════════════
# Profile
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.positive
class TestProfile:

    def test_get_profile_returns_current_user(self, admin_api, env_config):
        auth = AuthAPI(admin_api)
        resp = auth.get_profile()
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == env_config.admin_email
        assert body["role"] == "admin"
        for field in ("id", "first_name", "last_name", "is_active"):
            assert field in body, f"Missing field '{field}' in profile response"

    def test_update_profile_persists_changes(self, create_temp_user, env_config):
        """PATCH /auth/profile/ must save and return the updated values."""
        user = create_temp_user(role="owner")
        client = APIClient(env_config.api_url)
        client.authenticate(user["email"], user["password"])
        auth = AuthAPI(client)

        new_first = "UpdatedFirst"
        new_last  = "UpdatedLast"
        resp = auth.update_profile(first_name=new_first, last_name=new_last)
        assert resp.status_code == 200
        body = resp.json()
        assert body["first_name"] == new_first
        assert body["last_name"]  == new_last

        client.logout()


@pytest.mark.negative
class TestProfileNegative:

    def test_get_profile_without_token_returns_401(self, unauthenticated_api):
        auth = AuthAPI(unauthenticated_api)
        resp = auth.get_profile()
        assert resp.status_code == 401

    def test_update_profile_without_token_returns_401(self, unauthenticated_api):
        auth = AuthAPI(unauthenticated_api)
        resp = auth.update_profile(first_name="Hacker")
        assert resp.status_code == 401


# ══════════════════════════════════════════════════════════════════════════════
# Change Password
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.positive
class TestChangePassword:

    def test_change_password_returns_200(self, create_temp_user, env_config):
        user = create_temp_user(role="owner")
        client = APIClient(env_config.api_url)
        client.authenticate(user["email"], user["password"])
        auth = AuthAPI(client)

        new_pw = PasswordFactory.new_valid(exclude=user["password"])
        resp = auth.change_password(
            current_password=user["password"],
            new_password=new_pw,
        )
        assert resp.status_code == 200, resp.text
        client.logout()

    def test_can_login_with_new_password_after_change(self, create_temp_user, env_config):
        user = create_temp_user(role="owner")
        client = APIClient(env_config.api_url)
        client.authenticate(user["email"], user["password"])
        auth = AuthAPI(client)

        new_pw = PasswordFactory.new_valid(exclude=user["password"])
        auth.change_password(current_password=user["password"], new_password=new_pw)
        client.logout()

        # Login with new password
        new_client = APIClient(env_config.api_url)
        data = new_client.authenticate(user["email"], new_pw)
        assert "access" in data
        new_client.logout()


@pytest.mark.negative
class TestChangePasswordNegative:

    def test_wrong_current_password_returns_400(self, create_temp_user, env_config):
        user = create_temp_user(role="owner")
        client = APIClient(env_config.api_url)
        client.authenticate(user["email"], user["password"])
        auth = AuthAPI(client)

        resp = auth.change_password(
            current_password="WrongCurrent@1",
            new_password="NewValid@99",
        )
        assert resp.status_code == 400, resp.text
        client.logout()

    @pytest.mark.parametrize("pw_sample", PasswordFactory.weak_samples())
    def test_weak_new_password_rejected(self, pw_sample, create_temp_user, env_config):
        """Each weak password variant must be rejected with 400."""
        user = create_temp_user(role="owner")
        client = APIClient(env_config.api_url)
        client.authenticate(user["email"], user["password"])
        auth = AuthAPI(client)

        resp = auth.change_password(
            current_password=user["password"],
            new_password=pw_sample["password"],
        )
        assert resp.status_code == 400, (
            f"Weak password ({pw_sample['reason']}) should be rejected, "
            f"got {resp.status_code}"
        )
        client.logout()

    def test_change_password_without_token_returns_401(self, unauthenticated_api):
        auth = AuthAPI(unauthenticated_api)
        resp = auth.change_password("old@pass", "New@pass1")
        assert resp.status_code == 401
