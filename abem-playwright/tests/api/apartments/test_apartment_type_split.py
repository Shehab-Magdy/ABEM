"""API tests for apartment type-based expense splitting."""

import pytest
from playwright.sync_api import APIRequestContext

from utils.data_factory import build_building, build_expense


@pytest.mark.api
@pytest.mark.apartments
@pytest.mark.expenses
class TestApartmentTypeSplit:

    def _setup_building_with_types(self, admin_api):
        """Create a building with both apartment and store units."""
        building = admin_api.post(
            "/api/v1/buildings/",
            data=build_building(num_apartments=2, num_stores=1),
        ).json()
        bid = building["id"]

        apts_resp = admin_api.get("/api/v1/apartments/", params={"building_id": bid})
        apt_list = apts_resp.json().get("results", apts_resp.json())

        cats_resp = admin_api.get(
            "/api/v1/expenses/categories/", params={"building_id": bid}
        )
        cat_list = cats_resp.json().get("results", cats_resp.json())

        apartments = [a for a in apt_list if a.get("type", a.get("unit_type")) == "apartment"]
        stores = [a for a in apt_list if a.get("type", a.get("unit_type")) == "store"]

        return building, apartments, stores, cat_list[0] if cat_list else None

    def test_filter_by_type_apartment(self, admin_api: APIRequestContext, seeded_building):
        bid = seeded_building["building"]["id"]
        resp = admin_api.get("/api/v1/apartments/", params={"building_id": bid, "unit_type": "apartment"})
        assert resp.status == 200
        results = resp.json().get("results", resp.json())
        for apt in results:
            assert apt.get("type", apt.get("unit_type")) == "apartment"

    def test_filter_by_type_store(self, admin_api: APIRequestContext, seeded_building):
        bid = seeded_building["building"]["id"]
        resp = admin_api.get("/api/v1/apartments/", params={"building_id": bid, "unit_type": "store"})
        assert resp.status == 200
        results = resp.json().get("results", resp.json())
        for apt in results:
            assert apt.get("type", apt.get("unit_type")) == "store"

    def test_apartments_only_split(self, admin_api: APIRequestContext):
        """equal_apartments split: only apartment-type units get shares."""
        building, apartments, stores, category = self._setup_building_with_types(admin_api)
        try:
            if not category:
                pytest.skip("No category")
            resp = admin_api.post("/api/v1/expenses/", data={
                "building_id": building["id"],
                "category_id": category["id"],
                "title": "Apartments Only Test",
                "amount": "200",
                "expense_date": "2026-01-01",
                "split_type": "equal_apartments",
            })
            assert resp.status == 201
            shares = resp.json().get("apartment_shares", [])
            share_apt_ids = {s["apartment"] for s in shares}
            store_ids = {s["id"] for s in stores}
            assert share_apt_ids.isdisjoint(store_ids), "Stores should not have shares"
        finally:
            admin_api.delete(f"/api/v1/buildings/{building['id']}/")

    def test_stores_only_split(self, admin_api: APIRequestContext):
        """equal_stores split: only store-type units get shares."""
        building, apartments, stores, category = self._setup_building_with_types(admin_api)
        try:
            if not category:
                pytest.skip("No category")
            resp = admin_api.post("/api/v1/expenses/", data={
                "building_id": building["id"],
                "category_id": category["id"],
                "title": "Stores Only Test",
                "amount": "200",
                "expense_date": "2026-01-01",
                "split_type": "equal_stores",
            })
            assert resp.status == 201
            shares = resp.json().get("apartment_shares", [])
            share_apt_ids = {s["apartment"] for s in shares}
            apt_ids = {a["id"] for a in apartments}
            assert share_apt_ids.isdisjoint(apt_ids), "Apartments should not have shares"
        finally:
            admin_api.delete(f"/api/v1/buildings/{building['id']}/")
