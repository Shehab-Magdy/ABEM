"""DB tests for soft-delete integrity."""
import pytest
from utils.data_factory import build_building, build_expense
from utils.db_client import query_one


@pytest.mark.db
class TestSoftDeleteIntegrity:
    def test_deleted_expense_has_deleted_at(self, admin_api, db_conn):
        building = admin_api.post("/api/v1/buildings/", data=build_building(num_apartments=1, num_stores=0)).json()
        try:
            cats = admin_api.get("/api/v1/expenses/categories/", params={"building_id": building["id"]}).json()
            cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
            expense = admin_api.post("/api/v1/expenses/", data=build_expense(
                building["id"], cat_list[0]["id"], amount="100"
            )).json()
            admin_api.delete(f"/api/v1/expenses/{expense['id']}/")
            row = query_one(db_conn, "SELECT deleted_at FROM expenses_expense WHERE id::text = %s", (expense["id"],))
            assert row is not None and row["deleted_at"] is not None
        finally:
            admin_api.delete(f"/api/v1/buildings/{building['id']}/")

    def test_api_returns_404_after_soft_delete(self, admin_api, seeded_building):
        bid = seeded_building["building"]["id"]
        cats = admin_api.get("/api/v1/expenses/categories/", params={"building_id": bid}).json()
        cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
        expense = admin_api.post("/api/v1/expenses/", data=build_expense(bid, cat_list[0]["id"])).json()
        admin_api.delete(f"/api/v1/expenses/{expense['id']}/")
        assert admin_api.get(f"/api/v1/expenses/{expense['id']}/").status == 404
