"""Dashboard-related Locust task helpers.

Provides admin and owner dashboard fetch utilities with response
validation for reuse across load test scenarios.
"""

from __future__ import annotations

from typing import Any

from locust.clients import HttpSession

ADMIN_DASHBOARD_ENDPOINT = "/api/v1/dashboard/admin/"
OWNER_DASHBOARD_ENDPOINT = "/api/v1/dashboard/owner/"


def get_admin_dashboard(
    client: HttpSession,
    headers: dict[str, str],
) -> dict[str, Any] | None:
    """GET the admin dashboard aggregations.

    Returns:
        The JSON response body on success, or ``None`` on failure.
    """
    with client.get(
        ADMIN_DASHBOARD_ENDPOINT,
        headers=headers,
        name="GET /dashboard/admin/",
        catch_response=True,
    ) as resp:
        if resp.status_code != 200:
            resp.failure(f"Admin dashboard failed ({resp.status_code})")
            return None
        content_type = resp.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            resp.failure(f"Unexpected Content-Type: {content_type}")
            return None
        resp.success()
        return resp.json()


def get_owner_dashboard(
    client: HttpSession,
    headers: dict[str, str],
) -> dict[str, Any] | None:
    """GET the owner dashboard view.

    Returns:
        The JSON response body on success, or ``None`` on failure.
    """
    with client.get(
        OWNER_DASHBOARD_ENDPOINT,
        headers=headers,
        name="GET /dashboard/owner/",
        catch_response=True,
    ) as resp:
        if resp.status_code != 200:
            resp.failure(f"Owner dashboard failed ({resp.status_code})")
            return None
        content_type = resp.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            resp.failure(f"Unexpected Content-Type: {content_type}")
            return None
        resp.success()
        return resp.json()
