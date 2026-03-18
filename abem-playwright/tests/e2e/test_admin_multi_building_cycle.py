"""E2E Journey 5: Multi-building context switch."""
import pytest
from pages.expenses_page import ExpensesPage
from utils.data_factory import build_building, build_expense
from config.settings import settings


@pytest.mark.e2e
class TestAdminMultiBuildingCycle:

    def test_multi_building_switch(self, admin_page, admin_api, second_admin_api):
        # Create two buildings
        bA = admin_api.post("/api/v1/buildings/", data=build_building(name="Building Alpha")).json()
        bB = admin_api.post("/api/v1/buildings/", data=build_building(name="Building Beta")).json()
        try:
            catsA = admin_api.get("/api/v1/expenses/categories/", params={"building_id": bA["id"]}).json()
            catA = (catsA.get("results", catsA) if isinstance(catsA, dict) else catsA)[0]
            catsB = admin_api.get("/api/v1/expenses/categories/", params={"building_id": bB["id"]}).json()
            catB = (catsB.get("results", catsB) if isinstance(catsB, dict) else catsB)[0]

            admin_api.post("/api/v1/expenses/", data=build_expense(
                bA["id"], catA["id"], title="Alpha Expense"
            ))
            admin_api.post("/api/v1/expenses/", data=build_expense(
                bB["id"], catB["id"], title="Beta Expense"
            ))

            # Navigate to expenses
            ep = ExpensesPage(admin_page)
            ep.navigate()
            ep.wait_for_load()

            # Verify isolation: second admin cannot see Building A
            resp = second_admin_api.get(f"/api/v1/buildings/{bA['id']}/")
            assert resp.status in (403, 404)

        finally:
            admin_api.delete(f"/api/v1/buildings/{bA['id']}/")
            admin_api.delete(f"/api/v1/buildings/{bB['id']}/")
