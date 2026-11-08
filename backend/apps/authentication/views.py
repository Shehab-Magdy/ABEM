"""
Authentication views - email OTP, Google Sign-In, cookie-based refresh,
logout, register, profile, delete-account.

All endpoints are under /api/v1/auth/.
"""

from datetime import timedelta
from decimal import Decimal

import jwt
from django.conf import settings
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django_ratelimit.decorators import ratelimit
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings as jwt_api_settings
from rest_framework_simplejwt.token_blacklist.models import (BlacklistedToken,
                                                             OutstandingToken)
from rest_framework_simplejwt.tokens import RefreshToken

from apps.audit.mixins import log_action

from .cookies import (TRUSTED_DEVICE_COOKIE_NAME, clear_refresh_cookie,
                      clear_trusted_device_cookie, set_refresh_cookie,
                      set_trusted_device_cookie)
from .device import client_ip_from_request
from .models import TrustedDevice, User, UserSession
from .otp import (OTP_OK, OTP_TOO_MANY_ATTEMPTS, create_trusted_device,
                  find_trusted_device, otp_error_message,
                  request_otp_for_email, request_otp_for_user,
                  touch_trusted_device, verify_otp_for_email,
                  verify_otp_for_user)
from .permissions import IsAdminRole
from .serializers import (GoogleSignInSerializer, OTPRequestSerializer,
                          OTPVerifySerializer, ProfileUpdateSerializer,
                          RegisterUserSerializer, SelfRegisterSerializer,
                          UserSerializer, UserSessionSerializer)
from .tokens import issue_tokens_for_user


def _otp_rate_key(_group, request):
    """Rate-limit email-OTP requests per (email, IP) pair."""
    try:
        email = str(request.data.get("email", "")).strip().lower()
    except Exception:  # pragma: no cover - defensive, request.data always a dict here
        email = ""
    ip = request.META.get("REMOTE_ADDR", "") or ""
    return f"{email}:{ip}"


def _current_refresh_payload(request):
    """
    Decode the request's own refresh_token cookie (if any) and return its
    payload dict, or {} if there isn't one or it doesn't decode. Used to
    read the session_id/jti of the CALLING session - e.g. to mark it
    `is_current` in /auth/sessions/ or to exclude it from a mass-revoke.
    """
    raw_token = request.COOKIES.get("refresh_token")
    if not raw_token:
        return {}
    try:
        return RefreshToken(raw_token).payload
    except TokenError:
        return {}


def _auth_response(
    user, request, status_code=status.HTTP_200_OK, set_trusted_device=True
):
    """
    Build the shared {access, user} response for a successful sign-in
    (OTP verify, Google, or trusted-device bypass): issues a fresh token
    pair (and a fresh UserSession row), sets the refresh cookie, and
    optionally sets/rotates the trusted_device cookie.
    """
    access, refresh = issue_tokens_for_user(user, request=request)
    response = Response(
        {
            "access": access,
            "user": UserSerializer(user, context={"request": request}).data,
        },
        status=status_code,
    )
    set_refresh_cookie(response, refresh)
    if set_trusted_device:
        device = create_trusted_device(user)
        max_age = int((device.expires_at - timezone.now()).total_seconds())
        set_trusted_device_cookie(response, device.token, max_age=max_age)
    return response


# ── Email OTP ─────────────────────────────────────────────────────────────────


def _otp_request_ip_key(_group, request):
    """
    Rate-limit email-OTP requests by IP alone, independent of the target
    email.

    `_otp_rate_key` above (per email+IP) gives every new target address its
    own fresh budget, so a single IP can otherwise "email-bomb" unlimited
    different real users, or just run up email-sending cost, by varying the
    email on each request. This is a second, coarser ceiling stacked on top
    of it (django_ratelimit ORs `request.limited` across stacked decorators -
    see OTPRequestView.post).

    30/hour is picked to tolerate a legitimate shared-NAT case - e.g. a
    whole apartment building of ABEM residents behind one public IP/router,
    which is a realistic scenario for this product - while still bounding
    sustained abuse from one source. Keyed on `client_ip_from_request`
    (X-Real-IP, set by nginx from the real TCP peer; REMOTE_ADDR in local
    dev/tests) rather than the raw REMOTE_ADDR that `_otp_rate_key` uses, so
    it can't be defeated by a spoofed X-Forwarded-For.
    """
    return client_ip_from_request(request) or ""


