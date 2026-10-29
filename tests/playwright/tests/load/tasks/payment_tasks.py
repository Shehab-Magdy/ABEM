"""Payment-related Locust task helpers.

Encapsulates payment recording and listing logic for reuse across
load test scenarios.
"""

from __future__ import annotations

import random
from datetime import date
from typing import Any
from uuid import uuid4

from locust.clients import HttpSession

PAYMENTS_ENDPOINT = "/api/v1/payments/"


def record_payment_task(
    client: HttpSession,
    headers: dict[str, str],
    *,
    apartment_id: str | None = None,
) -> dict[str, Any] | None:
    """POST a randomly-generated payment.

    When *apartment_id* is ``None`` the function fetches the first
    available apartment from the API.

    Returns:
        The created payment dict on success, or ``None`` on failure.
    """
    if apartment_id is None:
        apartment_id = _fetch_first_apartment_id(client, headers)

    payload = {
        "apartment_id": apartment_id,
        "amount_paid": str(random.randint(100, 5_000)),
        "payment_method": random.choice(["cash", "bank_transfer", "cheque"]),
        "payment_date": date.today().isoformat(),
        "notes": f"load_test_{uuid4().hex[:8]}",
    }

    with client.post(
        PAYMENTS_ENDPOINT,
        json=payload,
        headers=headers,
        name="POST /payments/",
        catch_response=True,
    ) as resp:
        if resp.status_code != 201:
            resp.failure(
                f"Record payment failed ({resp.status_code}): "
                f"{resp.text[:200]}"
            )
            return None
        content_type = resp.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            resp.failure(f"Unexpected Content-Type: {content_type}")
            return None
        resp.success()
        return resp.json()


def get_payments_task(
    client: HttpSession,
    headers: dict[str, str],
) -> dict[str, Any] | None:
    """GET paginated payment list.

    Returns:
        The JSON response body on success, or ``None`` on failure.
    """
    with client.get(
        f"{PAYMENTS_ENDPOINT}?page_size=20",
        headers=headers,
        name="GET /payments/",
        catch_response=True,
    ) as resp:
        if resp.status_code != 200:
            resp.failure(f"Get payments failed ({resp.status_code})")
            return None
        content_type = resp.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            resp.failure(f"Unexpected Content-Type: {content_type}")
            return None
        resp.success()
        return resp.json()


# ── Internal helpers ─────────────────────────────────────────────


def _fetch_first_apartment_id(
    client: HttpSession,
    headers: dict[str, str],
) -> str:
    """Return the ID of the first apartment from the apartments list."""
    with client.get(
        "/api/v1/apartments/",
        headers=headers,
        name="GET /apartments/ (lookup)",
        catch_response=True,
    ) as resp:
        if resp.status_code != 200:
            resp.failure(f"Apartment lookup failed ({resp.status_code})")
            return ""
        data = resp.json()
        results = data if isinstance(data, list) else data.get("results", [])
        resp.success()
        return str(results[0]["id"]) if results else ""
