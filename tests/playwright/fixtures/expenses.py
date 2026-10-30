"""Expense create/teardown fixtures."""

from __future__ import annotations

import logging

import pytest
from playwright.sync_api import APIRequestContext

from utils.data_factory import build_expense

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def create_expense(admin_api: APIRequestContext):
    """Factory fixture: create expenses and clean up on teardown."""
    created_ids: list[str] = []

    def _create(building_id: str, category_id: str, **overrides) -> dict:
        payload = build_expense(building_id, category_id, **overrides)
        resp = admin_api.post("/api/v1/expenses/", data=payload)
        assert resp.status == 201, f"Create expense failed: {resp.text()}"
        data = resp.json()
        created_ids.append(data["id"])
        logger.info("Created expense %s (%s)", data["id"], data.get("title"))
        return data

    yield _create

    for eid in reversed(created_ids):
        resp = admin_api.delete(f"/api/v1/expenses/{eid}/")
        logger.debug("Deleted expense %s (status=%s)", eid, resp.status)


@pytest.fixture(scope="function")
def seeded_expense(admin_api: APIRequestContext, seeded_building: dict):
    """Create an expense in the seeded building with its first category.

    Yields a dict with expense data and parent building info.
    """
    building = seeded_building["building"]
    building_id = building["id"]

    # Fetch a category for the building
    cat_resp = admin_api.get(
        "/api/v1/expenses/categories/",
        params={"building_id": building_id},
    )
    assert cat_resp.status == 200, f"Fetch categories failed: {cat_resp.text()}"
    categories = cat_resp.json()
    cat_list = categories.get("results", categories) if isinstance(categories, dict) else categories
    assert len(cat_list) > 0, "No categories found for seeded building"
    category = cat_list[0]

    # Create expense
    payload = build_expense(building_id, category["id"], amount="101")
    resp = admin_api.post("/api/v1/expenses/", data=payload)
    assert resp.status == 201, f"Seed expense failed: {resp.text()}"
    expense = resp.json()

    result = {
        "expense": expense,
        "building": building,
        "category": category,
        "apartments": seeded_building["apartments"],
        "apartment": seeded_building["apartment"],
        "store": seeded_building["store"],
    }

    yield result

    admin_api.delete(f"/api/v1/expenses/{expense['id']}/")
    logger.info("Tore down seeded expense %s", expense["id"])
