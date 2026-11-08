"""
Email OTP + trusted-device helpers.

Replaces password auth: a user signs in by requesting a 6-digit code emailed
to them (`EmailOTP`) or via Google Sign-In. A successful sign-in may mark the
device as trusted (`TrustedDevice`) so a later `otp/request/` skips the code
step entirely for ~30 days.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import EmailOTP, TrustedDevice, User

# Codes returned by verify_otp_for_user / verify_otp_for_email to let the
# view pick the right HTTP status and message.
OTP_OK = "ok"
OTP_NOT_FOUND = "not_found"
OTP_EXPIRED = "expired"
OTP_INVALID = "invalid"
OTP_TOO_MANY_ATTEMPTS = "max_attempts"

TRUSTED_DEVICE_TTL_DAYS = 30


def _hmac_hash(value: str) -> str:
    """HMAC-SHA256 the given value with the app's SECRET_KEY."""
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"), value.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def _sha256_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def generate_otp_code() -> str:
    """A 6-digit numeric code, zero-padded."""
    return f"{secrets.randbelow(1_000_000):06d}"


def create_otp_for_user(user: User) -> str:
    """Create (and return the plaintext of) a new OTP code for `user`."""
    code = generate_otp_code()
    ttl_minutes = getattr(settings, "OTP_CODE_TTL_MINUTES", 10)
    EmailOTP.objects.create(
        user=user,
        code_hash=_hmac_hash(code),
        expires_at=timezone.now() + timedelta(minutes=ttl_minutes),
    )
    return code


def create_otp_for_email(email: str) -> str:
    """
    Create (and return the plaintext of) a new OTP code for an `email` that
    has no account yet. Used by otp/request/ for a brand-new signup, so no
    `User` row is created before the Terms of Service are accepted in
    otp/verify/.
    """
    code = generate_otp_code()
    ttl_minutes = getattr(settings, "OTP_CODE_TTL_MINUTES", 10)
    EmailOTP.objects.create(
        user=None,
        email=email,
        code_hash=_hmac_hash(code),
        expires_at=timezone.now() + timedelta(minutes=ttl_minutes),
    )
    return code


def send_otp_email(
    email: str, code: str, first_name: str = "", lang: str = "en"
) -> bool:
    """Email the given plaintext OTP code to `email` in the given language."""
    from apps.notifications.email_service import send_notification_email

    lang = lang if lang in ("en", "ar") else "en"
    return send_notification_email(
        "otp",
        email,
        {
            "code": code,
            "first_name": first_name,
            "ttl_minutes": getattr(settings, "OTP_CODE_TTL_MINUTES", 10),
        },
        lang=lang,
    )


def request_otp_for_user(user: User) -> str:
    """Create a new OTP for `user` and email it. Returns the plaintext code (for tests)."""
    code = create_otp_for_user(user)
    send_otp_email(
        user.email, code, first_name=user.first_name, lang=user.preferred_language
    )
    return code


def request_otp_for_email(email: str) -> str:
    """
    Create a new OTP for a not-yet-registered `email` and email it. Mirrors
    `request_otp_for_user` as closely as possible (same DB write + email
    send shape) so otp/request/'s response/timing doesn't leak whether the
    address has an account (anti-enumeration).
    """
    code = create_otp_for_email(email)
    send_otp_email(email, code)
    return code


def _consume_otp(otp: Optional[EmailOTP], code: str) -> str:
    """
    Shared verify/consume logic for a looked-up `EmailOTP` row (by user or
    by pending email). Consumes (deletes) the row on success, or on
    exceeding the max attempt count. Returns one of the OTP_* constants.
    """
    if otp is None:
        return OTP_NOT_FOUND
    if otp.is_expired:
        otp.delete()
        return OTP_EXPIRED

    max_attempts = getattr(settings, "OTP_MAX_ATTEMPTS", 5)
    if otp.attempts >= max_attempts:
        otp.delete()
        return OTP_TOO_MANY_ATTEMPTS

    if not hmac.compare_digest(otp.code_hash, _hmac_hash(code or "")):
        otp.attempts += 1
        if otp.attempts >= max_attempts:
            otp.delete()
            return OTP_TOO_MANY_ATTEMPTS
        otp.save(update_fields=["attempts"])
        return OTP_INVALID

    otp.delete()
    return OTP_OK


def verify_otp_for_user(user: User, code: str) -> str:
    """
    Verify `code` against the latest non-expired OTP for `user`.

    Consumes (deletes) the OTP row on success, or on exceeding the max
    attempt count. Returns one of the OTP_* status constants above.
    """
    otp = EmailOTP.objects.filter(user=user).order_by("-created_at").first()
    return _consume_otp(otp, code)


def verify_otp_for_email(email: str, code: str) -> str:
    """
    Verify `code` against the latest non-expired OTP for a not-yet-registered
    `email` (user is null). Same consume/attempt-burn semantics as
    `verify_otp_for_user`. Returns one of the OTP_* status constants above.
    """
    otp = (
        EmailOTP.objects.filter(user__isnull=True, email__iexact=email)
        .order_by("-created_at")
        .first()
    )
    return _consume_otp(otp, code)


def otp_error_message(error_code: str):
    """Human-facing (translatable) message for an OTP_* error constant."""
    return {
        OTP_NOT_FOUND: _("No active code was found for this email. Request a new one."),
        OTP_EXPIRED: _("This code has expired. Request a new one."),
        OTP_INVALID: _("Incorrect code."),
        OTP_TOO_MANY_ATTEMPTS: _("Too many attempts. Request a new code."),
    }.get(error_code, _("Could not verify this code."))


# ── Trusted devices ──────────────────────────────────────────────────────────


def generate_device_token() -> str:
    return secrets.token_urlsafe(32)


def create_trusted_device(user: User) -> TrustedDevice:
    """Create a new trusted device row and return it (access `.token` for the raw cookie value)."""
    token = generate_device_token()
    device = TrustedDevice.objects.create(
        user=user,
        token_hash=_sha256_hash(token),
        expires_at=timezone.now() + timedelta(days=TRUSTED_DEVICE_TTL_DAYS),
    )
    device.token = token  # not persisted; carried only for this request/response
    return device


def find_trusted_device(user: User, raw_token: str) -> Optional[TrustedDevice]:
    """Return the matching, non-expired TrustedDevice for `user`, or None."""
    if not raw_token:
        return None
    return TrustedDevice.objects.filter(
        user=user, token_hash=_sha256_hash(raw_token), expires_at__gt=timezone.now()
    ).first()


def touch_trusted_device(device: TrustedDevice) -> None:
    device.last_used_at = timezone.now()
    device.save(update_fields=["last_used_at"])
