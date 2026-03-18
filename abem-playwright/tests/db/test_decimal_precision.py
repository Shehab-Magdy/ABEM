"""DB tests for decimal precision."""
from decimal import Decimal
import pytest
from utils.data_factory import build_building, build_expense
from utils.db_client import query_one, column_type


@pytest.mark.db
class TestDecimalPrecision:
    def test_expense_amount_stored_as_decimal(self, admin_api, db_conn):
        building = admin_api.post("/api/v1/buildings/", data=build_building(num_apartments=1, num_stores=0)).json()
        try:
            cats = admin_api.get("/api/v1/expenses/categories/", params={"building_id": building["id"]}).json()
            cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
            expense = admin_api.post("/api/v1/expenses/", data=build_expense(
                building["id"], cat_list[0]["id"], amount="101.37"
            )).json()
            row = query_one(db_conn, "SELECT amount FROM expenses_expense WHERE id::text = %s", (expense["id"],))
            assert Decimal(str(row["amount"])) == Decimal("101.37")
        finally:
            admin_api.delete(f"/api/v1/buildings/{building['id']}/")

    def test_expense_amount_column_type(self, db_conn):
        col_type = column_type(db_conn, "expenses_expense", "amount")
        assert col_type in ("numeric", "decimal"), f"Expected numeric, got {col_type}"
