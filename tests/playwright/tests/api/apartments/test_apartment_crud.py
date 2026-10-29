"""API tests for apartment CRUD operations."""

import pytest
from playwright.sync_api import APIRequestContext

from utils.data_factory import build_apartment, build_store, unique_prefix


@pytest.mark.api
@pytest.mark.apartments
class TestApartmentCRUD:

    def test_create_apartment(self, admin_api: APIRequestContext, seeded_building):
        bid = seeded_building["building"]["id"]
        payload = build_apartment(bid)
        resp = admin_api.post("/api/v1/apartments/", data=payload)
        assert resp.status == 201
        body = resp.json()
        assert "id" in body
        admin_api.delete(f"/api/v1/apartments/{body['id']}/")

    def test_list_apartments_by_building(
        self, admin_api: APIRequestContext, seeded_building
    ):
        bid = seeded_building["building"]["id"]
        resp = admin_api.get("/api/v1/apartments/", params={"building_id": bid})
        assert resp.status == 200
        body = resp.json()
        results = body.get("results", body) if isinstance(body, dict) else body
        assert len(results) >= 2  # at least auto-created apartment + store

    def test_get_apartment_by_id(self, admin_api: APIRequestContext, seeded_building):
        apt = seeded_building["apartment"]
        if apt is None:
            pytest.skip("No apartment in seeded building")
        resp = admin_api.get(f"/api/v1/apartments/{apt['id']}/")
        assert resp.status == 200

    def test_update_apartment(self, admin_api: APIRequestContext, seeded_building):
        apt = seeded_building["apartment"]
        if apt is None:
            pytest.skip("No apartment")
        new_number = f"U-{unique_prefix()[:6]}"
        resp = admin_api.patch(
            f"/api/v1/apartments/{apt['id']}/",
            data={"unit_number": new_number},
        )
        assert resp.status == 200

    def test_delete_apartment(self, admin_api: APIRequestContext, seeded_building):
        bid = seeded_building["building"]["id"]
        apt = admin_api.post(
            "/api/v1/apartments/", data=build_apartment(bid)
        ).json()
        resp = admin_api.delete(f"/api/v1/apartments/{apt['id']}/")
        assert resp.status in (200, 204)

    # ── Negative ──────────────────────────────────────────────

    def test_create_without_building_id(self, admin_api: APIRequestContext):
        payload = {"unit_number": "X1", "floor": 1, "type": "apartment"}
        resp = admin_api.post("/api/v1/apartments/", data=payload)
        assert resp.status == 400

    def test_create_without_unit_number(
        self, admin_api: APIRequestContext, seeded_building
    ):
        bid = seeded_building["building"]["id"]
        payload = {"building_id": bid, "floor": 1, "type": "apartment"}
        resp = admin_api.post("/api/v1/apartments/", data=payload)
        assert resp.status == 400

    def test_create_duplicate_unit_number(
        self, admin_api: APIRequestContext, seeded_building
    ):
        apt = seeded_building["apartment"]
        if apt is None:
            pytest.skip("No apartment")
        bid = seeded_building["building"]["id"]
        unit_number = apt.get("unit_number", "A-001")
        payload = build_apartment(bid, unit_number=unit_number)
        resp = admin_api.post("/api/v1/apartments/", data=payload)
        assert resp.status in (400, 409)

    def test_owner_cannot_create(self, owner_api: APIRequestContext, seeded_building):
        bid = seeded_building["building"]["id"]
        payload = build_apartment(bid)
        resp = owner_api.post("/api/v1/apartments/", data=payload)
        assert resp.status == 403

    def test_get_nonexistent(self, admin_api: APIRequestContext):
        resp = admin_api.get(
            "/api/v1/apartments/00000000-0000-0000-0000-000000000000/"
        )
        assert resp.status == 404
