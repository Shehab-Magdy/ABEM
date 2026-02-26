"""
Sprint 1 — Self-Registration API tests.

Covers POST /auth/self-register/ — the public, AllowAny endpoint that lets
anyone create an account and choose a role (admin | owner).

Positive:  both roles accepted, tokens returned, profile persisted
Negative:  duplicate email, password mismatch, weak password, invalid role

Markers: api, sprint_1
"""

import pytest

from api.auth_api import AuthAPI
from core.api_client import APIClient
from utils.test_data import PasswordFactory, UserFactory

pytestmark = [pytest.mark.api, pytest.mark.sprint_1]


# ══════════════════════════════════════════════════════════════════════════════
# Self-register — positive
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.positive
class TestSelfRegisterPositive:

    def test_self_register_as_owner_returns_201_with_tokens(self, env_config):
        """POST /auth/self-register/ with role='owner' → 201, access+refresh tokens."""
        data = UserFactory.owner()
        auth = AuthAPI(APIClient(env_config.api_url))
        resp = auth.self_register(
            email=data["email"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            role="owner",
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert "access" in body,  "Missing 'access' token in response"
        assert "refresh" in body, "Missing 'refresh' token in response"
        assert "user" in body,    "Missing 'user' object in response"

    def test_self_register_as_admin_returns_201_with_tokens(self, env_config):
        """POST /auth/self-register/ with role='admin' → 201, access+refresh tokens."""
        data = UserFactory.admin()
        auth = AuthAPI(APIClient(env_config.api_url))
        resp = auth.self_register(
            email=data["email"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            role="admin",
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert "access" in body
        assert "refresh" in body
        assert "user" in body

    def test_self_registered_owner_role_in_user_object(self, env_config):
        """User object in 201 response must reflect the requested role."""
        data = UserFactory.owner()
        auth = AuthAPI(APIClient(env_config.api_url))
        resp = auth.self_register(
            email=data["email"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            role="owner",
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["user"]["role"] == "owner"

    def test_self_registered_admin_role_in_user_object(self, env_config):
        """Admin role must be stored and returned correctly."""
        data = UserFactory.admin()
        auth = AuthAPI(APIClient(env_config.api_url))
        resp = auth.self_register(
            email=data["email"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            role="admin",
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["user"]["role"] == "admin"

    def test_self_registered_user_can_login_with_credentials(self, env_config):
        """After self-registration, user must be able to log in with their password."""
        data = UserFactory.owner()
        auth = AuthAPI(APIClient(env_config.api_url))
        auth.self_register(
            email=data["email"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            role="owner",
        )

        login_resp = auth.login(data["email"], data["password"])
        assert login_resp.status_code == 200, (
            f"Newly registered user must be able to log in, got {login_resp.status_code}"
        )

    def test_access_token_contains_correct_role_claim(self, env_config):
        """JWT 'role' claim must match the role chosen at registration."""
        data = UserFactory.owner()
        auth = AuthAPI(APIClient(env_config.api_url))
        resp = auth.self_register(
            email=data["email"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            role="owner",
        )
        assert resp.status_code == 201, resp.text
        claims = AuthAPI.decode_token_claims(resp.json()["access"])
        assert claims.get("role") == "owner", (
            f"JWT 'role' claim must be 'owner', got {claims.get('role')}"
        )

    def test_self_register_with_optional_phone(self, env_config):
        """Phone field is optional — request with phone must succeed."""
        data = UserFactory.owner()
        auth = AuthAPI(APIClient(env_config.api_url))
        resp = auth.self_register(
            email=data["email"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            role="owner",
            phone=data.get("phone", "+201234567890"),
        )
        assert resp.status_code == 201, resp.text


# ══════════════════════════════════════════════════════════════════════════════
# Self-register — negative
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.negative
class TestSelfRegisterNegative:

    def test_duplicate_email_returns_400(self, env_config):
        """Registering with an already-used email must return 400."""
        data = UserFactory.owner()
        auth = AuthAPI(APIClient(env_config.api_url))

        # First registration succeeds
        first = auth.self_register(
            email=data["email"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            role="owner",
        )
        assert first.status_code == 201, first.text

        # Second registration with same email must fail
        second = auth.self_register(
            email=data["email"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            role="owner",
        )
        assert second.status_code == 400, (
            f"Duplicate email must return 400, got {second.status_code}: {second.text}"
        )

    def test_password_mismatch_returns_400(self, env_config):
        """Mismatched password/confirm_password must return 400."""
        import requests as req
        data = UserFactory.owner()
        resp = req.post(
            env_config.api_url + "/auth/self-register/",
            json={
                "email": data["email"],
                "password": data["password"],
                "confirm_password": "Totally@Different9",
                "first_name": data["first_name"],
                "last_name": data["last_name"],
                "role": "owner",
            },
            timeout=10,
        )
        assert resp.status_code == 400, (
            f"Password mismatch must return 400, got {resp.status_code}: {resp.text}"
        )

    @pytest.mark.parametrize("pw_sample", PasswordFactory.weak_samples())
    def test_weak_password_rejected(self, pw_sample, env_config):
        """Each weak password variant must be rejected with 400."""
        import requests as req
        data = UserFactory.owner()
        resp = req.post(
            env_config.api_url + "/auth/self-register/",
            json={
                "email": data["email"],
                "password": pw_sample["password"],
                "confirm_password": pw_sample["password"],
                "first_name": data["first_name"],
                "last_name": data["last_name"],
                "role": "owner",
            },
            timeout=10,
        )
        assert resp.status_code == 400, (
            f"Weak password ({pw_sample['reason']}) must be rejected, "
            f"got {resp.status_code}: {resp.text}"
        )

    def test_invalid_role_returns_400(self, env_config):
        """role='superuser' (or any unrecognised value) must return 400."""
        import requests as req
        data = UserFactory.owner()
        resp = req.post(
            env_config.api_url + "/auth/self-register/",
            json={
                "email": data["email"],
                "password": data["password"],
                "confirm_password": data["password"],
                "first_name": data["first_name"],
                "last_name": data["last_name"],
                "role": "superuser",
            },
            timeout=10,
        )
        assert resp.status_code == 400, (
            f"Invalid role must return 400, got {resp.status_code}: {resp.text}"
        )

    def test_missing_required_fields_returns_400(self, env_config):
        """Empty body → 400 (all required fields missing)."""
        import requests as req
        resp = req.post(
            env_config.api_url + "/auth/self-register/",
            json={},
            timeout=10,
        )
        assert resp.status_code == 400, (
            f"Empty payload must return 400, got {resp.status_code}"
        )

    def test_self_register_does_not_require_authentication(self, env_config):
        """The endpoint is public — no prior auth token should be needed."""
        import requests as req
        data = UserFactory.owner()
        resp = req.post(
            env_config.api_url + "/auth/self-register/",
            json={
                "email": data["email"],
                "password": data["password"],
                "confirm_password": data["password"],
                "first_name": data["first_name"],
                "last_name": data["last_name"],
                "role": "owner",
            },
            timeout=10,
        )
        # 201 = success with no token in headers
        assert resp.status_code == 201, (
            f"Self-register must not require auth, got {resp.status_code}: {resp.text}"
        )
