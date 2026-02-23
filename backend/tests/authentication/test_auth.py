"""
Sprint 1 – Authentication tests.
Covers: login, lockout, logout, register, change-password, profile.
"""
import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

LOGIN_URL = "/api/v1/auth/login/"
LOGOUT_URL = "/api/v1/auth/logout/"
REGISTER_URL = "/api/v1/auth/register/"
CHANGE_PASSWORD_URL = "/api/v1/auth/change-password/"
PROFILE_URL = "/api/v1/auth/profile/"


# ── Login ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLogin:
    def test_login_success_returns_tokens_and_user(self, api_client, admin_user):
        response = api_client.post(LOGIN_URL, {"email": admin_user.email, "password": "AdminPass1!"})
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["user"]["email"] == admin_user.email

    def test_login_wrong_password_returns_401(self, api_client, admin_user):
        response = api_client.post(LOGIN_URL, {"email": admin_user.email, "password": "WrongPass!"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_unknown_email_returns_401(self, api_client):
        response = api_client.post(LOGIN_URL, {"email": "nobody@abem.test", "password": "Pass1!"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_increments_failed_attempts(self, api_client, admin_user):
        api_client.post(LOGIN_URL, {"email": admin_user.email, "password": "WrongPass!"})
        admin_user.refresh_from_db()
        assert admin_user.failed_login_attempts == 1

    def test_account_locks_after_5_failed_attempts(self, api_client, admin_user):
        for _ in range(5):
            api_client.post(LOGIN_URL, {"email": admin_user.email, "password": "WrongPass!"})
        admin_user.refresh_from_db()
        assert admin_user.is_locked is True
        assert admin_user.locked_until is not None

    def test_locked_account_returns_423(self, api_client, admin_user):
        admin_user.locked_until = timezone.now() + timedelta(minutes=15)
        admin_user.save()
        response = api_client.post(LOGIN_URL, {"email": admin_user.email, "password": "AdminPass1!"})
        assert response.status_code == status.HTTP_423_LOCKED
        assert "locked_until" in response.data

    def test_inactive_user_returns_403(self, api_client, admin_user):
        admin_user.is_active = False
        admin_user.save()
        response = api_client.post(LOGIN_URL, {"email": admin_user.email, "password": "AdminPass1!"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_successful_login_resets_failed_attempts(self, api_client, admin_user):
        admin_user.failed_login_attempts = 3
        admin_user.save()
        api_client.post(LOGIN_URL, {"email": admin_user.email, "password": "AdminPass1!"})
        admin_user.refresh_from_db()
        assert admin_user.failed_login_attempts == 0

    def test_login_missing_fields_returns_400(self, api_client):
        response = api_client.post(LOGIN_URL, {"email": "test@abem.test"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── Logout ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLogout:
    def test_logout_blacklists_refresh_token(self, admin_client, admin_user):
        refresh = str(RefreshToken.for_user(admin_user))
        response = admin_client.post(LOGOUT_URL, {"refresh": refresh})
        assert response.status_code == status.HTTP_200_OK

    def test_logout_without_refresh_token_returns_400(self, admin_client):
        response = admin_client.post(LOGOUT_URL, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_logout_requires_authentication(self, api_client, admin_user):
        refresh = str(RefreshToken.for_user(admin_user))
        response = api_client.post(LOGOUT_URL, {"refresh": refresh})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_double_logout_returns_400(self, admin_client, admin_user):
        refresh = str(RefreshToken.for_user(admin_user))
        admin_client.post(LOGOUT_URL, {"refresh": refresh})
        response = admin_client.post(LOGOUT_URL, {"refresh": refresh})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── Register ──────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRegister:
    def test_admin_can_create_user(self, admin_client):
        response = admin_client.post(REGISTER_URL, {
            "email": "new@abem.test",
            "first_name": "New",
            "last_name": "User",
            "role": "owner",
            "password": "NewPass1!",
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email="new@abem.test").exists()

    def test_owner_cannot_register_users(self, owner_client):
        response = owner_client.post(REGISTER_URL, {
            "email": "new2@abem.test",
            "password": "NewPass1!",
            "first_name": "New",
            "last_name": "User",
            "role": "owner",
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_duplicate_email_returns_400(self, admin_client, admin_user):
        response = admin_client.post(REGISTER_URL, {
            "email": admin_user.email,
            "password": "NewPass1!",
            "first_name": "Dup",
            "last_name": "User",
            "role": "owner",
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_weak_password_rejected(self, admin_client):
        response = admin_client.post(REGISTER_URL, {
            "email": "weak@abem.test",
            "password": "password",  # no uppercase, no digit, no special
            "first_name": "Weak",
            "last_name": "Pass",
            "role": "owner",
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── Change Password ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestChangePassword:
    def test_change_password_success(self, admin_client, admin_user):
        response = admin_client.patch(CHANGE_PASSWORD_URL, {
            "current_password": "AdminPass1!",
            "new_password": "NewAdmin2@",
            "confirm_password": "NewAdmin2@",
        })
        assert response.status_code == status.HTTP_200_OK
        admin_user.refresh_from_db()
        assert admin_user.check_password("NewAdmin2@")

    def test_wrong_current_password_rejected(self, admin_client):
        response = admin_client.patch(CHANGE_PASSWORD_URL, {
            "current_password": "WrongPass!",
            "new_password": "NewAdmin2@",
            "confirm_password": "NewAdmin2@",
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_mismatched_confirm_password_rejected(self, admin_client):
        response = admin_client.patch(CHANGE_PASSWORD_URL, {
            "current_password": "AdminPass1!",
            "new_password": "NewAdmin2@",
            "confirm_password": "DifferentPass1!",
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── Profile ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProfile:
    def test_get_profile_returns_user_data(self, admin_client, admin_user):
        response = admin_client.get(PROFILE_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == admin_user.email

    def test_update_profile_success(self, admin_client, admin_user):
        response = admin_client.patch(PROFILE_URL, {"first_name": "Updated"})
        assert response.status_code == status.HTTP_200_OK
        admin_user.refresh_from_db()
        assert admin_user.first_name == "Updated"

    def test_unauthenticated_profile_returns_401(self, api_client):
        response = api_client.get(PROFILE_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ── User Management (Admin) ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestUserManagement:
    USERS_URL = "/api/v1/users/"

    def test_admin_can_list_users(self, admin_client, admin_user, owner_user):
        response = admin_client.get(self.USERS_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 2

    def test_owner_cannot_list_users(self, owner_client):
        response = owner_client.get(self.USERS_URL)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_deactivate_user(self, admin_client, owner_user):
        response = admin_client.post(f"{self.USERS_URL}{owner_user.id}/deactivate/")
        assert response.status_code == status.HTTP_200_OK
        owner_user.refresh_from_db()
        assert owner_user.is_active is False

    def test_admin_cannot_deactivate_self(self, admin_client, admin_user):
        response = admin_client.post(f"{self.USERS_URL}{admin_user.id}/deactivate/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_admin_can_activate_user(self, admin_client, owner_user):
        owner_user.is_active = False
        owner_user.save()
        response = admin_client.post(f"{self.USERS_URL}{owner_user.id}/activate/")
        assert response.status_code == status.HTTP_200_OK
        owner_user.refresh_from_db()
        assert owner_user.is_active is True

    def test_admin_can_reset_user_password(self, admin_client, owner_user):
        response = admin_client.post(
            f"{self.USERS_URL}{owner_user.id}/reset-password/",
            {"new_password": "NewOwner2!", "confirm_password": "NewOwner2!"},
        )
        assert response.status_code == status.HTTP_200_OK
        owner_user.refresh_from_db()
        assert owner_user.check_password("NewOwner2!")
