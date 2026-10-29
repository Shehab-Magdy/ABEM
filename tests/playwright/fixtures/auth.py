"""Authentication fixtures — JWT token acquisition for admin and owner roles."""

from __future__ import annotations

import logging

import pytest
from playwright.sync_api import APIRequestContext, Playwright

from config.settings import settings

logger = logging.getLogger(__name__)

# ── Session-level token cache ─────────────────────────────────
_token_cache: dict[str, dict] = {}


def _get_cached_tokens(
    playwright: Playwright,
    email: str,
    password: str,
    cache_key: str,
) -> dict:
    """Authenticate once per session and cache the tokens."""
    if cache_key in _token_cache:
        return _token_cache[cache_key]

    ctx = playwright.request.new_context(base_url=settings.API_BASE_URL)
    try:
        resp = ctx.post(
            "/api/v1/auth/login/",
            data={"email": email, "password": password},
        )
        assert resp.status == 200, (
            f"Auth failed for {email} ({resp.status}): {resp.text()}"
        )
        tokens = resp.json()
        _token_cache[cache_key] = tokens
        logger.info("Cached %s tokens for session", cache_key)
        return tokens
    finally:
        ctx.dispose()


@pytest.fixture(scope="function")
def admin_token(playwright: Playwright) -> str:
    """Return the admin JWT access token (session-cached)."""
    tokens = _get_cached_tokens(
        playwright,
        settings.ADMIN_EMAIL,
        settings.ADMIN_PASSWORD,
        "admin",
    )
    return tokens["access"]


@pytest.fixture(scope="function")
def owner_token(playwright: Playwright) -> str:
    """Return the owner JWT access token (session-cached)."""
    tokens = _get_cached_tokens(
        playwright,
        settings.OWNER_EMAIL,
        settings.OWNER_PASSWORD,
        "owner",
    )
    return tokens["access"]


@pytest.fixture(scope="function")
def admin_tokens(playwright: Playwright) -> dict:
    """Return the full admin token dict {access, refresh, user}."""
    return _get_cached_tokens(
        playwright,
        settings.ADMIN_EMAIL,
        settings.ADMIN_PASSWORD,
        "admin",
    )


@pytest.fixture(scope="function")
def owner_tokens(playwright: Playwright) -> dict:
    """Return the full owner token dict {access, refresh, user}."""
    return _get_cached_tokens(
        playwright,
        settings.OWNER_EMAIL,
        settings.OWNER_PASSWORD,
        "owner",
    )


@pytest.fixture(scope="function")
def admin_api(playwright: Playwright, admin_token: str) -> APIRequestContext:
    """Playwright APIRequestContext with admin Authorization header."""
    ctx = playwright.request.new_context(
        base_url=settings.API_BASE_URL,
        extra_http_headers={
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json",
        },
    )
    yield ctx
    ctx.dispose()


@pytest.fixture(scope="function")
def owner_api(playwright: Playwright, owner_token: str) -> APIRequestContext:
    """Playwright APIRequestContext with owner Authorization header."""
    ctx = playwright.request.new_context(
        base_url=settings.API_BASE_URL,
        extra_http_headers={
            "Authorization": f"Bearer {owner_token}",
            "Content-Type": "application/json",
        },
    )
    yield ctx
    ctx.dispose()


@pytest.fixture(scope="function")
def second_admin_api(playwright: Playwright) -> APIRequestContext:
    """APIRequestContext for a second independent admin account."""
    tokens = _get_cached_tokens(
        playwright,
        settings.ADMIN2_EMAIL,
        settings.ADMIN2_PASSWORD,
        "admin2",
    )
    ctx = playwright.request.new_context(
        base_url=settings.API_BASE_URL,
        extra_http_headers={
            "Authorization": f"Bearer {tokens['access']}",
            "Content-Type": "application/json",
        },
    )
    yield ctx
    ctx.dispose()


@pytest.fixture(scope="function")
def unauthenticated_api(playwright: Playwright) -> APIRequestContext:
    """Playwright APIRequestContext with no auth headers."""
    ctx = playwright.request.new_context(
        base_url=settings.API_BASE_URL,
        extra_http_headers={"Content-Type": "application/json"},
    )
    yield ctx
    ctx.dispose()
