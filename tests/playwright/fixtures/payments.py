"""Payment create/teardown fixtures."""

from __future__ import annotations

import logging

import pytest
from playwright.sync_api import APIRequestContext

from utils.data_factory import build_payment

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def create_payment(admin_api: APIRequestContext):
    """Factory fixture: record payments (immutable — no teardown delete)."""
    created_ids: list[str] = []

    def _create(apartment_id: str, **overrides) -> dict:
        payload = build_payment(apartment_id, **overrides)
        resp = admin_api.post("/api/v1/payments/", data=payload)
        assert resp.status == 201, f"Create payment failed: {resp.text()}"
        data = resp.json()
        created_ids.append(data["id"])
        logger.info("Recorded payment %s (amount=%s)", data["id"], data.get("amount_paid"))
        return data

    yield _create

    # Payments are immutable — no DELETE. Log for traceability.
    for pid in created_ids:
        logger.debug("Payment %s created during test (immutable, not deleted)", pid)


@pytest.fixture(scope="function")
def seeded_payment(admin_api: APIRequestContext, seeded_expense: dict):
    """Record a partial payment in the seeded context.

    Yields a dict with payment data and parent entities.
    """
    apartment = seeded_expense.get("apartment")
    if apartment is None:
        pytest.skip("No apartment in seeded building for payment fixture")

    apartment_id = apartment["id"]
    expense = seeded_expense["expense"]

    payload = build_payment(
        apartment_id,
        amount_paid="20",
        payment_method="cash",
        expense_ids=[expense["id"]],
    )
    resp = admin_api.post("/api/v1/payments/", data=payload)
    assert resp.status == 201, f"Seed payment failed: {resp.text()}"
    payment = resp.json()

    result = {
        "payment": payment,
        "expense": expense,
        "building": seeded_expense["building"],
        "apartment": apartment,
        "store": seeded_expense.get("store"),
        "category": seeded_expense["category"],
    }

    yield result

    logger.info("Seeded payment %s (immutable, not deleted)", payment["id"])
