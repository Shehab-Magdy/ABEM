"""Locust load & stress test definitions for the ABEM REST API.

Two user personas simulate realistic traffic:

* **AdminUser** (weight 1) — admin operations: CRUD buildings, expenses,
  payments, dashboard, and audit log.
* **OwnerUser** (weight 3) — owner operations: dashboard, expense list,
  payment list, and notifications.

Token management is handled per-instance via JWT inspection.  When an
access token is within 60 s of expiry the user transparently refreshes
it; if the refresh fails the user re-authenticates from scratch.

Environment variables (sourced via python-dotenv):
    ADMIN_EMAIL, ADMIN_PASSWORD   — admin credentials
    OWNER_EMAIL, OWNER_PASSWORD   — owner credentials
    BUILDING_ID                   — (optional) fixed building for expenses
    LOCUST_HOST                   — API base URL (e.g. http://localhost:8000)
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any

# Ensure the abem-playwright root is on sys.path for absolute imports
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv
from locust import HttpUser, between, task

from tests.load.tasks.auth_tasks import (
    is_token_expiring,
    login,
    refresh_token,
)
from tests.load.tasks.dashboard_tasks import get_admin_dashboard, get_owner_dashboard
from tests.load.tasks.expense_tasks import create_expense_task, get_expenses_task
from tests.load.tasks.payment_tasks import get_payments_task

load_dotenv()

logger = logging.getLogger(__name__)

# ── Environment configuration ───────────────────────────────────

ADMIN_EMAIL: str = os.environ.get("ADMIN_EMAIL", "admin@abem.test")
ADMIN_PASSWORD: str = os.environ.get("ADMIN_PASSWORD", "Admin@123!")
OWNER_EMAIL: str = os.environ.get("OWNER_EMAIL", "owner@abem.test")
OWNER_PASSWORD: str = os.environ.get("OWNER_PASSWORD", "Owner@123!")
BUILDING_ID: str | None = os.environ.get("BUILDING_ID")


# ── Response validation helper ──────────────────────────────────


def _validate_response(response: Any, *, expected_codes: tuple[int, ...] = (200, 201)) -> None:
    """Mark a Locust *response* as failure when it doesn't meet expectations.

    Checks:
    1. HTTP status code is within *expected_codes*.
    2. ``Content-Type`` contains ``application/json``.

    Called inside ``catch_response=True`` blocks created by the task
    helpers. Standalone tasks that bypass the helpers should call this
    directly.
    """
    if response.status_code not in expected_codes:
        response.failure(
            f"Unexpected status {response.status_code} "
            f"(expected one of {expected_codes})"
        )
        return

    content_type: str = response.headers.get("Content-Type", "")
    if "application/json" not in content_type:
        response.failure(f"Unexpected Content-Type: {content_type}")


# ── Base user with token management ─────────────────────────────


class _AuthenticatedUser(HttpUser):
    """Abstract base providing JWT lifecycle management.

    Subclasses must set ``_email`` and ``_password`` before calling
    ``super().on_start()``.
    """

    abstract = True
    host = os.environ.get("LOCUST_HOST", "http://localhost:8000")

    _email: str
    _password: str

    # Per-instance token storage (thread-safe — each greenlet gets its own
    # HttpUser instance).
    access_token: str = ""
    refresh_token_value: str = ""

    def on_start(self) -> None:
        """Authenticate and store tokens on first spawn."""
        self._do_login()

    # ── Token helpers ────────────────────────────────────────────

    def _do_login(self) -> None:
        """Perform a fresh login and store the resulting tokens."""
        tokens = login(self.client, self._email, self._password)
        self.access_token = tokens["access"]
        self.refresh_token_value = tokens["refresh"]

    def _ensure_valid_token(self) -> None:
        """Refresh or re-login if the access token is about to expire."""
        if not self.access_token or is_token_expiring(self.access_token, within_seconds=60):
            try:
                self.access_token = refresh_token(
                    self.client, self.refresh_token_value
                )
            except RuntimeError:
                logger.warning(
                    "Token refresh failed for %s — re-authenticating", self._email
                )
                self._do_login()

    @property
    def auth_headers(self) -> dict[str, str]:
        """Return an Authorization header dict with a valid bearer token."""
        self._ensure_valid_token()
        return {"Authorization": f"Bearer {self.access_token}"}


# ── Admin persona ────────────────────────────────────────────────


class AdminUser(_AuthenticatedUser):
    """Simulates an admin user performing management operations."""

    weight = 1
    wait_time = between(1, 3)

    _email = ADMIN_EMAIL
    _password = ADMIN_PASSWORD

    # Cached IDs so we don't look them up every request.
    _building_id: str | None = BUILDING_ID
    _category_id: str | None = None

    # ── Tasks ────────────────────────────────────────────────────

    @task(3)
    def list_buildings(self) -> None:
        """GET /api/v1/buildings/"""
        with self.client.get(
            "/api/v1/buildings/",
            headers=self.auth_headers,
            name="GET /buildings/",
            catch_response=True,
        ) as resp:
            _validate_response(resp)

    @task(3)
    def list_expenses(self) -> None:
        """GET /api/v1/expenses/?page_size=20"""
        get_expenses_task(self.client, self.auth_headers)

    @task(2)
    def list_payments(self) -> None:
        """GET /api/v1/payments/?page_size=20"""
        get_payments_task(self.client, self.auth_headers)

    @task(2)
    def admin_dashboard(self) -> None:
        """GET /api/v1/dashboard/admin/"""
        get_admin_dashboard(self.client, self.auth_headers)

    @task(1)
    def create_expense(self) -> None:
        """POST /api/v1/expenses/ with random data."""
        create_expense_task(
            self.client,
            self.auth_headers,
            building_id=self._building_id,
            category_id=self._category_id,
        )

    @task(1)
    def list_audit(self) -> None:
        """GET /api/v1/audit/"""
        with self.client.get(
            "/api/v1/audit/",
            headers=self.auth_headers,
            name="GET /audit/",
            catch_response=True,
        ) as resp:
            _validate_response(resp)


# ── Owner persona ────────────────────────────────────────────────


class OwnerUser(_AuthenticatedUser):
    """Simulates an owner user viewing their dashboards and lists."""

    weight = 3
    wait_time = between(1, 3)

    _email = OWNER_EMAIL
    _password = OWNER_PASSWORD

    # ── Tasks ────────────────────────────────────────────────────

    @task(4)
    def owner_dashboard(self) -> None:
        """GET /api/v1/dashboard/owner/"""
        get_owner_dashboard(self.client, self.auth_headers)

    @task(3)
    def list_expenses(self) -> None:
        """GET /api/v1/expenses/?page_size=20"""
        get_expenses_task(self.client, self.auth_headers)

    @task(3)
    def list_payments(self) -> None:
        """GET /api/v1/payments/?page_size=20"""
        get_payments_task(self.client, self.auth_headers)

    @task(1)
    def list_notifications(self) -> None:
        """GET /api/v1/notifications/"""
        with self.client.get(
            "/api/v1/notifications/",
            headers=self.auth_headers,
            name="GET /notifications/",
            catch_response=True,
        ) as resp:
            _validate_response(resp)
