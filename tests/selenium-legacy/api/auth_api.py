"""
Auth API wrapper — thin methods over every /auth/* endpoint.

Maps to backend/apps/authentication/views.py (Sprint 1).

Endpoint reference:
    POST /auth/login/           → login
    POST /auth/logout/          → logout
    POST /auth/token/refresh/   → refresh_token
    POST /auth/register/        → register (admin only)
    POST /auth/change-password/ → change_password
    GET  /auth/profile/         → get_profile
    PATCH /auth/profile/        → update_profile
"""

from __future__ import annotations

from typing import Optional

from requests import Response

from core.api_client import APIClient
from utils.logger import get_logger

logger = get_logger(__name__)


class AuthAPI:
    """Thin, stateless wrappers around every /auth/* endpoint."""

    def __init__(self, client: APIClient):
        self._c = client

    # ── Login / Logout / Refresh ────────────────────────────────────────────────

    def login(self, email: str, password: str) -> Response:
        """
        POST /auth/login/

        Expected responses:
          200 – {"access": "...", "refresh": "...", "user": {...}}
          400 – validation error (missing fields)
          401 – wrong credentials
          423 – account locked
        """
        logger.info("Login → %s", email)
        return self._c.session.post(
            f"{self._c.base_url}/auth/login/",
            json={"email": email, "password": password},
        )

    def logout(self, refresh_token: str) -> Response:
        """POST /auth/logout/ — blacklists the refresh token."""
        return self._c.post(
            "/auth/logout/",
            json={"refresh": refresh_token},
        )

    def refresh_token(self, refresh: str) -> Response:
        """POST /auth/refresh/ — exchange refresh for new access token."""
        return self._c.session.post(
            f"{self._c.base_url}/auth/refresh/",
            json={"refresh": refresh},
        )

    # ── Registration ────────────────────────────────────────────────────────────

    def register(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role: str = "owner",
        phone: Optional[str] = None,
    ) -> Response:
        """
        POST /auth/register/ — admin only.

        Expected responses:
          201 – user created
          400 – validation error / duplicate email
          403 – caller is not admin
        """
        payload: dict = {
            "email": email,
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
            "role": role,
        }
        if phone:
            payload["phone"] = phone
        return self._c.post("/auth/register/", json=payload)

    def self_register(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role: str = "owner",
        phone: Optional[str] = None,
        confirm_password: Optional[str] = None,
    ) -> Response:
        """
        POST /auth/self-register/ — public (AllowAny).

        Caller chooses role: 'admin' or 'owner'.

        Expected responses:
          201 – {"access": "...", "refresh": "...", "user": {...}}
          400 – validation error (missing fields, weak password, duplicate email)
        """
        payload: dict = {
            "email": email,
            "password": password,
            "confirm_password": confirm_password or password,
            "first_name": first_name,
            "last_name": last_name,
            "role": role,
        }
        if phone:
            payload["phone"] = phone
        logger.info("Self-register → %s (role=%s)", email, role)
        return self._c.session.post(
            f"{self._c.base_url}/auth/self-register/",
            json=payload,
        )

    # ── Password management ─────────────────────────────────────────────────────

    def change_password(
        self,
        current_password: str,
        new_password: str,
        confirm_password: Optional[str] = None,
    ) -> Response:
        """
        PATCH /auth/change-password/

        Expected responses:
          200 – password changed
          400 – current password wrong / new password fails complexity
          401 – not authenticated
        """
        payload = {
            "current_password": current_password,
            "new_password": new_password,
            "confirm_password": confirm_password or new_password,
        }
        return self._c.patch("/auth/change-password/", json=payload)

    # ── Profile ────────────────────────────────────────────────────────────────

    def get_profile(self) -> Response:
        """GET /auth/profile/ — returns authenticated user's profile."""
        return self._c.get("/auth/profile/")

    def update_profile(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> Response:
        """
        PATCH /auth/profile/

        Expected responses:
          200 – profile updated
          400 – validation error
          401 – not authenticated
        """
        payload = {}
        if first_name is not None:
            payload["first_name"] = first_name
        if last_name is not None:
            payload["last_name"] = last_name
        if phone is not None:
            payload["phone"] = phone
        return self._c.patch("/auth/profile/", json=payload)

    # ── Token introspection ────────────────────────────────────────────────────

    @staticmethod
    def decode_token_claims(access_token: str) -> dict:
        """
        Decode JWT payload without signature verification.
        Useful for asserting custom claims (role, tenant_ids, user_id).
        """
        import base64
        import json

        payload_b64 = access_token.split(".")[1]
        # Pad Base64 string
        padding = 4 - len(payload_b64) % 4
        payload_b64 += "=" * padding
        decoded = base64.urlsafe_b64decode(payload_b64)
        return json.loads(decoded)
