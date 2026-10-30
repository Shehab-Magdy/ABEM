"""Building and apartment create/teardown fixtures."""

from __future__ import annotations

import logging

import pytest
from playwright.sync_api import APIRequestContext

from utils.data_factory import build_apartment, build_building, build_store

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def create_building(admin_api: APIRequestContext):
    """Factory fixture: create buildings and clean up on teardown."""
    created_ids: list[str] = []

    def _create(**overrides) -> dict:
        payload = build_building(**overrides)
        resp = admin_api.post("/api/v1/buildings/", data=payload)
        assert resp.status == 201, f"Create building failed: {resp.text()}"
        data = resp.json()
        created_ids.append(data["id"])
        logger.info("Created building %s (%s)", data["id"], data["name"])
        return data

    yield _create

    for bid in reversed(created_ids):
        resp = admin_api.delete(f"/api/v1/buildings/{bid}/")
        logger.debug("Deleted building %s (status=%s)", bid, resp.status)


@pytest.fixture(scope="function")
def create_apartment(admin_api: APIRequestContext):
    """Factory fixture: create apartments and clean up on teardown."""
    created_ids: list[str] = []

    def _create(building_id: str, **overrides) -> dict:
        payload = build_apartment(building_id, **overrides)
        resp = admin_api.post("/api/v1/apartments/", data=payload)
        assert resp.status == 201, f"Create apartment failed: {resp.text()}"
        data = resp.json()
        created_ids.append(data["id"])
        logger.info("Created apartment %s (%s)", data["id"], data.get("unit_number"))
        return data

    yield _create

    for aid in reversed(created_ids):
        resp = admin_api.delete(f"/api/v1/apartments/{aid}/")
        logger.debug("Deleted apartment %s (status=%s)", aid, resp.status)


@pytest.fixture(scope="function")
def seeded_building(admin_api: APIRequestContext):
    """Create a building with two apartments (one Apartment, one Store).

    Yields a dict with keys: building, apartments, apartment, store.
    """
    # Create building with auto-generated units
    building_payload = build_building(num_apartments=1, num_stores=1)
    resp = admin_api.post("/api/v1/buildings/", data=building_payload)
    assert resp.status == 201, f"Seed building failed: {resp.text()}"
    building = resp.json()
    building_id = building["id"]

    # Fetch auto-created apartments
    apt_resp = admin_api.get(
        "/api/v1/apartments/", params={"building_id": building_id}
    )
    assert apt_resp.status == 200
    apts = apt_resp.json()
    apt_list = apts.get("results", apts) if isinstance(apts, dict) else apts

    apartment = None
    store = None
    for a in apt_list:
        unit_type = a.get("type", a.get("unit_type", ""))
        if unit_type == "apartment" and apartment is None:
            apartment = a
        elif unit_type == "store" and store is None:
            store = a

    result = {
        "building": building,
        "apartments": apt_list,
        "apartment": apartment,
        "store": store,
    }

    yield result

    # Teardown
    admin_api.delete(f"/api/v1/buildings/{building_id}/")
    logger.info("Tore down seeded building %s", building_id)
