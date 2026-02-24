"""
User Management API wrapper — covers every /users/* endpoint.

Maps to backend/apps/authentication/user_views.py (Sprint 1).

Endpoint reference:
    GET    /users/                    → list users
    POST   /users/                    → create user (admin)
    GET    /users/{id}/               → get user by id
    PATCH  /users/{id}/               → update user
    DELETE /users/{id}/               → delete user
    POST   /users/{id}/deactivate/    → deactivate user
    POST   /users/{id}/activate/      → activate user
    POST   /users/{id}/reset-password/ → admin reset password
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from requests import Response

from core.api_client import APIClient
from utils.logger import get_logger

logger = get_logger(__name__)


class UserAPI:
    """Thin wrappers around every /users/* endpoint."""

    def __init__(self, client: APIClient):
        self._c = client

    # ── CRUD ───────────────────────────────────────────────────────────────────

    def list_users(
        self,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Response:
        """
        GET /users/

        Supports server-side filtering and pagination.
        Expected responses:
          200 – paginated {"count": n, "results": [...]}
          401 – not authenticated
          403 – caller is not admin
        """
        params: dict = {"page": page, "page_size": page_size}
        if role:
            params["role"] = role
        if is_active is not None:
            params["is_active"] = str(is_active).lower()
        if search:
            params["search"] = search
        return self._c.get("/users/", params=params)

    def get_user(self, user_id: str) -> Response:
        """GET /users/{id}/"""
        return self._c.get(f"/users/{user_id}/")

    def create_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role: str = "owner",
        phone: Optional[str] = None,
    ) -> Response:
        """
        POST /users/ (admin only — same as /auth/register/).

        Expected responses:
          201 – user created
          400 – duplicate email / weak password / validation error
          403 – not admin
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
        logger.info("Create user → %s (%s)", email, role)
        return self._c.post("/users/", json=payload)

    def update_user(self, user_id: str, **fields) -> Response:
        """
        PATCH /users/{id}/

        Pass any subset of updatable fields as keyword args:
          first_name, last_name, phone, is_active, role
        """
        return self._c.patch(f"/users/{user_id}/", json=fields)

    def delete_user(self, user_id: str) -> Response:
        """DELETE /users/{id}/"""
        return self._c.delete(f"/users/{user_id}/")

    # ── Custom actions ──────────────────────────────────────────────────────────

    def deactivate_user(self, user_id: str) -> Response:
        """
        POST /users/{id}/deactivate/

        Expected responses:
          200 – deactivated
          400 – cannot deactivate self
          403 – not admin
          404 – user not found
        """
        logger.info("Deactivate user %s", user_id)
        return self._c.post(f"/users/{user_id}/deactivate/")

    def activate_user(self, user_id: str) -> Response:
        """
        POST /users/{id}/activate/

        Expected responses:
          200 – activated
          403 – not admin
          404 – user not found
        """
        logger.info("Activate user %s", user_id)
        return self._c.post(f"/users/{user_id}/activate/")

    def reset_password(self, user_id: str, new_password: str) -> Response:
        """
        POST /users/{id}/reset-password/

        Admin resets another user's password.
        Expected responses:
          200 – password reset
          400 – password fails complexity
          403 – not admin
          404 – user not found
        """
        return self._c.post(
            f"/users/{user_id}/reset-password/",
            json={"new_password": new_password},
        )

    # ── Helpers ────────────────────────────────────────────────────────────────

    def create_and_get(self, **user_fields) -> dict:
        """Create a user and return the parsed JSON response body."""
        resp = self.create_user(**user_fields)
        assert resp.status_code == 201, f"Create failed: {resp.text}"
        return resp.json()

    def list_all(self, **filters) -> list:
        """Return all user objects (handles pagination automatically)."""
        results = []
        page = 1
        while True:
            resp = self.list_users(page=page, page_size=100, **filters)
            data = resp.json()
            results.extend(data.get("results", []))
            if not data.get("next"):
                break
            page += 1
        return results
