"""
Authentication tests: email OTP sign-in, Google Sign-In, cookie-based refresh
(rotation + reuse detection + trusted-device bypass), logout, register, profile.

Note: OTP codes are generated with `apps.authentication.otp.generate_otp_code`
patched to a fixed value rather than parsed out of the sent email. Rendering
emails/otp_*.html via the Django test client crashes on this environment
(Python 3.14 + Django 4.2's `BaseContext.__copy__` does `copy(super())`,
which Python 3.14 no longer supports) - a pre-existing interpreter/framework
incompatibility unrelated to this feature (verified independently: the exact
same render_to_string call succeeds outside of the pytest test-client
instrumentation). Patching the code generator sidesteps that broken path
while still exercising the real OTP create/verify/consume logic.
"""

import importlib
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.apps import apps as django_apps
from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.core.cache import cache, caches
from django.core.cache.backends.db import DatabaseCache
from django.utils import timezone
from rest_framework import status
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.cookies import REFRESH_COOKIE_NAME, TRUSTED_DEVICE_COOKIE_NAME
from apps.authentication.device import (
    client_ip_from_request,
    device_label_from_user_agent,
)
from apps.authentication.models import EmailOTP, TrustedDevice, UserSession
from apps.authentication.otp import OTP_EXPIRED, OTP_NOT_FOUND, verify_otp_for_user
from apps.authentication.tokens import CustomRefreshToken

User = get_user_model()


@pytest.fixture(autouse=True)
def _clear_ratelimit_cache(db):
    """
    django_ratelimit counters live in CACHES["ratelimit"] (a DB-backed
    cache, so counters are shared across worker processes in production -
    see RATELIMIT_USE_CACHE in config/settings/base.py), keyed on email+IP -
    clear it so one test's otp/request calls never count against another
    test reusing the same fixture email (e.g. owner@abem.test).

    Depends on the `db` fixture (rather than requiring every test in this
    module to carry @pytest.mark.django_db individually) purely so this
    autouse fixture - which must query the DB-backed cache table - is
    allowed to touch the database at all; pure unit tests in this module
    (e.g. TestDeviceLabelFromUserAgent) don't otherwise need a database.
    """
    cache.clear()
    caches["ratelimit"].clear()
    yield


OTP_REQUEST_URL = "/api/v1/auth/otp/request/"
OTP_VERIFY_URL = "/api/v1/auth/otp/verify/"
GOOGLE_URL = "/api/v1/auth/google/"
REFRESH_URL = "/api/v1/auth/refresh/"
LOGOUT_URL = "/api/v1/auth/logout/"
REVOKE_ALL_URL = "/api/v1/auth/devices/revoke-all/"
REGISTER_URL = "/api/v1/auth/register/"
PROFILE_URL = "/api/v1/auth/profile/"

FIXED_CODE = "123456"


def _request_otp(client, email):
    """POST otp/request/ with the OTP code generator patched to FIXED_CODE."""
    with patch("apps.authentication.otp.generate_otp_code", return_value=FIXED_CODE):
        return client.post(OTP_REQUEST_URL, {"email": email})


