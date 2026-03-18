"""API tests for building CRUD operations."""

import pytest
from playwright.sync_api import APIRequestContext

from utils.data_factory import build_building, unique_prefix


@pytest.mark.api
@pytest.mark.buildings
class TestBuildingCRUD:
    """CRUD tests for POST/GET/PATCH/DELETE /api/v1/buildings/."""

    # ── Positive tests ────────────────────────────────────────

    def test_create_building_with_required_fields(self, admin_api: APIRequestContext):
        payload = build_building()
        resp = admin_api.post("/api/v1/buildings/", data=payload)
        assert resp.status == 201
        body = resp.json()
        assert "id" in body
        assert body["name"] == payload["name"]
        # Cleanup
        admin_api.delete(f"/api/v1/buildings/{body['id']}/")

    def test_create_building_with_all_fields(self, admin_api: APIRequestContext):
        payload = build_building(city="Cairo", country="Egypt", num_floors=10)
        resp = admin_api.post("/api/v1/buildings/", data=payload)
        assert resp.status == 201
        body = resp.json()
        assert body["city"] == "Cairo"
        admin_api.delete(f"/api/v1/buildings/{body['id']}/")

    def test_list_buildings(self, admin_api: APIRequestContext):
        resp = admin_api.get("/api/v1/buildings/")
        assert resp.status == 200
        body = resp.json()
        assert "count" in body
        assert "results" in body
        assert isinstance(body["results"], list)

    def test_get_building_by_id(self, admin_api: APIRequestContext, seeded_building):
        bid = seeded_building["building"]["id"]
        resp = admin_api.get(f"/api/v1/buildings/{bid}/")
        assert resp.status == 200
        assert resp.json()["id"] == bid

    def test_update_building(self, admin_api: APIRequestContext, seeded_building):
        bid = seeded_building["building"]["id"]
        new_name = f"{unique_prefix()} Updated"
        resp = admin_api.patch(f"/api/v1/buildings/{bid}/", data={"name": new_name})
        assert resp.status == 200
        assert resp.json()["name"] == new_name

    def test_delete_building(self, admin_api: APIRequestContext):
        payload = build_building()
        create_resp = admin_api.post("/api/v1/buildings/", data=payload)
        bid = create_resp.json()["id"]
        del_resp = admin_api.delete(f"/api/v1/buildings/{bid}/")
        assert del_resp.status in (200, 204)
        get_resp = admin_api.get(f"/api/v1/buildings/{bid}/")
        assert get_resp.status == 404

    # ── Negative tests ────────────────────────────────────────

    def test_create_building_missing_name(self, admin_api: APIRequestContext):
        payload = build_building()
        del payload["name"]
        resp = admin_api.post("/api/v1/buildings/", data=payload)
        assert resp.status == 400

    def test_create_building_missing_address(self, admin_api: APIRequestContext):
        payload = build_building()
        del payload["address"]
        resp = admin_api.post("/api/v1/buildings/", data=payload)
        assert resp.status == 400

    def test_create_building_invalid_num_floors_zero(self, admin_api: APIRequestContext):
        payload = build_building(num_floors=0)
        resp = admin_api.post("/api/v1/buildings/", data=payload)
        assert resp.status == 400

    def test_get_nonexistent_building(self, admin_api: APIRequestContext):
        resp = admin_api.get("/api/v1/buildings/00000000-0000-0000-0000-000000000000/")
        assert resp.status == 404

    def test_unauthenticated_create(self, unauthenticated_api: APIRequestContext):
        payload = build_building()
        resp = unauthenticated_api.post("/api/v1/buildings/", data=payload)
        assert resp.status == 401

    def test_owner_cannot_create_building(self, owner_api: APIRequestContext):
        payload = build_building()
        resp = owner_api.post("/api/v1/buildings/", data=payload)
        assert resp.status == 403

    def test_owner_cannot_delete_building(
        self, owner_api: APIRequestContext, seeded_building
    ):
        bid = seeded_building["building"]["id"]
        resp = owner_api.delete(f"/api/v1/buildings/{bid}/")
        assert resp.status == 403
