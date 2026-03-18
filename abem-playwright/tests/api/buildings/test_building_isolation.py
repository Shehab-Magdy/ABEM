"""API tests for building multi-tenant isolation."""

import pytest
from playwright.sync_api import APIRequestContext

from utils.data_factory import build_building, build_expense


@pytest.mark.api
@pytest.mark.buildings
@pytest.mark.tenant_isolation
class TestBuildingIsolation:

    def test_admin_cannot_read_other_admin_buildings(
        self,
        admin_api: APIRequestContext,
        second_admin_api: APIRequestContext,
    ):
        """Admin B cannot see Admin A's buildings."""
        payload = build_building()
        create_resp = admin_api.post("/api/v1/buildings/", data=payload)
        assert create_resp.status == 201
        building_id = create_resp.json()["id"]

        try:
            resp = second_admin_api.get(f"/api/v1/buildings/{building_id}/")
            assert resp.status in (403, 404), (
                f"Admin B should not see Admin A's building, got {resp.status}"
            )
        finally:
            admin_api.delete(f"/api/v1/buildings/{building_id}/")

    def test_admin_cannot_create_expense_in_other_admin_building(
        self,
        admin_api: APIRequestContext,
        second_admin_api: APIRequestContext,
    ):
        """Admin B cannot create an expense in Admin A's building."""
        building = admin_api.post("/api/v1/buildings/", data=build_building()).json()
        building_id = building["id"]

        try:
            # Get a category from admin A's building
            cats = admin_api.get(
                "/api/v1/expenses/categories/",
                params={"building_id": building_id},
            ).json()
            cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
            if not cat_list:
                pytest.skip("No categories available")
            category_id = cat_list[0]["id"]

            resp = second_admin_api.post(
                "/api/v1/expenses/",
                data={
                    "building_id": building_id,
                    "category_id": category_id,
                    "title": "Isolation Test",
                    "amount": "100",
                    "expense_date": "2026-01-01",
                    "split_type": "equal_all",
                },
            )
            assert resp.status in (400, 403)
        finally:
            admin_api.delete(f"/api/v1/buildings/{building_id}/")

    def test_building_creates_default_categories(self, admin_api: APIRequestContext):
        building = admin_api.post("/api/v1/buildings/", data=build_building()).json()
        try:
            resp = admin_api.get(
                "/api/v1/expenses/categories/",
                params={"building_id": building["id"]},
            )
            assert resp.status == 200
            cats = resp.json()
            cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
            assert len(cat_list) == 15, f"Expected 15 default categories, got {len(cat_list)}"
        finally:
            admin_api.delete(f"/api/v1/buildings/{building['id']}/")

    def test_building_creates_auto_apartments(self, admin_api: APIRequestContext):
        building = admin_api.post(
            "/api/v1/buildings/",
            data=build_building(num_apartments=3, num_stores=1),
        ).json()
        try:
            resp = admin_api.get(
                "/api/v1/apartments/",
                params={"building_id": building["id"]},
            )
            apts = resp.json()
            apt_list = apts.get("results", apts) if isinstance(apts, dict) else apts
            assert len(apt_list) == 4, f"Expected 4 auto-created units, got {len(apt_list)}"
        finally:
            admin_api.delete(f"/api/v1/buildings/{building['id']}/")
