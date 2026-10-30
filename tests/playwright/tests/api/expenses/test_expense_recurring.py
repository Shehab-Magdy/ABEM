"""API tests for recurring expenses."""

import pytest
from playwright.sync_api import APIRequestContext

from utils.data_factory import build_expense


@pytest.mark.api
@pytest.mark.expenses
class TestExpenseRecurring:

    def _get_category(self, admin_api, building_id):
        cats = admin_api.get(
            "/api/v1/expenses/categories/", params={"building_id": building_id}
        ).json()
        cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
        return cat_list[0] if cat_list else None

    def test_create_recurring_expense(self, admin_api: APIRequestContext, seeded_building):
        bid = seeded_building["building"]["id"]
        cat = self._get_category(admin_api, bid)
        resp = admin_api.post("/api/v1/expenses/", data=build_expense(
            bid, cat["id"], is_recurring=True, frequency="monthly"
        ))
        assert resp.status == 201
        body = resp.json()
        assert body.get("is_recurring") is True
        admin_api.delete(f"/api/v1/expenses/{body['id']}/")

    def test_recurring_expense_has_config(self, admin_api: APIRequestContext, seeded_building):
        bid = seeded_building["building"]["id"]
        cat = self._get_category(admin_api, bid)
        resp = admin_api.post("/api/v1/expenses/", data=build_expense(
            bid, cat["id"], is_recurring=True, frequency="quarterly"
        ))
        body = resp.json()
        config = body.get("recurring_config")
        assert config is not None, "recurring_config should be present"
        assert config.get("frequency") == "quarterly"
        admin_api.delete(f"/api/v1/expenses/{body['id']}/")

    def test_recurring_without_frequency_rejected(
        self, admin_api: APIRequestContext, seeded_building
    ):
        bid = seeded_building["building"]["id"]
        cat = self._get_category(admin_api, bid)
        payload = build_expense(bid, cat["id"], is_recurring=True)
        payload.pop("frequency", None)
        resp = admin_api.post("/api/v1/expenses/", data=payload)
        assert resp.status == 400

    def test_non_recurring_ignores_frequency(
        self, admin_api: APIRequestContext, seeded_building
    ):
        bid = seeded_building["building"]["id"]
        cat = self._get_category(admin_api, bid)
        resp = admin_api.post("/api/v1/expenses/", data=build_expense(
            bid, cat["id"], is_recurring=False, frequency="annual"
        ))
        assert resp.status == 201
        body = resp.json()
        assert body.get("is_recurring") is False
        admin_api.delete(f"/api/v1/expenses/{body['id']}/")
