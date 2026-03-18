"""Expense category fixtures and seed verification helpers."""

from __future__ import annotations

import logging

import pytest
from playwright.sync_api import APIRequestContext

from utils.data_factory import build_category

logger = logging.getLogger(__name__)

# Default category names auto-created per building
DEFAULT_CATEGORY_NAMES = [
    "Maintenance",
    "Utilities",
    "Cleaning",
    "Security",
    "Elevator",
    "Plumbing",
    "Internet & Cable",
    "Parking",
    "Landscaping",
    "Pest Control",
    "Fire Safety",
    "Waste Management",
    "Insurance",
    "Management",
    "Other",
]


@pytest.fixture(scope="function")
def create_category(admin_api: APIRequestContext):
    """Factory fixture: create custom expense categories."""
    created_ids: list[str] = []

    def _create(building_id: str, **overrides) -> dict:
        payload = build_category(building_id, **overrides)
        resp = admin_api.post("/api/v1/expenses/categories/", data=payload)
        assert resp.status == 201, f"Create category failed: {resp.text()}"
        data = resp.json()
        created_ids.append(data["id"])
        logger.info("Created category %s (%s)", data["id"], data.get("name"))
        return data

    yield _create

    for cid in reversed(created_ids):
        resp = admin_api.delete(f"/api/v1/expenses/categories/{cid}/")
        logger.debug("Deleted category %s (status=%s)", cid, resp.status)


@pytest.fixture(scope="function")
def building_categories(admin_api: APIRequestContext, seeded_building: dict) -> list[dict]:
    """Return the list of categories for the seeded building."""
    building_id = seeded_building["building"]["id"]
    resp = admin_api.get(
        "/api/v1/expenses/categories/",
        params={"building_id": building_id},
    )
    assert resp.status == 200
    data = resp.json()
    return data.get("results", data) if isinstance(data, dict) else data


def get_category_by_name(categories: list[dict], name: str) -> dict | None:
    """Find a category by name (case-insensitive)."""
    for cat in categories:
        if cat.get("name", "").lower() == name.lower():
            return cat
    return None
