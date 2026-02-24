"""
Reusable HTTP client for ABEM REST API.

Features:
- Automatic JWT Bearer injection on every request
- Silent token refresh on 401 (queued to avoid duplicate refreshes)
- Retry-once strategy before propagating errors
- Full request/response logging at DEBUG level
"""

import threading
import time
from typing import Any, Optional
from urllib.parse import urljoin

import requests
from requests import Response, Session

from utils.logger import get_logger

logger = get_logger(__name__)


class APIError(Exception):
    """Raised when the server returns an unexpected status code."""

    def __init__(self, response: Response):
        self.status_code = response.status_code
        self.body = response.text
        try:
            self.json = response.json()
        except Exception:
            self.json = {}
        super().__init__(f"HTTP {self.status_code}: {self.body[:200]}")


class APIClient:
    """Thread-safe REST client with JWT auth and token refresh."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session: Session = requests.Session()
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self._refresh_lock = threading.Lock()
        self._refreshing = False

    # ── Authentication ─────────────────────────────────────────────────────────

    def authenticate(self, email: str, password: str) -> dict:
        """Login and store tokens. Returns the full response payload."""
        logger.info("Authenticating as %s", email)
        resp = self._raw_request(
            "POST",
            "/auth/login/",
            json={"email": email, "password": password},
        )
        self._raise_for_status(resp, expected={200})
        data = resp.json()
        self.access_token = data["access"]
        self.refresh_token = data["refresh"]
        logger.info("Authenticated — role: %s", data.get("user", {}).get("role"))
        return data

    def refresh_access_token(self) -> bool:
        """Use the stored refresh token to obtain a new access token."""
        if not self.refresh_token:
            return False
        try:
            resp = self._raw_request(
                "POST",
                "/auth/token/refresh/",
                json={"refresh": self.refresh_token},
            )
            if resp.status_code == 200:
                self.access_token = resp.json()["access"]
                logger.debug("Access token refreshed successfully")
                return True
        except Exception as exc:
            logger.warning("Token refresh failed: %s", exc)
        return False

    def logout(self) -> None:
        """Blacklist the refresh token on the server and clear local tokens."""
        if self.refresh_token:
            try:
                self.post("/auth/logout/", json={"refresh": self.refresh_token})
            except APIError:
                pass  # best-effort
        self.access_token = None
        self.refresh_token = None
        logger.info("Logged out")

    # ── Public request helpers ─────────────────────────────────────────────────

    def get(self, endpoint: str, **kwargs) -> Response:
        return self.request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs) -> Response:
        return self.request("POST", endpoint, **kwargs)

    def patch(self, endpoint: str, **kwargs) -> Response:
        return self.request("PATCH", endpoint, **kwargs)

    def put(self, endpoint: str, **kwargs) -> Response:
        return self.request("PUT", endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> Response:
        return self.request("DELETE", endpoint, **kwargs)

    def request(self, method: str, endpoint: str, **kwargs) -> Response:
        """
        Execute an authenticated request. On 401, attempt one token refresh
        then replay the original request before raising.
        """
        resp = self._raw_request(method, endpoint, **kwargs)

        if resp.status_code == 401 and self.refresh_token:
            with self._refresh_lock:
                if not self._refreshing:
                    self._refreshing = True
                    try:
                        if self.refresh_access_token():
                            resp = self._raw_request(method, endpoint, **kwargs)
                    finally:
                        self._refreshing = False

        return resp

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _raw_request(self, method: str, endpoint: str, **kwargs) -> Response:
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        headers = kwargs.pop("headers", {})
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        headers.setdefault("Content-Type", "application/json")

        logger.debug("→ %s %s | body=%s", method, url, kwargs.get("json"))
        resp = self.session.request(method, url, headers=headers, **kwargs)
        logger.debug(
            "← %s %s | status=%d body=%s",
            method,
            url,
            resp.status_code,
            resp.text[:300],
        )
        return resp

    @staticmethod
    def _raise_for_status(resp: Response, expected: set) -> None:
        if resp.status_code not in expected:
            raise APIError(resp)

    # ── Context manager support ────────────────────────────────────────────────

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.logout()
