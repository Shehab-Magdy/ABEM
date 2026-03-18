"""API tests for expense CRUD operations."""

import pytest
from playwright.sync_api import APIRequestContext

from utils.data_factory import build_expense, unique_prefix


@pytest.mark.api
@pytest.mark.expenses
class TestExpenseCRUD:

    def test_create_expense_with_required_fields(
        self, admin_api: APIRequestContext, seeded_building
    ):
        building = seeded_building["building"]
        cats = admin_api.get(
            "/api/v1/expenses/categories/",
            params={"building_id": building["id"]},
        ).json()
        cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
        payload = build_expense(building["id"], cat_list[0]["id"])
        resp = admin_api.post("/api/v1/expenses/", data=payload)
        assert resp.status == 201
        body = resp.json()
        assert "id" in body
        assert "apartment_shares" in body
        admin_api.delete(f"/api/v1/expenses/{body['id']}/")

    def test_create_expense_with_all_fields(
        self, admin_api: APIRequestContext, seeded_building
    ):
        building = seeded_building["building"]
        cats = admin_api.get(
            "/api/v1/expenses/categories/", params={"building_id": building["id"]}
        ).json()
        cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
        payload = build_expense(
            building["id"], cat_list[0]["id"],
            description="Full fields test",
            due_date="2026-12-31",
            is_recurring=True,
            frequency="monthly",
        )
        resp = admin_api.post("/api/v1/expenses/", data=payload)
        assert resp.status == 201
        admin_api.delete(f"/api/v1/expenses/{resp.json()['id']}/")

    def test_list_expenses(self, admin_api: APIRequestContext):
        resp = admin_api.get("/api/v1/expenses/")
        assert resp.status == 200
        body = resp.json()
        assert "results" in body

    def test_get_expense_by_id(self, admin_api: APIRequestContext, seeded_expense):
        eid = seeded_expense["expense"]["id"]
        resp = admin_api.get(f"/api/v1/expenses/{eid}/")
        assert resp.status == 200

    def test_update_expense(self, admin_api: APIRequestContext, seeded_expense):
        eid = seeded_expense["expense"]["id"]
        resp = admin_api.patch(
            f"/api/v1/expenses/{eid}/",
            data={"title": f"{unique_prefix()} Updated"},
        )
        assert resp.status == 200

    def test_delete_expense_soft_delete(self, admin_api: APIRequestContext, seeded_building):
        building = seeded_building["building"]
        cats = admin_api.get(
            "/api/v1/expenses/categories/", params={"building_id": building["id"]}
        ).json()
        cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
        expense = admin_api.post(
            "/api/v1/expenses/",
            data=build_expense(building["id"], cat_list[0]["id"]),
        ).json()
        resp = admin_api.delete(f"/api/v1/expenses/{expense['id']}/")
        assert resp.status in (200, 204)
        get_resp = admin_api.get(f"/api/v1/expenses/{expense['id']}/")
        assert get_resp.status == 404

    # ── Negative ──────────────────────────────────────────────

    def test_create_missing_building_id(self, admin_api: APIRequestContext):
        resp = admin_api.post("/api/v1/expenses/", data={
            "title": "No building", "amount": "100",
            "expense_date": "2026-01-01", "split_type": "equal_all",
        })
        assert resp.status == 400

    def test_create_missing_amount(self, admin_api: APIRequestContext, seeded_building):
        building = seeded_building["building"]
        cats = admin_api.get(
            "/api/v1/expenses/categories/", params={"building_id": building["id"]}
        ).json()
        cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
        resp = admin_api.post("/api/v1/expenses/", data={
            "building_id": building["id"], "category_id": cat_list[0]["id"],
            "title": "No amount", "expense_date": "2026-01-01",
        })
        assert resp.status == 400

    def test_create_negative_amount(self, admin_api: APIRequestContext, seeded_building):
        building = seeded_building["building"]
        cats = admin_api.get(
            "/api/v1/expenses/categories/", params={"building_id": building["id"]}
        ).json()
        cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
        resp = admin_api.post("/api/v1/expenses/", data=build_expense(
            building["id"], cat_list[0]["id"], amount="-50"
        ))
        assert resp.status == 400

    def test_create_zero_amount(self, admin_api: APIRequestContext, seeded_building):
        building = seeded_building["building"]
        cats = admin_api.get(
            "/api/v1/expenses/categories/", params={"building_id": building["id"]}
        ).json()
        cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
        resp = admin_api.post("/api/v1/expenses/", data=build_expense(
            building["id"], cat_list[0]["id"], amount="0"
        ))
        assert resp.status == 400

    def test_create_invalid_amount_string(self, admin_api: APIRequestContext, seeded_building):
        building = seeded_building["building"]
        cats = admin_api.get(
            "/api/v1/expenses/categories/", params={"building_id": building["id"]}
        ).json()
        cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
        resp = admin_api.post("/api/v1/expenses/", data=build_expense(
            building["id"], cat_list[0]["id"], amount="abc"
        ))
        assert resp.status == 400

    def test_owner_cannot_create(self, owner_api: APIRequestContext, seeded_building):
        building = seeded_building["building"]
        resp = owner_api.post("/api/v1/expenses/", data={
            "building_id": building["id"], "title": "Blocked",
            "amount": "100", "expense_date": "2026-01-01",
        })
        assert resp.status == 403

    def test_unauthenticated(self, unauthenticated_api: APIRequestContext):
        resp = unauthenticated_api.get("/api/v1/expenses/")
        assert resp.status == 401

    def test_get_nonexistent(self, admin_api: APIRequestContext):
        resp = admin_api.get("/api/v1/expenses/00000000-0000-0000-0000-000000000000/")
        assert resp.status == 404