class OTPRequestView(APIView):
    """
    POST /auth/otp/request/ {email}

    Anti-enumeration: the response is the same `200 {"detail": ...}` shape
    whether or not `email` already has an account, and no `User` row is
    created for an email that doesn't have one yet - only a pending
    `EmailOTP` row keyed by the email itself. The account is only created
    in `otp/verify/`, once `accept_terms: true` has been supplied for it
    (see OTPVerifyView). If a valid trusted_device cookie is presented for
    an *existing* user, this signs them in immediately (same response shape
    as otp/verify) without sending a code.
    """

    permission_classes = [AllowAny]

    @method_decorator(
        ratelimit(key=_otp_request_ip_key, rate="30/h", method="POST", block=False)
    )
    @method_decorator(
        ratelimit(key=_otp_rate_key, rate="5/m", method="POST", block=False)
    )
    def post(self, request):
        if getattr(request, "limited", False):
            return Response(
                {"detail": _("Too many requests. Please wait a moment and try again.")},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower()

        user = User.objects.filter(email__iexact=email).first()

        if user is None:
            # Brand-new address: no account yet, and none is created here -
            # just a pending OTP row keyed by the email. Mirrors the
            # existing-user branch below as closely as possible so the
            # response/timing doesn't reveal that the account doesn't exist.
            request_otp_for_email(email)
            return Response(
                {"detail": _("A sign-in code has been sent to your email.")}
            )

        if not user.is_active:
            return Response(
                {"detail": _("This account has been deactivated.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        raw_device_token = request.COOKIES.get(TRUSTED_DEVICE_COOKIE_NAME)
        device = (
            find_trusted_device(user, raw_device_token) if raw_device_token else None
        )
        if device is not None:
            touch_trusted_device(device)
            log_action(
                user=user,
                action="login",
                entity="user",
                entity_id=user.id,
                changes={"method": "trusted_device"},
                request=request,
            )
            return _auth_response(user, request, set_trusted_device=False)

        request_otp_for_user(user)
        log_action(
            user=user,
            action="otp_requested",
            entity="user",
            entity_id=user.id,
            request=request,
        )
        return Response({"detail": _("A sign-in code has been sent to your email.")})


class OTPVerifyView(APIView):
    """
    POST /auth/otp/verify/ {email, code, accept_terms?} -> {access, user} +
    refresh/trusted_device cookies.

    If `email` already has an account, this is an ordinary sign-in:
    `accept_terms` is not needed. If it doesn't, this is a brand-new
    signup via the login page (mirrors `SelfRegisterView`, which requires
    acceptance up front - OTP just defers it past the anti-enumeration
    boundary in otp/request/): `accept_terms: true` must be present, or the
    request is rejected with `400 {"detail": ..., "code": "terms_required"}`
    WITHOUT checking or consuming the code, so the frontend can show a
    terms checkbox and resubmit the same `{email, code, accept_terms: true}`.
    Once `accept_terms: true` is present and `code` is correct, the account
    is created (role=owner, terms_accepted_at=now) and the code is consumed.
    """

    permission_classes = [AllowAny]

    # Backstop against requesting many fresh codes to farm more 5-wrong-
    # attempts budgets (otp/request/ is itself 5/m per email+IP, so a caller
    # could otherwise sustain ~25 guesses/min indefinitely). The per-code
    # attempt-burn in verify_otp_for_user is the primary defense; this limit
    # is intentionally looser (10/m, keyed the same way as otp/request/) so
    # a legitimate user mistyping a code a couple of times isn't blocked,
    # and it counts every request regardless of success/failure.
    @method_decorator(
        ratelimit(key=_otp_rate_key, rate="10/m", method="POST", block=False)
    )
    def post(self, request):
        if getattr(request, "limited", False):
            return Response(
                {"detail": _("Too many requests. Please wait a moment and try again.")},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower()
        code = serializer.validated_data["code"]
        accept_terms = serializer.validated_data.get("accept_terms", False)

        user = User.objects.filter(email__iexact=email).first()

        if user is None:
            if not accept_terms:
                return Response(
                    {
                        "detail": _(
                            "You must accept the Terms of Service and Privacy Policy."
                        ),
                        "code": "terms_required",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            result = verify_otp_for_email(email, code)
            if result != OTP_OK:
                http_status = (
                    status.HTTP_429_TOO_MANY_REQUESTS
                    if result == OTP_TOO_MANY_ATTEMPTS
                    else status.HTTP_400_BAD_REQUEST
                )
                return Response(
                    {"detail": otp_error_message(result), "code": result},
                    status=http_status,
                )

            user = User(email=email, first_name="", last_name="")
            user.terms_accepted_at = timezone.now()
            user.set_unusable_password()
            user.save()
            log_action(
                user=user,
                action="self_register",
                entity="user",
                entity_id=user.id,
                changes={"method": "otp"},
                request=request,
            )
        else:
            if not user.is_active:
                return Response(
                    {"detail": _("This account has been deactivated.")},
                    status=status.HTTP_403_FORBIDDEN,
                )

            result = verify_otp_for_user(user, code)
            if result != OTP_OK:
                http_status = (
                    status.HTTP_429_TOO_MANY_REQUESTS
                    if result == OTP_TOO_MANY_ATTEMPTS
                    else status.HTTP_400_BAD_REQUEST
                )
                return Response(
                    {"detail": otp_error_message(result), "code": result},
                    status=http_status,
                )

        log_action(
            user=user,
            action="login",
            entity="user",
            entity_id=user.id,
            changes={"method": "otp"},
            request=request,
        )
        return _auth_response(user, request)


# ── Google Sign-In ──────────────────────────────────────────────────────────


class GoogleSignInView(APIView):
    """
    POST /auth/google/ {id_token, accept_terms?} -> {access, user} +
    refresh/trusted_device cookies.

    Same signup-requires-terms rule as `OTPVerifyView`: if the
    Google-verified email already has an account, this is an ordinary
    sign-in. If it doesn't, `accept_terms: true` must be present in the
    body or the request is rejected with
    `400 {"detail": ..., "code": "terms_required"}` WITHOUT creating any
    account, so the frontend can show a terms checkbox and resubmit the
    same `{id_token, accept_terms: true}`.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleSignInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        raw_id_token = serializer.validated_data["id_token"]
        accept_terms = serializer.validated_data.get("accept_terms", False)

        if not settings.GOOGLE_CLIENT_ID:
            return Response(
                {"detail": _("Google Sign-In is not configured.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            idinfo = google_id_token.verify_oauth2_token(
                raw_id_token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
            )
        except ValueError:
            return Response(
                {"detail": _("Invalid Google sign-in token.")},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        email = (idinfo.get("email") or "").lower()
        if not email or not idinfo.get("email_verified", True):
            return Response(
                {"detail": _("Invalid Google sign-in token.")},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Auto-link to an existing account by email - intentional (same person, one identity).
        user = User.objects.filter(email__iexact=email).first()

        if user is None:
            if not accept_terms:
                return Response(
                    {
                        "detail": _(
                            "You must accept the Terms of Service and Privacy Policy."
                        ),
                        "code": "terms_required",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = User(
                email=email,
                first_name=idinfo.get("given_name", "") or "",
                last_name=idinfo.get("family_name", "") or "",
            )
            user.terms_accepted_at = timezone.now()
            user.set_unusable_password()
            user.save()
            log_action(
                user=user,
                action="self_register",
                entity="user",
                entity_id=user.id,
                changes={"method": "google"},
                request=request,
            )
        elif not user.is_active:
            return Response(
                {"detail": _("This account has been deactivated.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        log_action(
            user=user,
            action="login",
            entity="user",
            entity_id=user.id,
            changes={"method": "google"},
            request=request,
        )
        return _auth_response(user, request)


# ── Cookie-based refresh (rotation + reuse detection) ──────────────────────


class CookieTokenRefreshView(APIView):
    """
    POST /auth/refresh/ (no body - the refresh token travels as an httpOnly
    cookie) -> {access}, and sets a rotated refresh cookie.

    Reuse detection: if the presented refresh token is already blacklisted
    (i.e. it was already rotated once), every outstanding session for that
    user is revoked - unless the blacklist entry is within a ~30s grace
    window, which tolerates two near-simultaneous tabs both submitting the
    same pre-rotation token.
    """

    permission_classes = [AllowAny]
    REUSE_GRACE_SECONDS = 30

    def post(self, request):
        raw_token = request.COOKIES.get("refresh_token")
        if not raw_token:
            return self._unauthorized(_("Refresh token is required."))

        try:
            refresh = RefreshToken(raw_token)
        except TokenError:
            return self._handle_invalid_refresh(request, raw_token)

        if jwt_api_settings.ROTATE_REFRESH_TOKENS:
            user_id = refresh.payload.get(jwt_api_settings.USER_ID_CLAIM)
            session_id = refresh.payload.get("session_id")
            user = User.objects.filter(pk=user_id).first()
            if user is None or not user.is_active:
                return self._unauthorized()

            if jwt_api_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    refresh.blacklist()
                except (
                    AttributeError
                ):  # pragma: no cover - blacklist app always installed here
                    pass

            # Issue a genuinely new refresh token (not a mutated copy of the
            # old one) so a real OutstandingToken row exists for it - that
            # row is what lets reuse-detection's mass-revoke find and
            # blacklist this token later. Mutating jti/exp/iat on the decoded
            # `refresh` object in place would leave rotated-to tokens with no
            # OutstandingToken row until they themselves get used/blacklisted,
            # letting the live token survive a "revoke all sessions".
            # `session_id` is passed through unchanged so the UserSession row
            # for this session is updated in place rather than duplicated.
            access, new_refresh = issue_tokens_for_user(
                user, request=request, session_id=session_id
            )
            response = Response({"access": access}, status=status.HTTP_200_OK)
            set_refresh_cookie(response, new_refresh)
            return response

        access = refresh.access_token
        response = Response({"access": str(access)}, status=status.HTTP_200_OK)
        set_refresh_cookie(response, str(refresh))
        return response

    def _handle_invalid_refresh(self, request, raw_token):
        """
        The token failed simplejwt's normal verification (expired, invalid,
        wrong type, or blacklisted). Decode it ignoring expiry - but still
        checking the signature - to see whether this was a blacklisted
        (already-rotated) token being replayed.
        """
        try:
            payload = jwt.decode(
                raw_token,
                jwt_api_settings.SIGNING_KEY,
                algorithms=[jwt_api_settings.ALGORITHM],
                options={"verify_exp": False},
            )
        except jwt.PyJWTError:
            return self._unauthorized()

        jti = payload.get(jwt_api_settings.JTI_CLAIM) or payload.get("jti")
        user_id = payload.get(jwt_api_settings.USER_ID_CLAIM)

        blacklisted = None
        if jti:
            blacklisted = (
                BlacklistedToken.objects.filter(token__jti=jti)
                .select_related("token")
                .first()
            )

        if blacklisted is None:
            # Genuinely expired, unknown, or never-issued - not a reuse case.
            return self._unauthorized()

        grace = timedelta(seconds=self.REUSE_GRACE_SECONDS)
        if timezone.now() - blacklisted.blacklisted_at < grace:
            return self._unauthorized(
                _("This refresh token was already used. Please try again.")
            )

        # Reuse detected beyond the grace window: revoke every session for this user.
        if user_id:
            user = User.objects.filter(pk=user_id).first()
            if user:
                for outstanding in OutstandingToken.objects.filter(user=user):
                    BlacklistedToken.objects.get_or_create(token=outstanding)
                log_action(
                    user=user,
                    action="refresh_reuse_detected",
                    entity="user",
                    entity_id=user.id,
                    request=request,
                )

        return self._unauthorized(
            _("Session invalidated for your safety. Please sign in again.")
        )

    def _unauthorized(self, message=None):
        response = Response(
            {"detail": message or _("Refresh token is invalid or expired.")},
            status=status.HTTP_401_UNAUTHORIZED,
        )
        clear_refresh_cookie(response)
        return response


# ── Logout ────────────────────────────────────────────────────────────────────


class LogoutView(APIView):
    """POST /auth/logout/ (refresh token read from cookie) -> blacklists it, clears the cookie."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        raw_token = request.COOKIES.get("refresh_token")
        if not raw_token:
            return Response(
                {"detail": _("No session to log out of.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(raw_token)
            session_id = token.payload.get("session_id")
            token.blacklist()
        except TokenError:
            response = Response(
                {"detail": _("Token is invalid or already blacklisted.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
            clear_refresh_cookie(response)
            return response

        if session_id:
            UserSession.objects.filter(
                user=request.user, session_id=session_id
            ).delete()

        log_action(
            user=request.user,
            action="logout",
            entity="user",
            entity_id=request.user.id,
            request=request,
        )

        response = Response({"detail": _("Successfully logged out.")})
        clear_refresh_cookie(response)
        # trusted_device is left alone on purpose: logging out of one device
        # shouldn't un-trust it (use /auth/devices/revoke-all/ for that).
        return response


# ── Trusted devices ─────────────────────────────────────────────────────────


class RevokeAllDevicesView(APIView):
    """
    POST /auth/devices/revoke-all/ - ends every OTHER active session for the
    caller: deletes every trusted device (so otp/request/ can no longer skip
    the code step from another browser), blacklists every other outstanding
    refresh token for the user (so an already-issued cookie on another
    device stops working, instead of quietly surviving until it naturally
    expires), and deletes the UserSession row for each of those other
    sessions. The current session's own refresh token and UserSession row,
    if identifiable from the request cookie, are left alone.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        deleted, _counts = TrustedDevice.objects.filter(user=request.user).delete()

        current_payload = _current_refresh_payload(request)
        current_jti = current_payload.get(jwt_api_settings.JTI_CLAIM)
        current_session_id = current_payload.get("session_id")

        outstanding = OutstandingToken.objects.filter(user=request.user)
        if current_jti:
            outstanding = outstanding.exclude(jti=current_jti)
        revoked_count = 0
        for token in outstanding:
            _blacklisted, created = BlacklistedToken.objects.get_or_create(token=token)
            if created:
                revoked_count += 1

        other_sessions = UserSession.objects.filter(user=request.user)
        if current_session_id:
            other_sessions = other_sessions.exclude(session_id=current_session_id)
        other_sessions_deleted, _deleted_counts = other_sessions.delete()

        log_action(
            user=request.user,
            action="devices_revoked",
            entity="user",
            entity_id=request.user.id,
            changes={
                "trusted_devices_deleted": deleted,
                "sessions_revoked": revoked_count,
                "user_sessions_deleted": other_sessions_deleted,
            },
            request=request,
        )
        response = Response({"detail": _("All trusted devices have been revoked.")})
        clear_trusted_device_cookie(response)
        return response


# ── Signed-in sessions (list + per-session revoke) ──────────────────────────


class SessionListView(APIView):
    """
    GET /auth/sessions/ -> [{id, device_label, ip_address, created_at,
    last_used_at, is_current}, ...], ordered by most recently used first.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        current_session_id = _current_refresh_payload(request).get("session_id")
        sessions = UserSession.objects.filter(user=request.user).order_by(
            "-last_used_at"
        )
        serializer = UserSessionSerializer(
            sessions, many=True, context={"current_session_id": current_session_id}
        )
        return Response(serializer.data)


class SessionRevokeView(APIView):
    """
    POST /auth/sessions/{id}/revoke/ - ends one OTHER signed-in session:
    blacklists its current OutstandingToken (by the UserSession's
    current_jti) and deletes the UserSession row. 404 if the session
    doesn't belong to the caller; 400 if it's the caller's own current
    session (use /auth/logout/ for that instead).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, session_pk):
        session = get_object_or_404(UserSession, pk=session_pk, user=request.user)

        current_session_id = _current_refresh_payload(request).get("session_id")
        if current_session_id and str(session.session_id) == str(current_session_id):
            return Response(
                {"detail": _("Use /auth/logout/ to sign out of your current session.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        outstanding = OutstandingToken.objects.filter(
            user=request.user, jti=session.current_jti
        ).first()
        if outstanding is not None:
            BlacklistedToken.objects.get_or_create(token=outstanding)

        session_id = session.session_id
        device_label = session.device_label
        session.delete()

        log_action(
            user=request.user,
            action="session_revoked",
            entity="user",
            entity_id=request.user.id,
            changes={"session_id": str(session_id), "device_label": device_label},
            request=request,
        )

        return Response({"detail": _("Session revoked.")})


# ── Register (Admin only) ──────────────────────────────────────────────────────


class RegisterView(APIView):
    """
    POST /auth/register/ (Admin only) - creates a pending (passwordless) user
    record. The frontend then drives the new user through otp/request +
    otp/verify (or Google) to complete their first sign-in.
    """

    permission_classes = [IsAdminRole]

    def post(self, request):
        serializer = RegisterUserSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        log_action(
            user=request.user,
            action="create",
            entity="user",
            entity_id=user.id,
            changes={"email": {"after": user.email}, "role": {"after": user.role}},
            request=request,
        )

        return Response(
            UserSerializer(user, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


# ── Self-Register (public, role forced to 'owner') ────────────────────────────


class SelfRegisterView(APIView):
    """
    POST /auth/self-register/ - creates a pending (passwordless) user record.
    The frontend then drives the new user through otp/request + otp/verify
    (or Google) to complete their first sign-in.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SelfRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        log_action(
            user=user,
            action="self_register",
            entity="user",
            entity_id=user.id,
            request=request,
        )

        return Response(
            UserSerializer(user, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


# ── Profile ────────────────────────────────────────────────────────────────────


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        return Response(UserSerializer(request.user, context={"request": request}).data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        old_values = {
            field: getattr(request.user, field) for field in serializer.validated_data
        }
        serializer.save()

        log_action(
            user=request.user,
            action="update",
            entity="user",
            entity_id=request.user.id,
            changes={
                field: {
                    "before": str(old_values[field]),
                    "after": str(serializer.validated_data[field]),
                }
                for field in serializer.validated_data
            },
            request=request,
        )

        return Response(UserSerializer(request.user, context={"request": request}).data)


# ── Delete my account ────────────────────────────────────────────────────────

BOARD_TITLES = {
    "chair": ("chair", "رئيس الهيئة"),
    "treasurer": ("treasurer", "أمين الصندوق"),
    "secretary": ("secretary", "أمين السر"),
}


class DeleteAccountView(APIView):
    """
    POST /auth/delete-account/ {code, confirm_balance?}

    Removes the person, keeps the books: the account is deactivated and its personal data
    (name, email, phone, picture, memberships) is erased, while payments, expense shares and the
    audit log stay attached to an anonymised user. The primary admin of a building must hand it
    over first so no building is left without an administrator.

    `code` is a fresh email OTP (requested via POST /auth/otp/request/) - this replaces the old
    password confirmation now that accounts have no password.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.apartments.models import Apartment
        from apps.buildings.models import (Building, BuildingCoAdmin,
                                           UserBuilding)
        from apps.notifications.services import building_admins, tell
        from apps.payments.models import ClaimStatus, PaymentClaim

        user = request.user

        result = verify_otp_for_user(user, request.data.get("code") or "")
        if result != OTP_OK:
            http_status = (
                status.HTTP_429_TOO_MANY_REQUESTS
                if result == OTP_TOO_MANY_ATTEMPTS
                else status.HTTP_400_BAD_REQUEST
            )
            return Response({"detail": otp_error_message(result)}, status=http_status)

        owned = Building.objects.filter(admin=user, deleted_at__isnull=True)
        if owned.exists():
            return Response(
                {
                    "detail": _(
                        "You are the administrator of a building. Hand it over to another admin before deleting your account."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        other_platform_owners = User.objects.filter(
            is_superuser=True, is_active=True
        ).exclude(pk=user.pk)
        if user.is_superuser and not other_platform_owners.exists():
            return Response(
                {
                    "detail": _(
                        "You are the last platform owner. Make someone else a platform owner first."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        # units the person owns or rents: what they still owe must be acknowledged before leaving
        units = Apartment.objects.filter(Q(owner=user) | Q(owners=user)).distinct()
        owed = units.filter(balance__gt=0).aggregate(s=Sum("balance"))["s"] or Decimal(
            "0.00"
        )
        if owed > 0 and str(request.data.get("confirm_balance")).lower() != "true":
            return Response(
                {
                    "detail": _(
                        "You still owe a balance on your unit. Send confirm_balance to delete your account anyway."
                    ),
                    "balance": str(owed),
                    "requires_confirmation": True,
                },
                status=status.HTTP_409_CONFLICT,
            )

        with transaction.atomic():
            # a pending transfer report can no longer be reviewed against a person who is gone
            rejected = PaymentClaim.objects.filter(
                created_by=user, status=ClaimStatus.PENDING
            ).update(status=ClaimStatus.REJECTED, reviewed_at=timezone.now())
            # tell each building's admins when a board member leaves
            for link in (
                UserBuilding.objects.filter(user=user)
                .exclude(board_role="")
                .select_related("building")
            ):
                for admin in building_admins(link.building):
                    if admin.pk == user.pk:
                        continue
                    role_en, role_ar = BOARD_TITLES.get(
                        link.board_role, (link.board_role, link.board_role)
                    )
                    tell(
                        admin,
                        (
                            "Board member left",
                            f"The {role_en} of {link.building.name} deleted their account.",
                        ),
                        (
                            "غادر عضو في الهيئة الإدارية",
                            f"قام {role_ar} في {link.building.name} بحذف حسابه.",
                        ),
                        {"building_id": str(link.building_id)},
                    )
            for apt in Apartment.objects.filter(owner=user):
                apt.owner = None
                apt.save(update_fields=["owner", "updated_at"])
            Apartment.owners.through.objects.filter(user_id=user.pk).delete()
            UserBuilding.objects.filter(user=user).delete()
            BuildingCoAdmin.objects.filter(user=user).delete()

            log_action(
                user=user,
                action="delete_account",
                entity="user",
                entity_id=user.id,
                changes={"claims_rejected": rejected, "balance_owed": str(owed)},
                request=request,
            )

            user.email = f"deleted-{user.pk}@deleted.invalid"
            user.first_name = ""
            user.last_name = ""
            user.phone = ""
            user.profile_picture = None
            user.is_active = False
            user.set_unusable_password()
            user.save()

            # sign the person out everywhere
            for token in OutstandingToken.objects.filter(user=user):
                BlacklistedToken.objects.get_or_create(token=token)
            TrustedDevice.objects.filter(user=user).delete()
            UserSession.objects.filter(user=user).delete()

        response = Response({"detail": _("Your account has been deleted.")})
        clear_refresh_cookie(response)
        clear_trusted_device_cookie(response)
        return response
