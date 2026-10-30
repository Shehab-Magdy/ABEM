"""Boundary tests for equal expense splitting with round-up-to-5 logic."""

import math
from decimal import Decimal

import pytest
from playwright.sync_api import APIRequestContext

from utils.data_factory import build_building, build_expense


def round_up_to_5(amount: Decimal) -> Decimal:
    return Decimal(str(math.ceil(float(amount) / 5) * 5))


@pytest.mark.api
@pytest.mark.expenses
@pytest.mark.boundary
class TestExpenseSplitEqual:

    def _create_building_and_expense(self, admin_api, num_apartments, num_stores, amount):
        building = admin_api.post(
            "/api/v1/buildings/",
            data=build_building(num_apartments=num_apartments, num_stores=num_stores),
        ).json()
        bid = building["id"]
        cats = admin_api.get(
            "/api/v1/expenses/categories/", params={"building_id": bid}
        ).json()
        cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
        expense = admin_api.post("/api/v1/expenses/", data=build_expense(
            bid, cat_list[0]["id"], amount=str(amount), split_type="equal_all"
        )).json()
        return building, expense

    def test_amount_exactly_divisible(self, admin_api: APIRequestContext):
        """100 / 2 units = 50 each. 50 is already a multiple of 5."""
        building, expense = self._create_building_and_expense(admin_api, 1, 1, 100)
        try:
            shares = expense.get("apartment_shares", [])
            for s in shares:
                assert Decimal(str(s["share_amount"])) == round_up_to_5(Decimal("50"))
        finally:
            admin_api.delete(f"/api/v1/buildings/{building['id']}/")

    def test_amount_produces_remainder(self, admin_api: APIRequestContext):
        """101 / 2 = 50.5 → rounds up to 55."""
        building, expense = self._create_building_and_expense(admin_api, 1, 1, 101)
        try:
            shares = expense.get("apartment_shares", [])
            total = sum(Decimal(str(s["share_amount"])) for s in shares)
            assert total >= Decimal("101"), f"Sum {total} < 101"
            for s in shares:
                assert Decimal(str(s["share_amount"])) == Decimal("55"), (
                    f"Expected 55, got {s['share_amount']}"
                )
        finally:
            admin_api.delete(f"/api/v1/buildings/{building['id']}/")

    def test_amount_99_split_2(self, admin_api: APIRequestContext):
        """99 / 2 = 49.5 → rounds up to 50."""
        building, expense = self._create_building_and_expense(admin_api, 1, 1, 99)
        try:
            shares = expense.get("apartment_shares", [])
            for s in shares:
                assert Decimal(str(s["share_amount"])) == Decimal("50")
        finally:
            admin_api.delete(f"/api/v1/buildings/{building['id']}/")

    def test_single_unit_gets_full_amount(self, admin_api: APIRequestContext):
        """1 unit gets the full amount, rounded to nearest 5."""
        building, expense = self._create_building_and_expense(admin_api, 1, 0, 101)
        try:
            shares = expense.get("apartment_shares", [])
            assert len(shares) == 1
            assert Decimal(str(shares[0]["share_amount"])) == round_up_to_5(Decimal("101"))
        finally:
            admin_api.delete(f"/api/v1/buildings/{building['id']}/")

    @pytest.mark.parametrize("amount", ["101", "203", "999", "1"])
    def test_shares_sum_always_gte_amount(self, admin_api: APIRequestContext, amount):
        building, expense = self._create_building_and_expense(admin_api, 1, 1, amount)
        try:
            shares = expense.get("apartment_shares", [])
            total = sum(Decimal(str(s["share_amount"])) for s in shares)
            assert total >= Decimal(amount), f"Sum {total} < {amount}"
        finally:
            admin_api.delete(f"/api/v1/buildings/{building['id']}/")

    def test_min_amount_001(self, admin_api: APIRequestContext):
        building, expense = self._create_building_and_expense(admin_api, 1, 0, "0.01")
        try:
            assert expense.get("id") is not None
        finally:
            admin_api.delete(f"/api/v1/buildings/{building['id']}/")

    def test_negative_amount_rejected(self, admin_api: APIRequestContext, seeded_building):
        building = seeded_building["building"]
        cats = admin_api.get(
            "/api/v1/expenses/categories/", params={"building_id": building["id"]}
        ).json()
        cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
        resp = admin_api.post("/api/v1/expenses/", data=build_expense(
            building["id"], cat_list[0]["id"], amount="-100"
        ))
        assert resp.status == 400

    def test_zero_amount_rejected(self, admin_api: APIRequestContext, seeded_building):
        building = seeded_building["building"]
        cats = admin_api.get(
            "/api/v1/expenses/categories/", params={"building_id": building["id"]}
        ).json()
        cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
        resp = admin_api.post("/api/v1/expenses/", data=build_expense(
            building["id"], cat_list[0]["id"], amount="0"
        ))
        assert resp.status == 400

    def test_null_amount_rejected(self, admin_api: APIRequestContext, seeded_building):
        building = seeded_building["building"]
        cats = admin_api.get(
            "/api/v1/expenses/categories/", params={"building_id": building["id"]}
        ).json()
        cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
        resp = admin_api.post("/api/v1/expenses/", data={
            "building_id": building["id"], "category_id": cat_list[0]["id"],
            "title": "Null amount", "amount": None,
            "expense_date": "2026-01-01", "split_type": "equal_all",
        })
        assert resp.status == 400

    def test_string_amount_rejected(self, admin_api: APIRequestContext, seeded_building):
        building = seeded_building["building"]
        cats = admin_api.get(
            "/api/v1/expenses/categories/", params={"building_id": building["id"]}
        ).json()
        cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
        resp = admin_api.post("/api/v1/expenses/", data=build_expense(
            building["id"], cat_list[0]["id"], amount="abc"
        ))
        assert resp.status == 400
