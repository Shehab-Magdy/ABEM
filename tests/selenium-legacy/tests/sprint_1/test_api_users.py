"""
Sprint 1 — API User Management Test Suite.

Covers every /users/* endpoint:
  - CRUD (list, get, create, update, delete)
  - Custom actions (deactivate, activate, reset-password)
  - RBAC enforcement (admin-only access)
  - Filtering, search, and pagination

Markers: api, sprint_1
"""

import pytest

from api.auth_api import AuthAPI
from api.user_api import UserAPI
from core.api_client import APIClient
from utils.test_data import PasswordFactory, UserFactory

pytestmark = [pytest.mark.api, pytest.mark.sprint_1]


# ══════════════════════════════════════════════════════════════════════════════
# List Users
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.positive
class TestListUsers:

    def test_admin_can_list_users(self, admin_api):
        user_api = UserAPI(admin_api)
        resp = user_api.list_users()
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "count" in body
        assert "results" in body
        assert isinstance(body["results"], list)

    def test_list_returns_at_least_one_user(self, admin_api):
        """The admin user itself must always appear in the list."""
        user_api = UserAPI(admin_api)
        users = user_api.list_all()
        assert len(users) >= 1

    def test_filter_by_role_admin(self, admin_api):
        user_api = UserAPI(admin_api)
        resp = user_api.list_users(role="admin")
        assert resp.status_code == 200
        for user in resp.json()["results"]:
            assert user["role"] == "admin", f"Non-admin user in filtered result: {user}"

    def test_filter_by_role_owner(self, admin_api, create_temp_user):
        create_temp_user(role="owner")
        user_api = UserAPI(admin_api)
        resp = user_api.list_users(role="owner")
        assert resp.status_code == 200
        for user in resp.json()["results"]:
            assert user["role"] == "owner"

    def test_search_by_email(self, admin_api, env_config):
        user_api = UserAPI(admin_api)
        # Search for the known admin email (partial match)
        partial = env_config.admin_email.split("@")[0]
        resp = user_api.list_users(search=partial)
        assert resp.status_code == 200
        emails = [u["email"] for u in resp.json()["results"]]
        assert any(env_config.admin_email in e for e in emails), (
            f"Admin email not found in search results for '{partial}': {emails}"
        )

    def test_pagination_respected(self, admin_api):
        user_api = UserAPI(admin_api)
        resp = user_api.list_users(page=1, page_size=1)
        assert resp.status_code == 200
        assert len(resp.json()["results"]) <= 1

    def test_filter_active_users(self, admin_api):
        user_api = UserAPI(admin_api)
        resp = user_api.list_users(is_active=True)
        assert resp.status_code == 200
        for user in resp.json()["results"]:
            assert user["is_active"] is True


@pytest.mark.negative
class TestListUsersNegative:

    def test_owner_cannot_list_users(self, owner_api):
        user_api = UserAPI(owner_api)
        resp = user_api.list_users()
        assert resp.status_code == 403, (
            f"Owner should not be able to list users, got {resp.status_code}"
        )

    def test_unauthenticated_cannot_list_users(self, unauthenticated_api):
        user_api = UserAPI(unauthenticated_api)
        resp = user_api.list_users()
        assert resp.status_code == 401


# ══════════════════════════════════════════════════════════════════════════════
# Get Single User
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.positive
class TestGetUser:

    def test_admin_can_get_user_by_id(self, admin_api, env_config):
        """Admin can retrieve their own profile via /users/{id}/."""
        auth = AuthAPI(admin_api)
        profile = auth.get_profile().json()
        user_id = profile["id"]

        user_api = UserAPI(admin_api)
        resp = user_api.get_user(user_id)
        assert resp.status_code == 200
        assert resp.json()["id"] == user_id


