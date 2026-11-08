"""Custom JWT token with user_id and role claims."""

import uuid

from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from .device import client_ip_from_request, device_label_from_user_agent


class CustomRefreshToken(RefreshToken):
    """
    Extends the default RefreshToken to embed user_id, role and session_id
    into the token payload.

    Deliberately does NOT embed tenant_ids (the building UUIDs a user may
    access): every tenant-scoped queryset already goes through
    `apps/buildings/scoping.py` (`managed_buildings`/`ensure_manages`),
    which re-derives the set from the DB on every request regardless of
    what's in the token, so nothing reads this claim. Embedding it used to
    make the refresh token - which IS the refresh cookie's value - grow
    unbounded with the number of buildings an admin manages, large enough
    for a 200+-building admin to exceed browsers' ~4096-byte per-cookie
    ceiling (the cookie is then silently dropped, not truncated, on
    Set-Cookie). It also bloated the access token sent as a bearer header
    on every API request. The refresh endpoint re-derives everything fresh
    via `issue_tokens_for_user`/`CustomRefreshToken.for_user` on every
    rotation anyway, so there was nothing this claim bought.

    `session_id` is different: it identifies one continuous signed-in
    session (see `apps.authentication.models.UserSession`) and is meant to
    survive rotation unchanged, so it's passed in explicitly rather than
    re-derived.
    """

    @classmethod
    def for_user(cls, user, session_id=None):
        token = super().for_user(user)

        token["user_id"] = str(user.id)
        token["role"] = user.role
        token["session_id"] = str(session_id or uuid.uuid4())

        return token


def issue_tokens_for_user(user, request=None, session_id=None):
    """
    Build a fresh (access, refresh) token pair for `user`, embedding the
    custom user_id/role/session_id claims onto the refresh token so they
    survive refresh-token rotation (simplejwt's `RefreshToken.access_token`
    copies the refresh token's own payload forward onto each new access
    token, and rotation keeps the same payload apart from exp/iat/jti).

    `session_id`:
      - omitted (None) on a fresh sign-in (OTP verify, Google sign-in, the
        trusted-device bypass) - a new UUID is generated and a new
        `UserSession` row is created for it (when `request` is given).
      - passed through on refresh-token rotation, so the *same* session
        keeps the same `session_id` across rotations - only its
        `current_jti`/`last_used_at` are updated (when `request` is
        given). If no matching `UserSession` row exists yet (e.g. a token
        issued before this feature shipped), one is created defensively.

    `request` is optional so this stays callable without a request (tests,
    internal callers) - the `UserSession` upsert is simply skipped then.

    Returns (access_token_str, refresh_token_str).
    """
    is_new_session = session_id is None
    resolved_session_id = session_id or uuid.uuid4()

    refresh = CustomRefreshToken.for_user(user, session_id=resolved_session_id)
    access = refresh.access_token
    jti = refresh.payload.get("jti")

    if request is not None:
        from .models import UserSession

        if is_new_session:
            UserSession.objects.create(
                user=user,
                session_id=resolved_session_id,
                device_label=device_label_from_user_agent(
                    request.META.get("HTTP_USER_AGENT", "")
                ),
                ip_address=client_ip_from_request(request),
                current_jti=jti,
            )
        else:
            updated = UserSession.objects.filter(
                user=user, session_id=resolved_session_id
            ).update(current_jti=jti, last_used_at=timezone.now())
            if not updated:
                UserSession.objects.create(
                    user=user,
                    session_id=resolved_session_id,
                    device_label=device_label_from_user_agent(
                        request.META.get("HTTP_USER_AGENT", "")
                    ),
                    ip_address=client_ip_from_request(request),
                    current_jti=jti,
                )

    return str(access), str(refresh)
