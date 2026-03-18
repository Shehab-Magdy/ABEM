"""API tests for expense participation rules and custom splits."""

from decimal import Decimal

import pytest
from playwright.sync_api import APIRequestContext

from utils.data_factory import build_building, build_expense


@pytest.mark.api
@pytest.mark.expenses
class TestExpenseParticipation:

    def _setup(self, admin_api):
        building = admin_api.post(
            "/api/v1/buildings/",
            data=build_building(num_apartments=3, num_stores=0),
        ).json()
        bid = building["id"]
        apts = admin_api.get("/api/v1/apartments/", params={"building_id": bid}).json()
        apt_list = apts.get("results", apts) if isinstance(apts, dict) else apts
        cats = admin_api.get("/api/v1/expenses/categories/", params={"building_id": bid}).json()
        cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
        return building, apt_list, cat_list[0] if cat_list else None

    def test_custom_split_specific_apartments(self, admin_api: APIRequestContext):
        """Custom split with only 2 out of 3 apartments."""
        building, apts, cat = self._setup(admin_api)
        try:
            if not cat or len(apts) < 2:
                pytest.skip("Insufficient data")
            selected = [apts[0]["id"], apts[1]["id"]]
            resp = admin_api.post("/api/v1/expenses/", data={
                "building_id": building["id"],
                "category_id": cat["id"],
                "title": "Custom Split Test",
                "amount": "300",
                "expense_date": "2026-01-01",
                "split_type": "custom",
                "custom_split_apartments": selected,
            })
            assert resp.status == 201
            shares = resp.json().get("apartment_shares", [])
            share_ids = {s["apartment"] for s in shares}
            assert apts[2]["id"] not in share_ids
            assert len(shares) == 2
        finally:
            admin_api.delete(f"/api/v1/buildings/{building['id']}/")

    def test_custom_split_weights(self, admin_api: APIRequestContext):
        """Custom split with weighted allocation."""
        building, apts, cat = self._setup(admin_api)
        try:
            if not cat or len(apts) < 2:
                pytest.skip("Insufficient data")
            weights = {
                apts[0]["id"]: "2.0",
                apts[1]["id"]: "1.0",
            }
            resp = admin_api.post("/api/v1/expenses/", data={
                "building_id": building["id"],
                "category_id": cat["id"],
                "title": "Weighted Split Test",
                "amount": "300",
                "expense_date": "2026-01-01",
                "split_type": "custom",
                "custom_split_apartments": list(weights.keys()),
                "custom_split_weights": weights,
            })
            assert resp.status == 201
            shares = resp.json().get("apartment_shares", [])
            total = sum(Decimal(str(s["share_amount"])) for s in shares)
            assert total >= Decimal("300")
        finally:
            admin_api.delete(f"/api/v1/buildings/{building['id']}/")