@pytest.mark.negative
class TestGetUserNegative:

    def test_get_nonexistent_user_returns_404(self, admin_api):
        user_api = UserAPI(admin_api)
        resp = user_api.get_user("00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    def test_owner_cannot_get_arbitrary_user(self, owner_api, admin_api):
        auth = AuthAPI(admin_api)
        admin_id = auth.get_profile().json()["id"]
        user_api = UserAPI(owner_api)
        resp = user_api.get_user(admin_id)
        assert resp.status_code == 403


# ══════════════════════════════════════════════════════════════════════════════
# Create User
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.positive
class TestCreateUser:

    def test_admin_can_create_owner(self, admin_api):
        user_api = UserAPI(admin_api)
        data = UserFactory.owner()
        resp = user_api.create_user(**{k: data[k] for k in ["email", "password", "first_name", "last_name", "role"]})
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["email"] == data["email"]
        assert body["role"] == "owner"
        assert "id" in body

        # Cleanup
        user_api.delete_user(body["id"])

    def test_admin_can_create_another_admin(self, admin_api):
        user_api = UserAPI(admin_api)
        data = UserFactory.admin()
        resp = user_api.create_user(**{k: data[k] for k in ["email", "password", "first_name", "last_name", "role"]})
        assert resp.status_code == 201
        assert resp.json()["role"] == "admin"
        user_api.delete_user(resp.json()["id"])

    def test_created_user_can_login(self, admin_api, env_config):
        user_api = UserAPI(admin_api)
        data = UserFactory.owner()
        resp = user_api.create_user(**{k: data[k] for k in ["email", "password", "first_name", "last_name", "role"]})
        user_id = resp.json()["id"]

        new_client = APIClient(env_config.api_url)
        login_data = new_client.authenticate(data["email"], data["password"])
        assert "access" in login_data
        new_client.logout()

        user_api.delete_user(user_id)


@pytest.mark.negative
class TestCreateUserNegative:

    def test_owner_cannot_create_user(self, owner_api):
        user_api = UserAPI(owner_api)
        data = UserFactory.owner()
        resp = user_api.create_user(**{k: data[k] for k in ["email", "password", "first_name", "last_name", "role"]})
        assert resp.status_code == 403

    def test_duplicate_email_returns_400(self, admin_api, env_config):
        user_api = UserAPI(admin_api)
        data = UserFactory.owner()
        # First creation
        r1 = user_api.create_user(**{k: data[k] for k in ["email", "password", "first_name", "last_name", "role"]})
        assert r1.status_code == 201
        uid = r1.json()["id"]

        # Duplicate
        r2 = user_api.create_user(**{k: data[k] for k in ["email", "password", "first_name", "last_name", "role"]})
        assert r2.status_code == 400, "Duplicate email should return 400"
        user_api.delete_user(uid)

    @pytest.mark.parametrize("pw", [s["password"] for s in PasswordFactory.weak_samples()])
    def test_weak_password_rejected_on_create(self, pw, admin_api):
        user_api = UserAPI(admin_api)
        data = UserFactory.owner()
        data["password"] = pw
        resp = user_api.create_user(**{k: data[k] for k in ["email", "password", "first_name", "last_name", "role"]})
        assert resp.status_code == 400, (
            f"Weak password '{pw}' should be rejected, got {resp.status_code}"
        )

    def test_missing_email_returns_400(self, admin_api):
        user_api = UserAPI(admin_api)
        resp = user_api.create_user(
            email="",
            password="Valid@1234",
            first_name="Test",
            last_name="User",
            role="owner",
        )
        assert resp.status_code == 400

    def test_invalid_role_returns_400(self, admin_api):
        user_api = UserAPI(admin_api)
        data = UserFactory.owner()
        data["role"] = "superuser"
        resp = user_api.create_user(**{k: data[k] for k in ["email", "password", "first_name", "last_name", "role"]})
        assert resp.status_code == 400


# ══════════════════════════════════════════════════════════════════════════════
# Update User
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.positive
class TestUpdateUser:

    def test_admin_can_update_user_name(self, admin_api, create_temp_user):
        user = create_temp_user(role="owner")
        user_api = UserAPI(admin_api)
        resp = user_api.update_user(user["id"], first_name="Renamed", last_name="Person")
        assert resp.status_code == 200
        body = resp.json()
        assert body["first_name"] == "Renamed"
        assert body["last_name"] == "Person"


# ══════════════════════════════════════════════════════════════════════════════
# Deactivate / Activate
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.positive
class TestDeactivateActivate:

    def test_admin_can_deactivate_user(self, admin_api, create_temp_user):
        user = create_temp_user(role="owner")
        user_api = UserAPI(admin_api)

        resp = user_api.deactivate_user(user["id"])
        assert resp.status_code == 200

        # Confirm is_active is False
        get_resp = user_api.get_user(user["id"])
        assert get_resp.json()["is_active"] is False

    def test_admin_can_activate_deactivated_user(self, admin_api, create_temp_user):
        user = create_temp_user(role="owner")
        user_api = UserAPI(admin_api)
        user_api.deactivate_user(user["id"])

        resp = user_api.activate_user(user["id"])
        assert resp.status_code == 200
        assert user_api.get_user(user["id"]).json()["is_active"] is True

    def test_deactivated_user_cannot_login(self, admin_api, create_temp_user, env_config):
        user = create_temp_user(role="owner")
        UserAPI(admin_api).deactivate_user(user["id"])

        import requests as req
        resp = req.post(
            env_config.api_url + "/auth/login/",
            json={"email": user["email"], "password": user["password"]},
            timeout=10,
        )
        assert resp.status_code in (401, 403), (
            f"Deactivated user should not login, got {resp.status_code}"
        )


@pytest.mark.negative
class TestDeactivateNegative:

    def test_admin_cannot_deactivate_self(self, admin_api, env_config):
        """Self-deactivation must return 400 per backend guard."""
        auth = AuthAPI(admin_api)
        admin_id = auth.get_profile().json()["id"]
        user_api = UserAPI(admin_api)
        resp = user_api.deactivate_user(admin_id)
        assert resp.status_code == 400, (
            f"Admin deactivating self should return 400, got {resp.status_code}: {resp.text}"
        )

    def test_owner_cannot_deactivate_user(self, owner_api, create_temp_user):
        user = create_temp_user(role="owner")
        user_api = UserAPI(owner_api)
        resp = user_api.deactivate_user(user["id"])
        assert resp.status_code == 403

    def test_deactivate_nonexistent_user_returns_404(self, admin_api):
        user_api = UserAPI(admin_api)
        resp = user_api.deactivate_user("00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# Reset Password
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.positive
class TestResetPassword:

    def test_admin_can_reset_user_password(self, admin_api, create_temp_user, env_config):
        user = create_temp_user(role="owner")
        user_api = UserAPI(admin_api)
        new_pw = "ResetPass@99"

        resp = user_api.reset_password(user["id"], new_pw)
        assert resp.status_code == 200, resp.text

        # Verify new password works
        new_client = APIClient(env_config.api_url)
        data = new_client.authenticate(user["email"], new_pw)
        assert "access" in data
        new_client.logout()


@pytest.mark.negative
class TestResetPasswordNegative:

    def test_owner_cannot_reset_another_users_password(self, owner_api, create_temp_user):
        user = create_temp_user(role="owner")
        user_api = UserAPI(owner_api)
        resp = user_api.reset_password(user["id"], "NewPass@99")
        assert resp.status_code == 403

    @pytest.mark.parametrize("pw", [s["password"] for s in PasswordFactory.weak_samples()])
    def test_weak_reset_password_rejected(self, pw, admin_api, create_temp_user):
        user = create_temp_user(role="owner")
        user_api = UserAPI(admin_api)
        resp = user_api.reset_password(user["id"], pw)
        assert resp.status_code == 400, (
            f"Weak reset password '{pw}' should be rejected, got {resp.status_code}"
        )
