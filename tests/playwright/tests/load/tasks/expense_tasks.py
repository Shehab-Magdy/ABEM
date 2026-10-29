"""Expense-related Locust task helpers.

Encapsulates expense creation and listing logic so the main locustfile
stays clean and tasks can be reused across scenarios.
"""

from __future__ import annotations

import random
from datetime import date
from typing import Any
from uuid import uuid4

from locust.clients import HttpSession

EXPENSES_ENDPOINT = "/api/v1/expenses/"


def create_expense_task(
    client: HttpSession,
    headers: dict[str, str],
    *,
    building_id: str | None = None,
    category_id: str | None = None,
) -> dict[str, Any] | None:
    """POST a randomly-generated expense.

    When *building_id* or *category_id* are ``None`` the function
    fetches the first available building / category from the API.

    Returns:
        The created expense dict on success, or ``None`` on failure.
    """
    if building_id is None:
        building_id = _fetch_first_building_id(client, headers)
    if category_id is None:
        category_id = _fetch_first_category_id(client, headers)

    payload = {
        "title": f"load_test_{uuid4().hex[:8]}",
        "amount": str(random.randint(500, 10_000)),
        "expense_date": date.today().isoformat(),
        "building_id": building_id,
        "category_id": category_id,
        "split_type": "equal_all",
    }

    with client.post(
        EXPENSES_ENDPOINT,
        json=payload,
        headers=headers,
        name="POST /expenses/",
        catch_response=True,
    ) as resp:
        if resp.status_code != 201:
            resp.failure(
                f"Create expense failed ({resp.status_code}): "
                f"{resp.text[:200]}"
            )
            return None
        content_type = resp.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            resp.failure(f"Unexpected Content-Type: {content_type}")
            return None
        resp.success()
        return resp.json()


def get_expenses_task(
    client: HttpSession,
    headers: dict[str, str],
) -> dict[str, Any] | None:
    """GET paginated expense list.

    Returns:
        The JSON response body on success, or ``None`` on failure.
    """
    with client.get(
        f"{EXPENSES_ENDPOINT}?page_size=20",
        headers=headers,
        name="GET /expenses/",
        catch_response=True,
    ) as resp:
        if resp.status_code != 200:
            resp.failure(f"Get expenses failed ({resp.status_code})")
            return None
        content_type = resp.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            resp.failure(f"Unexpected Content-Type: {content_type}")
            return None
        resp.success()
        return resp.json()


# ── Internal helpers ─────────────────────────────────────────────


def _fetch_first_building_id(
    client: HttpSession,
    headers: dict[str, str],
) -> str:
    """Return the ID of the first building from the buildings list."""
    with client.get(
        "/api/v1/buildings/",
        headers=headers,
        name="GET /buildings/ (lookup)",
        catch_response=True,
    ) as resp:
        if resp.status_code != 200:
            resp.failure(f"Building lookup failed ({resp.status_code})")
            return ""
        data = resp.json()
        results = data if isinstance(data, list) else data.get("results", [])
        resp.success()
        return str(results[0]["id"]) if results else ""


def _fetch_first_category_id(
    client: HttpSession,
    headers: dict[str, str],
) -> str:
    """Return the ID of the first expense category."""
    with client.get(
        "/api/v1/categories/",
        headers=headers,
        name="GET /categories/ (lookup)",
        catch_response=True,
    ) as resp:
        if resp.status_code != 200:
            resp.failure(f"Category lookup failed ({resp.status_code})")
            return ""
        data = resp.json()
        results = data if isinstance(data, list) else data.get("results", [])
        resp.success()
        return str(results[0]["id"]) if results else ""
