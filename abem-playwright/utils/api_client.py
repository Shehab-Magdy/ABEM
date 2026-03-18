"""Thin wrapper around Playwright's APIRequestContext for ABEM API calls.

All HTTP communication goes through Playwright — no requests/httpx.
"""

from __future__ import annotations

import logging
from typing import Any

from playwright.sync_api import APIRequestContext, APIResponse

logger = logging.getLogger(__name__)


class APIClient:
    """Convenience wrapper that delegates to Playwright APIRequestContext."""

    def __init__(self, ctx: APIRequestContext, base_path: str = "/api/v1") -> None:
        self._ctx = ctx
        self._base = base_path

    def _url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        if path.startswith("/api/"):
            return path
        return f"{self._base}/{path.lstrip('/')}"

    # ── HTTP verbs ────────────────────────────────────────────

    def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        url = self._url(path)
        logger.debug("GET %s params=%s", url, params)
        return self._ctx.get(url, params=params, headers=headers)

    def post(
        self,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        multipart: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        url = self._url(path)
        logger.debug("POST %s data=%s", url, data)
        if multipart is not None:
            return self._ctx.post(url, multipart=multipart, headers=headers)
        return self._ctx.post(url, data=data, headers=headers)

    def patch(
        self,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        url = self._url(path)
        logger.debug("PATCH %s data=%s", url, data)
        return self._ctx.patch(url, data=data, headers=headers)

    def put(
        self,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> APIResponse:
        url = self._url(path)
        logger.debug("PUT %s data=%s", url, data)
        return self._ctx.put(url, data=data, headers=headers)

    def delete(
        self,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        data: dict[str, Any] | None = None,
    ) -> APIResponse:
        url = self._url(path)
        logger.debug("DELETE %s", url)
        return self._ctx.delete(url, headers=headers, data=data)

    # ── Auth helpers ──────────────────────────────────────────

    def login(self, email: str, password: str) -> dict[str, Any]:
        """POST /auth/login/ and return the JSON body."""
        resp = self.post("auth/login/", data={"email": email, "password": password})
        assert resp.status == 200, f"Login failed ({resp.status}): {resp.text()}"
        return resp.json()

    def logout(self, refresh_token: str) -> APIResponse:
        """POST /auth/logout/ with the refresh token."""
        return self.post("auth/logout/", data={"refresh": refresh_token})

    def refresh(self, refresh_token: str) -> dict[str, Any]:
        """POST /auth/refresh/ and return new tokens."""
        resp = self.post("auth/refresh/", data={"refresh": refresh_token})
        return resp.json()

    # ── Convenience ───────────────────────────────────────────

    @property
    def context(self) -> APIRequestContext:
        """Direct access to the underlying Playwright context."""
        return self._ctx
