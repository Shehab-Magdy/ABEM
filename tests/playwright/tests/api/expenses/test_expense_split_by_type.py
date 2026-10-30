"""API tests for type-based expense splitting (apartments-only and stores-only)."""

from decimal import Decimal

import pytest
from playwright.sync_api import APIRequestContext

from utils.data_factory import build_building, build_expense


@pytest.mark.api
@pytest.mark.expenses
@pytest.mark.boundary
class TestExpenseSplitByType:

    def _setup(self, admin_api):
        building = admin_api.post(
            "/api/v1/buildings/",
            data=build_building(num_apartments=2, num_stores=1),
        ).json()
        bid = building["id"]
        apts = admin_api.get("/api/v1/apartments/", params={"building_id": bid}).json()
        apt_list = apts.get("results", apts) if isinstance(apts, dict) else apts
        cats = admin_api.get("/api/v1/expenses/categories/", params={"building_id": bid}).json()
        cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
        apartments = [a for a in apt_list if a.get("type", a.get("unit_type")) == "apartment"]
        stores = [a for a in apt_list if a.get("type", a.get("unit_type")) == "store"]
        return building, apartments, stores, cat_list[0]

    def test_apartments_only_split_excludes_stores(self, admin_api: APIRequestContext):
        building, apartments, stores, cat = self._setup(admin_api)
        try:
            resp = admin_api.post("/api/v1/expenses/", data=build_expense(
                building["id"], cat["id"], amount="200", split_type="equal_apartments"
            ))
            assert resp.status == 201
            shares = resp.json().get("apartment_shares", [])
            share_ids = {s["apartment_id"] for s in shares}
            store_ids = {s["id"] for s in stores}
            assert share_ids.isdisjoint(store_ids)
        finally:
            admin_api.delete(f"/api/v1/buildings/{building['id']}/")

    def test_stores_only_split_excludes_apartments(self, admin_api: APIRequestContext):
        building, apartments, stores, cat = self._setup(admin_api)
        try:
            resp = admin_api.post("/api/v1/expenses/", data=build_expense(
                building["id"], cat["id"], amount="200", split_type="equal_stores"
            ))
            assert resp.status == 201
            shares = resp.json().get("apartment_shares", [])
            share_ids = {s["apartment_id"] for s in shares}
            apt_ids = {a["id"] for a in apartments}
            assert share_ids.isdisjoint(apt_ids)
        finally:
            admin_api.delete(f"/api/v1/buildings/{building['id']}/")

    def test_apartment_shares_sum_gte_amount(self, admin_api: APIRequestContext):
        building, apartments, stores, cat = self._setup(admin_api)
        try:
            resp = admin_api.post("/api/v1/expenses/", data=build_expense(
                building["id"], cat["id"], amount="201", split_type="equal_apartments"
            ))
            shares = resp.json().get("apartment_shares", [])
            total = sum(Decimal(str(s["share_amount"])) for s in shares)
            assert total >= Decimal("201")
        finally:
            admin_api.delete(f"/api/v1/buildings/{building['id']}/")

    def test_store_balance_unchanged_after_apartments_expense(
        self, admin_api: APIRequestContext
    ):
        building, apartments, stores, cat = self._setup(admin_api)
        try:
            if not stores:
                pytest.skip("No stores")
            store_before = admin_api.get(f"/api/v1/apartments/{stores[0]['id']}/").json()
            balance_before = Decimal(str(store_before.get("balance", "0")))

            admin_api.post("/api/v1/expenses/", data=build_expense(
                building["id"], cat["id"], amount="200", split_type="equal_apartments"
            ))

            store_after = admin_api.get(f"/api/v1/apartments/{stores[0]['id']}/").json()
            balance_after = Decimal(str(store_after.get("balance", "0")))
            assert balance_after == balance_before
        finally:
            admin_api.delete(f"/api/v1/buildings/{building['id']}/")