def _sign_in(client, email, user_agent=None):
    """Sign in via OTP, set the client's Bearer credentials, and return the user."""
    _request_otp(client, email)
    extra = {"HTTP_USER_AGENT": user_agent} if user_agent else {}
    response = client.post(
        OTP_VERIFY_URL, {"email": email, "code": FIXED_CODE}, **extra
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return User.objects.get(email=email)


# ── OTP request ───────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestOTPRequest:
    def test_request_creates_pending_user_and_an_otp_row(self, api_client):
        response = _request_otp(api_client, "new@abem.test")
        assert response.status_code == status.HTTP_200_OK
        user = User.objects.get(email="new@abem.test")
        assert not user.has_usable_password()
        assert EmailOTP.objects.filter(user=user).exists()

    def test_request_for_existing_user_sends_a_new_code(self, api_client, owner_user):
        response = _request_otp(api_client, owner_user.email)
        assert response.status_code == status.HTTP_200_OK
        assert EmailOTP.objects.filter(user=owner_user).exists()

    def test_request_missing_email_returns_400(self, api_client):
        response = api_client.post(OTP_REQUEST_URL, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_deactivated_user_cannot_request_a_code(self, api_client, owner_user):
        owner_user.is_active = False
        owner_user.save()
        response = _request_otp(api_client, owner_user.email)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_rate_limited_after_too_many_requests(self, api_client):
        email = "ratelimited@abem.test"
        for _ in range(5):
            _request_otp(api_client, email)
        response = _request_otp(api_client, email)
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_ratelimit_cache_is_db_backed_not_per_process_locmem(self):
        """
        Bug fix: django_ratelimit used to count against CACHES["default"]
        (LocMemCache), which is per-process - with N gunicorn workers the
        real rate becomes ~5*N/m instead of 5/m. RATELIMIT_USE_CACHE must
        point at a DB-backed (process-shared) cache alias instead.
        """
        assert django_settings.RATELIMIT_USE_CACHE == "ratelimit"
        assert isinstance(caches["ratelimit"], DatabaseCache)
        assert (
            django_settings.CACHES["ratelimit"]["LOCATION"] == "ratelimit_cache_table"
        )

    def test_trusted_device_cookie_bypasses_the_code_step(self, api_client):
        email = "trusted@abem.test"
        _request_otp(api_client, email)
        verify = api_client.post(OTP_VERIFY_URL, {"email": email, "code": FIXED_CODE})
        assert verify.status_code == status.HTTP_200_OK
        assert TRUSTED_DEVICE_COOKIE_NAME in api_client.cookies

        otp_count_before = EmailOTP.objects.filter(user__email=email).count()
        bypass = api_client.post(OTP_REQUEST_URL, {"email": email})
        assert bypass.status_code == status.HTTP_200_OK
        assert "access" in bypass.data
        assert bypass.data["user"]["email"] == email
        # no new code was generated for the bypass path
        assert EmailOTP.objects.filter(user__email=email).count() == otp_count_before


# ── OTP verify ────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestOTPVerify:
    def test_verify_success_returns_tokens_and_sets_cookies(self, api_client):
        email = "verify@abem.test"
        _request_otp(api_client, email)

        response = api_client.post(OTP_VERIFY_URL, {"email": email, "code": FIXED_CODE})
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert response.data["user"]["email"] == email
        assert REFRESH_COOKIE_NAME in api_client.cookies
        assert TRUSTED_DEVICE_COOKIE_NAME in api_client.cookies
        assert not EmailOTP.objects.filter(user__email=email).exists()

    def test_wrong_code_is_rejected_and_increments_attempts(self, api_client):
        email = "wrongcode@abem.test"
        _request_otp(api_client, email)

        response = api_client.post(OTP_VERIFY_URL, {"email": email, "code": "000000"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        otp = EmailOTP.objects.get(user__email=email)
        assert otp.attempts == 1

    def test_too_many_wrong_attempts_burns_the_code(self, api_client, settings):
        settings.OTP_MAX_ATTEMPTS = 3
        email = "maxattempts@abem.test"
        _request_otp(api_client, email)

        response = None
        for _ in range(3):
            response = api_client.post(
                OTP_VERIFY_URL, {"email": email, "code": "000000"}
            )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert not EmailOTP.objects.filter(user__email=email).exists()

    def test_unknown_email_returns_400(self, api_client):
        response = api_client.post(
            OTP_VERIFY_URL, {"email": "nobody@abem.test", "code": "123456"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_expired_code_is_rejected(self, api_client):
        email = "expired@abem.test"
        _request_otp(api_client, email)
        EmailOTP.objects.filter(user__email=email).update(
            expires_at=timezone.now() - timedelta(minutes=1)
        )

        response = api_client.post(OTP_VERIFY_URL, {"email": email, "code": FIXED_CODE})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Bug fix: an expired code must be reported as OTP_EXPIRED, not
        # OTP_NOT_FOUND - the row exists, it's just past expires_at.
        assert response.data["code"] == OTP_EXPIRED

    def test_expired_code_is_distinguished_from_no_code_at_all(self, owner_user):
        # No OTP row at all -> not_found.
        assert verify_otp_for_user(owner_user, "123456") == OTP_NOT_FOUND

        EmailOTP.objects.create(
            user=owner_user,
            code_hash="irrelevant",
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        # A row exists but is expired -> expired, never not_found.
        assert verify_otp_for_user(owner_user, "123456") == OTP_EXPIRED

    def test_deactivated_user_cannot_verify(self, api_client, owner_user):
        owner_user.is_active = False
        owner_user.save()
        response = api_client.post(
            OTP_VERIFY_URL, {"email": owner_user.email, "code": "123456"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_verify_is_rate_limited_regardless_of_right_or_wrong_codes(
        self, api_client, settings
    ):
        """
        otp/verify/ must itself be throttled (10/m per email) - otherwise a
        caller can request a fresh code (otp/request/'s own 5/m limit)
        to get a fresh 5-wrong-attempts budget indefinitely, bypassing the
        per-code attempt burn. Set OTP_MAX_ATTEMPTS high so the per-code
        burn doesn't fire first and mask the rate limit under test.
        """
        settings.OTP_MAX_ATTEMPTS = 20
        email = "verifyratelimited@abem.test"
        _request_otp(api_client, email)

        response = None
        for _ in range(10):
            response = api_client.post(
                OTP_VERIFY_URL, {"email": email, "code": "000000"}
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST
        # 11th request within the window is throttled, independent of the
        # (still wrong) code supplied.
        response = api_client.post(OTP_VERIFY_URL, {"email": email, "code": "000000"})
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_correct_code_still_succeeds_within_the_rate_limit_window(
        self, api_client, settings
    ):
        """The limiter counts request volume only - a correct code on, say,
        the 6th request in the window must still succeed."""
        settings.OTP_MAX_ATTEMPTS = 20
        email = "verifysucceedsafterretries@abem.test"
        _request_otp(api_client, email)

        for _ in range(5):
            response = api_client.post(
                OTP_VERIFY_URL, {"email": email, "code": "000000"}
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST

        response = api_client.post(OTP_VERIFY_URL, {"email": email, "code": FIXED_CODE})
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data


# ── Google Sign-In ──────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestGoogleSignIn:
    def test_new_user_is_created_and_signed_in(self, api_client, settings):
        settings.GOOGLE_CLIENT_ID = "test-client-id"
        with patch(
            "apps.authentication.views.google_id_token.verify_oauth2_token"
        ) as verify:
            verify.return_value = {
                "email": "googleuser@abem.test",
                "email_verified": True,
                "given_name": "Google",
                "family_name": "User",
            }
            response = api_client.post(GOOGLE_URL, {"id_token": "fake"})
        assert response.status_code == status.HTTP_200_OK
        assert User.objects.filter(email="googleuser@abem.test").exists()
        assert REFRESH_COOKIE_NAME in api_client.cookies

    def test_auto_links_an_existing_account_by_email(
        self, api_client, settings, owner_user
    ):
        settings.GOOGLE_CLIENT_ID = "test-client-id"
        with patch(
            "apps.authentication.views.google_id_token.verify_oauth2_token"
        ) as verify:
            verify.return_value = {"email": owner_user.email, "email_verified": True}
            response = api_client.post(GOOGLE_URL, {"id_token": "fake"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["user"]["id"] == str(owner_user.id)
        assert User.objects.filter(email=owner_user.email).count() == 1

    def test_invalid_token_returns_401(self, api_client, settings):
        settings.GOOGLE_CLIENT_ID = "test-client-id"
        with patch(
            "apps.authentication.views.google_id_token.verify_oauth2_token"
        ) as verify:
            verify.side_effect = ValueError("bad token")
            response = api_client.post(GOOGLE_URL, {"id_token": "fake"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_not_configured_returns_400(self, api_client, settings):
        settings.GOOGLE_CLIENT_ID = ""
        response = api_client.post(GOOGLE_URL, {"id_token": "fake"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── Refresh (rotation + reuse detection) ────────────────────────────────────


@pytest.mark.django_db
class TestRefresh:
    def test_refresh_rotates_the_cookie_and_returns_a_new_access_token(
        self, api_client
    ):
        _sign_in(api_client, "refresh@abem.test")
        old_refresh = api_client.cookies[REFRESH_COOKIE_NAME].value

        response = api_client.post(REFRESH_URL)
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert api_client.cookies[REFRESH_COOKIE_NAME].value != old_refresh

    def test_refresh_without_cookie_returns_401(self, api_client):
        response = api_client.post(REFRESH_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_reusing_a_rotated_token_beyond_the_grace_window_revokes_all_sessions(
        self, api_client
    ):
        user = _sign_in(api_client, "reuse@abem.test")
        old_refresh = api_client.cookies[REFRESH_COOKIE_NAME].value

        # rotate once: old_refresh is now blacklisted
        api_client.post(REFRESH_URL)

        # simulate time passing beyond the grace window
        blacklisted = (
            BlacklistedToken.objects.filter(token__user=user).order_by("-id").first()
        )
        blacklisted.blacklisted_at = timezone.now() - timedelta(seconds=60)
        blacklisted.save(update_fields=["blacklisted_at"])

        api_client.cookies[REFRESH_COOKIE_NAME] = old_refresh
        response = api_client.post(REFRESH_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # every outstanding token for the user is now blacklisted
        outstanding_ids = set(
            OutstandingToken.objects.filter(user=user).values_list("id", flat=True)
        )
        blacklisted_ids = set(
            BlacklistedToken.objects.filter(token__user=user).values_list(
                "token_id", flat=True
            )
        )
        assert outstanding_ids
        assert outstanding_ids == blacklisted_ids

    def test_double_submit_within_the_grace_window_is_tolerated(self, api_client):
        _sign_in(api_client, "doublesubmit@abem.test")
        old_refresh = api_client.cookies[REFRESH_COOKIE_NAME].value

        # first tab rotates successfully
        api_client.post(REFRESH_URL)

        # second tab immediately replays the same (now-rotated) old token
        api_client.cookies[REFRESH_COOKIE_NAME] = old_refresh
        response = api_client.post(REFRESH_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert (
            response.data["detail"]
            == "This refresh token was already used. Please try again."
        )

    def test_every_rotation_creates_a_real_outstanding_token_row(self, api_client):
        """
        Regression test: rotation must build a genuinely new refresh token
        (with its own OutstandingToken row), not just mutate jti/exp/iat on
        the decoded object in place - otherwise the live, not-yet-used
        token has no row for reuse-detection's mass-revoke to find later.
        """
        user = _sign_in(api_client, "outstandingrows@abem.test")
        count_after_login = OutstandingToken.objects.filter(user=user).count()
        assert count_after_login == 1

        for i in range(1, 4):
            response = api_client.post(REFRESH_URL)
            assert response.status_code == status.HTTP_200_OK
            assert (
                OutstandingToken.objects.filter(user=user).count()
                == count_after_login + i
            )

    def test_reuse_detection_also_revokes_the_live_not_yet_used_refresh_token(
        self, api_client
    ):
        """
        Regression test: replaying a long-stale (already-rotated-away)
        refresh token must kill every session for the user, including the
        live refresh token currently sitting unused in the cookie jar - not
        just tokens that have already been used-and-rotated-away.
        """
        user = _sign_in(api_client, "livetoken@abem.test")
        stale_refresh = api_client.cookies[REFRESH_COOKIE_NAME].value

        for _ in range(3):
            api_client.post(REFRESH_URL)
        live_refresh = api_client.cookies[REFRESH_COOKIE_NAME].value
        assert live_refresh != stale_refresh

        # back-date every blacklist entry so the grace window never applies
        BlacklistedToken.objects.filter(token__user=user).update(
            blacklisted_at=timezone.now() - timedelta(seconds=60)
        )

        # replay the stale, long-rotated-away token: triggers mass-revoke
        api_client.cookies[REFRESH_COOKIE_NAME] = stale_refresh
        response = api_client.post(REFRESH_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # the live, not-yet-used refresh token must be rejected too
        api_client.cookies[REFRESH_COOKIE_NAME] = live_refresh
        response = api_client.post(REFRESH_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ── Logout ────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestLogout:
    def test_logout_blacklists_the_cookie_and_clears_it(self, api_client):
        _sign_in(api_client, "logout@abem.test")

        response = api_client.post(LOGOUT_URL)
        assert response.status_code == status.HTTP_200_OK
        assert api_client.cookies[REFRESH_COOKIE_NAME].value == ""

    def test_logout_without_cookie_returns_400(self, admin_client):
        response = admin_client.post(LOGOUT_URL)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_logout_requires_authentication(self, api_client):
        response = api_client.post(LOGOUT_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_cookie_path_reaches_logout_not_just_refresh(self, api_client):
        """
        Regression test: the refresh_token cookie's Path must not be scoped
        to just /auth/refresh/ - browsers would never send it to the
        sibling path /auth/logout/, silently breaking logout.
        """
        _sign_in(api_client, "cookiepath@abem.test")
        cookie = api_client.cookies[REFRESH_COOKIE_NAME]
        assert LOGOUT_URL.startswith(cookie["path"])
        assert REFRESH_URL.startswith(cookie["path"])

    def test_logout_blacklists_the_refresh_token_so_it_cannot_be_reused(
        self, api_client
    ):
        """
        Regression test: once /auth/logout/ succeeds, replaying the
        "logged out" refresh token against /auth/refresh/ must fail -
        the bug was that logout silently no-opped because its cookie never
        arrived, leaving the token (and the session) alive.
        """
        _sign_in(api_client, "logoutreplay@abem.test")
        refresh_value = api_client.cookies[REFRESH_COOKIE_NAME].value

        response = api_client.post(LOGOUT_URL)
        assert response.status_code == status.HTTP_200_OK

        api_client.cookies[REFRESH_COOKIE_NAME] = refresh_value
        response = api_client.post(REFRESH_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ── Trusted devices ─────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestRevokeAllDevices:
    def test_revoke_all_deletes_every_trusted_device(self, admin_client, admin_user):
        TrustedDevice.objects.create(
            user=admin_user,
            token_hash="a" * 64,
            expires_at=timezone.now() + timedelta(days=1),
        )
        TrustedDevice.objects.create(
            user=admin_user,
            token_hash="b" * 64,
            expires_at=timezone.now() + timedelta(days=1),
        )
        response = admin_client.post(REVOKE_ALL_URL)
        assert response.status_code == status.HTTP_200_OK
        assert not TrustedDevice.objects.filter(user=admin_user).exists()

    def test_revoke_all_blacklists_other_sessions_refresh_tokens(
        self, admin_client, admin_user
    ):
        """
        Bug fix: revoke-all must not just delete TrustedDevice rows (which
        only gate the OTP-skip bypass) - it must also kill already-issued
        refresh tokens on other devices, matching what the "log out of all
        other devices" UI promises.
        """
        # Simulate two other devices that each already hold a live refresh
        # token (RefreshToken.for_user records a real OutstandingToken row
        # because rest_framework_simplejwt.token_blacklist is installed).
        other_session_1 = RefreshToken.for_user(admin_user)
        other_session_2 = RefreshToken.for_user(admin_user)

        assert not BlacklistedToken.objects.filter(
            token__jti=other_session_1.payload["jti"]
        ).exists()

        response = admin_client.post(REVOKE_ALL_URL)
        assert response.status_code == status.HTTP_200_OK

        assert BlacklistedToken.objects.filter(
            token__jti=other_session_1.payload["jti"]
        ).exists()
        assert BlacklistedToken.objects.filter(
            token__jti=other_session_2.payload["jti"]
        ).exists()

    def test_revoke_all_does_not_blacklist_the_calling_session(
        self, api_client, admin_user
    ):
        """The device the user clicked "revoke all" from should stay logged in."""
        refresh_token = CustomRefreshToken.for_user(admin_user)
        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {str(refresh_token.access_token)}"
        )
        api_client.cookies[REFRESH_COOKIE_NAME] = str(refresh_token)

        response = api_client.post(REVOKE_ALL_URL)
        assert response.status_code == status.HTTP_200_OK

        assert not BlacklistedToken.objects.filter(
            token__jti=refresh_token.payload["jti"]
        ).exists()


# ── Register ──────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestRegister:
    def test_admin_can_create_a_pending_user(self, admin_client):
        response = admin_client.post(
            REGISTER_URL,
            {
                "email": "newuser@abem.test",
                "first_name": "New",
                "last_name": "User",
                "role": "owner",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(email="newuser@abem.test")
        assert not user.has_usable_password()

    def test_owner_cannot_register_users(self, owner_client):
        response = owner_client.post(
            REGISTER_URL,
            {
                "email": "new2@abem.test",
                "first_name": "New",
                "last_name": "User",
                "role": "owner",
            },
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_duplicate_email_returns_400(self, admin_client, admin_user):
        response = admin_client.post(
            REGISTER_URL,
            {
                "email": admin_user.email,
                "first_name": "Dup",
                "last_name": "User",
                "role": "owner",
            },
        )
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

    @pytest.fixture(autouse=True)
    def _building(self, db, admin_user, owner_user):
        """Admins only manage users in their own buildings, so give them one."""
        from apps.buildings.models import Building, UserBuilding

        building = Building.objects.create(
            name="Test Building", address="1 Test St", admin=admin_user
        )
        UserBuilding.objects.create(user=owner_user, building=building)

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

    def test_admin_can_resend_an_invite(self, admin_client, owner_user):
        response = admin_client.post(f"{self.USERS_URL}{owner_user.id}/resend-invite/")
        assert response.status_code == status.HTTP_200_OK
        assert EmailOTP.objects.filter(user=owner_user).exists()


# ── Data migration: unusable-password rollout must spare superusers ────────────


@pytest.mark.django_db
class TestUnusablePasswordMigration:
    def test_superusers_and_staff_keep_a_usable_password(self):
        """
        Bug fix: 0011_unusable_passwords stripped every user's password,
        including Django-admin superusers, with no reverse migration - an
        irreversible lockout. Superusers/staff must be excluded.
        """
        migration_module = importlib.import_module(
            "apps.authentication.migrations.0011_unusable_passwords"
        )

        superuser = User.objects.create_user(
            email="root@abem.test",
            password="RealAdminPass1!",
            first_name="Root",
            last_name="Admin",
            is_staff=True,
            is_superuser=True,
        )
        staff_non_super = User.objects.create_user(
            email="staffer@abem.test",
            password="RealStaffPass1!",
            first_name="Staff",
            last_name="Member",
            is_staff=True,
        )
        regular = User.objects.create_user(
            email="regular@abem.test",
            password="RealOwnerPass1!",
            first_name="Regular",
            last_name="User",
        )

        migration_module.set_unusable_passwords(django_apps, None)

        superuser.refresh_from_db()
        staff_non_super.refresh_from_db()
        regular.refresh_from_db()

        assert superuser.has_usable_password()
        assert superuser.check_password("RealAdminPass1!")
        assert staff_non_super.has_usable_password()
        assert staff_non_super.check_password("RealStaffPass1!")
        # Non-staff, non-superuser accounts still get their password stripped.
        assert not regular.has_usable_password()


# ── JWT size: a large admin's claim set must not overflow the cookie ───────────


@pytest.mark.django_db
class TestTokenSize:
    def test_large_admin_refresh_token_has_no_unbounded_tenant_claim(self, admin_user):
        """
        Bug fix: tenant_ids used to embed every managed building UUID into
        both the access AND refresh token. For a 200+-building admin that
        pushed the refresh token - which IS the refresh cookie's value -
        past browsers' ~4096-byte per-cookie ceiling, so the cookie was
        silently dropped. Nothing reads tenant_ids off the token (tenant
        scoping is DB-derived via apps/buildings/scoping.py), so it's
        dropped entirely rather than merely capped.
        """
        from apps.buildings.models import Building

        for i in range(250):
            Building.objects.create(
                name=f"Building {i}",
                address=f"{i} Test Street",
                admin=admin_user,
            )

        refresh = CustomRefreshToken.for_user(admin_user)
        access = refresh.access_token

        assert "tenant_ids" not in refresh.payload
        assert "tenant_ids" not in access.payload

        # The refresh token is the cookie's value - keep it comfortably
        # under common browser/proxy header-size ceilings regardless of
        # how many buildings the admin manages.
        assert len(str(refresh)) < 2000
        assert len(str(access)) < 2000


# ── Device label parsing ─────────────────────────────────────────────────────


class TestDeviceLabelFromUserAgent:
    def test_chrome_on_macos(self):
        ua = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        assert device_label_from_user_agent(ua) == "Chrome on macOS"

    def test_safari_on_iphone(self):
        ua = (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        )
        assert device_label_from_user_agent(ua) == "Safari on iPhone"

    def test_firefox_on_windows(self):
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
        assert device_label_from_user_agent(ua) == "Firefox on Windows"

    def test_chrome_on_android(self):
        ua = (
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36"
        )
        assert device_label_from_user_agent(ua) == "Chrome on Android"

    def test_unparseable_ua_falls_back_to_unknown_device(self):
        assert device_label_from_user_agent("curl/7.64.1") == "Unknown device"

    def test_empty_ua_falls_back_to_unknown_device(self):
        assert device_label_from_user_agent("") == "Unknown device"
        assert device_label_from_user_agent(None) == "Unknown device"


class TestClientIpFromRequest:
    """
    Security fix: client_ip_from_request must not trust the client-supplied
    X-Forwarded-For header (nginx only APPENDS to it, so a client can send a
    fake first entry - see docs/DEPLOYMENT.md's `proxy_add_x_forwarded_for`).
    It must prefer X-Real-IP, which nginx sets from the actual TCP
    connection and can't be spoofed, falling back to REMOTE_ADDR only when
    neither proxy header is present (e.g. local dev without nginx).
    """

    def test_prefers_x_real_ip_over_a_spoofed_x_forwarded_for(self, rf):
        request = rf.post(
            "/api/v1/auth/otp/verify/",
            REMOTE_ADDR="10.0.0.1",
            HTTP_X_REAL_IP="203.0.113.9",
            HTTP_X_FORWARDED_FOR="1.2.3.4, 203.0.113.9",
        )
        assert client_ip_from_request(request) == "203.0.113.9"

    def test_falls_back_to_remote_addr_without_any_proxy_headers(self, rf):
        request = rf.post("/api/v1/auth/otp/verify/", REMOTE_ADDR="127.0.0.1")
        assert client_ip_from_request(request) == "127.0.0.1"

    def test_ignores_x_forwarded_for_when_x_real_ip_is_absent(self, rf):
        # Must NOT fall back to trusting X-Forwarded-For's first entry.
        request = rf.post(
            "/api/v1/auth/otp/verify/",
            REMOTE_ADDR="10.0.0.1",
            HTTP_X_FORWARDED_FOR="1.2.3.4, 203.0.113.9",
        )
        assert client_ip_from_request(request) == "10.0.0.1"


# ── Signed-in sessions ───────────────────────────────────────────────────────

SESSIONS_URL = "/api/v1/auth/sessions/"


def _revoke_url(session_pk):
    return f"/api/v1/auth/sessions/{session_pk}/revoke/"


def _session_id_from_cookie(client):
    raw = client.cookies[REFRESH_COOKIE_NAME].value
    return RefreshToken(raw).payload.get("session_id")


@pytest.mark.django_db
class TestSessionCreationOnLogin:
    def test_otp_verify_creates_exactly_one_session_with_correct_fields(
        self, api_client
    ):
        email = "sessionotp@abem.test"
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
        user = _sign_in(api_client, email, user_agent=ua)

        sessions = UserSession.objects.filter(user=user)
        assert sessions.count() == 1
        session = sessions.first()
        assert session.device_label == "Firefox on Windows"
        assert session.ip_address is not None
        assert session.current_jti
        assert str(session.session_id) == str(_session_id_from_cookie(api_client))

    def test_google_sign_in_creates_exactly_one_session(self, api_client, settings):
        settings.GOOGLE_CLIENT_ID = "test-client-id"
        with patch(
            "apps.authentication.views.google_id_token.verify_oauth2_token"
        ) as verify:
            verify.return_value = {
                "email": "googlesession@abem.test",
                "email_verified": True,
                "given_name": "Google",
                "family_name": "User",
            }
            response = api_client.post(
                GOOGLE_URL,
                {"id_token": "fake"},
                HTTP_USER_AGENT=(
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
                    "Mobile/15E148 Safari/604.1"
                ),
            )
        assert response.status_code == status.HTTP_200_OK
        user = User.objects.get(email="googlesession@abem.test")
        sessions = UserSession.objects.filter(user=user)
        assert sessions.count() == 1
        assert sessions.first().device_label == "Safari on iPhone"


@pytest.mark.django_db
class TestSessionIdStabilityAcrossRefresh:
    def test_refresh_keeps_session_id_but_bumps_jti_and_last_used_at(self, api_client):
        user = _sign_in(api_client, "sessionstability@abem.test")
        session = UserSession.objects.get(user=user)
        original_session_id = session.session_id
        original_jti = session.current_jti
        original_last_used_at = session.last_used_at

        response = api_client.post(REFRESH_URL)
        assert response.status_code == status.HTTP_200_OK

        session.refresh_from_db()
        assert session.session_id == original_session_id
        assert session.current_jti != original_jti
        assert session.last_used_at >= original_last_used_at
        assert UserSession.objects.filter(user=user).count() == 1


@pytest.mark.django_db
class TestSessionList:
    def test_is_current_true_only_for_the_calling_sessions_row(self, api_client):
        user = _sign_in(api_client, "sessionlist@abem.test")
        # simulate a second device/login for the same user
        other = UserSession.objects.create(
            user=user,
            device_label="Other device",
            ip_address="10.0.0.1",
            current_jti="other-jti",
        )

        response = api_client.get(SESSIONS_URL)
        assert response.status_code == status.HTTP_200_OK
        by_id = {row["id"]: row for row in response.data}

        current_session = UserSession.objects.exclude(pk=other.pk).get()
        assert by_id[current_session.pk]["is_current"] is True
        assert by_id[other.pk]["is_current"] is False


@pytest.mark.django_db
class TestSessionRevoke:
    def test_revoking_a_non_current_session_blacklists_only_its_token(self, api_client):
        user = _sign_in(api_client, "revokeother@abem.test")
        current_session = UserSession.objects.get(user=user)

        other_token = RefreshToken.for_user(user)
        other_session = UserSession.objects.create(
            user=user,
            device_label="Other device",
            ip_address="10.0.0.2",
            current_jti=other_token.payload["jti"],
        )

        response = api_client.post(_revoke_url(other_session.pk))
        assert response.status_code == status.HTTP_200_OK

        assert BlacklistedToken.objects.filter(
            token__jti=other_token.payload["jti"]
        ).exists()
        assert not UserSession.objects.filter(pk=other_session.pk).exists()
        # the caller's own session/token is untouched
        assert not BlacklistedToken.objects.filter(
            token__jti=current_session.current_jti
        ).exists()
        assert UserSession.objects.filter(pk=current_session.pk).exists()

    def test_revoking_own_current_session_returns_400_and_changes_nothing(
        self, api_client
    ):
        user = _sign_in(api_client, "revokeself@abem.test")
        current_session = UserSession.objects.get(user=user)

        response = api_client.post(_revoke_url(current_session.pk))
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assert UserSession.objects.filter(pk=current_session.pk).exists()
        assert not BlacklistedToken.objects.filter(
            token__jti=current_session.current_jti
        ).exists()

    def test_revoking_another_users_session_returns_404(self, api_client, owner_user):
        _sign_in(api_client, "revoke404@abem.test")
        others_session = UserSession.objects.create(
            user=owner_user,
            device_label="Someone else's device",
            ip_address="10.0.0.3",
            current_jti="someone-elses-jti",
        )
        response = api_client.post(_revoke_url(others_session.pk))
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_revoking_a_nonexistent_session_returns_404(self, api_client):
        _sign_in(api_client, "revokenonexistent@abem.test")
        response = api_client.post(_revoke_url(999999))
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestRevokeAllAlsoCleansUpUserSessions:
    def test_revoke_all_deletes_other_sessions_but_keeps_the_caller_s(self, api_client):
        user = _sign_in(api_client, "revokeallsessions@abem.test")
        current_session = UserSession.objects.get(user=user)
        other_session = UserSession.objects.create(
            user=user,
            device_label="Other device",
            ip_address="10.0.0.4",
            current_jti="other-jti-2",
        )

        response = api_client.post(REVOKE_ALL_URL)
        assert response.status_code == status.HTTP_200_OK

        assert UserSession.objects.filter(pk=current_session.pk).exists()
        assert not UserSession.objects.filter(pk=other_session.pk).exists()


@pytest.mark.django_db
class TestLogoutDeletesCurrentSession:
    def test_logout_deletes_the_current_sessions_row(self, api_client):
        user = _sign_in(api_client, "logoutsession@abem.test")
        assert UserSession.objects.filter(user=user).exists()

        response = api_client.post(LOGOUT_URL)
        assert response.status_code == status.HTTP_200_OK
        assert not UserSession.objects.filter(user=user).exists()


@pytest.mark.django_db
class TestAccountDeletionCleansUpUserSessions:
    def test_delete_account_removes_the_users_sessions(self, api_client, owner_user):
        _sign_in(api_client, owner_user.email)
        assert UserSession.objects.filter(user=owner_user).exists()

        # Request the deletion-confirmation code from a cookie-less client:
        # api_client's own trusted_device cookie (set by _sign_in) would
        # otherwise make otp/request/ bypass sending a fresh code entirely.
        from rest_framework.test import APIClient as _FreshClient

        with patch(
            "apps.authentication.otp.generate_otp_code", return_value=FIXED_CODE
        ):
            _FreshClient().post(OTP_REQUEST_URL, {"email": owner_user.email})
        response = api_client.post(
            "/api/v1/auth/delete-account/", {"code": FIXED_CODE}, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert not UserSession.objects.filter(user=owner_user).exists()
