"""JWT token management helpers for Locust load tests.

Provides login, token refresh, and expiry-check utilities used by
all HttpUser classes in the load test suite.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import jwt
from locust.clients import HttpSession

logger = logging.getLogger(__name__)

LOGIN_ENDPOINT = "/api/v1/auth/login/"
REFRESH_ENDPOINT = "/api/v1/auth/refresh/"


def login(session: HttpSession, email: str, password: str) -> dict[str, Any]:
    """Authenticate against the ABEM API and return the token payload.

    Returns:
        dict with ``access`` and ``refresh`` keys (plus any extras
        the API sends back, e.g. ``user``).

    Raises:
        AssertionError: when the login request does not return 200.
    """
    with session.post(
        LOGIN_ENDPOINT,
        json={"email": email, "password": password},
        name="POST /auth/login/",
        catch_response=True,
    ) as resp:
        if resp.status_code != 200:
            resp.failure(f"Login failed for {email} ({resp.status_code})")
            raise RuntimeError(f"Login failed for {email}: {resp.status_code}")
        tokens: dict[str, Any] = resp.json()
        resp.success()
        logger.info("Authenticated %s", email)
        return tokens


def refresh_token(session: HttpSession, refresh: str) -> str:
    """Exchange a refresh token for a new access token.

    Returns:
        The new access token string.

    Raises:
        RuntimeError: when the refresh request fails.
    """
    with session.post(
        REFRESH_ENDPOINT,
        json={"refresh": refresh},
        name="POST /auth/refresh/",
        catch_response=True,
    ) as resp:
        if resp.status_code != 200:
            resp.failure(f"Token refresh failed ({resp.status_code})")
            raise RuntimeError(f"Token refresh failed: {resp.status_code}")
        data: dict[str, Any] = resp.json()
        resp.success()
        logger.debug("Token refreshed successfully")
        return data["access"]


def is_token_expiring(token: str, within_seconds: int = 60) -> bool:
    """Check whether a JWT will expire within the given time window.

    Decodes without signature verification (test-only usage).
    Returns ``True`` if the token expires within *within_seconds* from now.
    """
    try:
        claims = jwt.decode(
            token,
            algorithms=["HS256"],
            options={"verify_signature": False},
        )
        exp: int = claims.get("exp", 0)
        return time.time() + within_seconds >= exp
    except jwt.DecodeError:
        logger.warning("Failed to decode JWT — treating as expired")
        return True
