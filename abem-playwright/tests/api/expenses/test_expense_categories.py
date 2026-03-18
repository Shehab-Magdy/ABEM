"""API tests for expense categories."""

import pytest
from playwright.sync_api import APIRequestContext

from utils.data_factory import build_category, unique_prefix


@pytest.mark.api
@pytest.mark.categories
class TestExpenseCategories:

    def test_list_building_categories(self, admin_api: APIRequestContext, seeded_building):
        bid = seeded_building["building"]["id"]
        resp = admin_api.get("/api/v1/expenses/categories/", params={"building_id": bid})
        assert resp.status == 200
        cats = resp.json()
        cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
        assert len(cat_list) == 15, f"Expected 15 default categories, got {len(cat_list)}"

    def test_each_category_has_required_fields(
        self, admin_api: APIRequestContext, seeded_building
    ):
        bid = seeded_building["building"]["id"]
        resp = admin_api.get("/api/v1/expenses/categories/", params={"building_id": bid})
        cats = resp.json()
        cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
        for cat in cat_list:
            assert "id" in cat
            assert "name" in cat and cat["name"]
            assert "icon" in cat
            assert "color" in cat

    def test_create_expense_with_valid_category(
        self, admin_api: APIRequestContext, seeded_building
    ):
        bid = seeded_building["building"]["id"]
        cats = admin_api.get(
            "/api/v1/expenses/categories/", params={"building_id": bid}
        ).json()
        cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
        resp = admin_api.post("/api/v1/expenses/", data={
            "building_id": bid, "category_id": cat_list[0]["id"],
            "title": "Valid Cat Test", "amount": "100",
            "expense_date": "2026-01-01", "split_type": "equal_all",
        })
        assert resp.status == 201
        admin_api.delete(f"/api/v1/expenses/{resp.json()['id']}/")

    def test_create_expense_with_invalid_category_id(
        self, admin_api: APIRequestContext, seeded_building
    ):
        bid = seeded_building["building"]["id"]
        resp = admin_api.post("/api/v1/expenses/", data={
            "building_id": bid,
            "category_id": "00000000-0000-0000-0000-000000000000",
            "title": "Bad Cat Test", "amount": "100",
            "expense_date": "2026-01-01", "split_type": "equal_all",
        })
        assert resp.status == 400

    def test_admin_can_create_custom_category(
        self, admin_api: APIRequestContext, seeded_building
    ):
        bid = seeded_building["building"]["id"]
        payload = build_category(bid)
        resp = admin_api.post("/api/v1/expenses/categories/", data=payload)
        assert resp.status == 201
        assert resp.json()["name"] == payload["name"]

    def test_custom_category_appears_in_list(
        self, admin_api: APIRequestContext, seeded_building
    ):
        bid = seeded_building["building"]["id"]
        payload = build_category(bid)
        create_resp = admin_api.post("/api/v1/expenses/categories/", data=payload)
        assert create_resp.status == 201
        list_resp = admin_api.get(
            "/api/v1/expenses/categories/", params={"building_id": bid}
        )
        cats = list_resp.json()
        cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
        names = [c["name"] for c in cat_list]
        assert payload["name"] in names

    def test_duplicate_category_name_rejected(
        self, admin_api: APIRequestContext, seeded_building
    ):
        bid = seeded_building["building"]["id"]
        name = f"{unique_prefix()} Dup Cat"
        admin_api.post("/api/v1/expenses/categories/", data=build_category(bid, name=name))
        resp = admin_api.post(
            "/api/v1/expenses/categories/", data=build_category(bid, name=name)
        )
        assert resp.status in (400, 409)

    def test_owner_cannot_create_category(
        self, owner_api: APIRequestContext, seeded_building
    ):
        bid = seeded_building["building"]["id"]
        resp = owner_api.post(
            "/api/v1/expenses/categories/",
            data=build_category(bid),
        )
        assert resp.status == 403

    def test_owner_cannot_delete_category(
        self, admin_api: APIRequestContext, owner_api: APIRequestContext, seeded_building
    ):
        bid = seeded_building["building"]["id"]
        cat = admin_api.post(
            "/api/v1/expenses/categories/", data=build_category(bid)
        ).json()
        resp = owner_api.delete(f"/api/v1/expenses/categories/{cat['id']}/")
        assert resp.status == 403
