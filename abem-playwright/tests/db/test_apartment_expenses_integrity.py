"""DB tests for apartment_expenses join table integrity."""
from decimal import Decimal
import pytest
from utils.data_factory import build_building, build_expense
from utils.db_client import get_apartment_expenses


@pytest.mark.db
class TestApartmentExpensesIntegrity:
    def test_equal_split_creates_correct_rows(self, admin_api, db_conn):
        building = admin_api.post("/api/v1/buildings/", data=build_building(num_apartments=2, num_stores=0)).json()
        try:
            cats = admin_api.get("/api/v1/expenses/categories/", params={"building_id": building["id"]}).json()
            cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
            expense = admin_api.post("/api/v1/expenses/", data=build_expense(
                building["id"], cat_list[0]["id"], amount="200"
            )).json()
            rows = get_apartment_expenses(db_conn, expense["id"])
            assert len(rows) == 2
        finally:
            admin_api.delete(f"/api/v1/buildings/{building['id']}/")

    def test_shares_sum_gte_expense_amount(self, admin_api, db_conn):
        building = admin_api.post("/api/v1/buildings/", data=build_building(num_apartments=2, num_stores=0)).json()
        try:
            cats = admin_api.get("/api/v1/expenses/categories/", params={"building_id": building["id"]}).json()
            cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
            expense = admin_api.post("/api/v1/expenses/", data=build_expense(
                building["id"], cat_list[0]["id"], amount="101"
            )).json()
            rows = get_apartment_expenses(db_conn, expense["id"])
            total = sum(Decimal(str(r["share_amount"])) for r in rows)
            assert total >= Decimal("101")
        finally:
            admin_api.delete(f"/api/v1/buildings/{building['id']}/")
