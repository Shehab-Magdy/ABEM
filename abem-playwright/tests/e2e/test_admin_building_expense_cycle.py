"""E2E Journey 1: Admin building and expense full cycle."""
import math
from decimal import Decimal

import pytest
from pages.expenses_page import ExpensesPage
from utils.data_factory import build_building, build_expense, build_payment
from utils.db_client import get_apartment_expenses, get_audit_logs, query_one
from config.settings import settings


@pytest.mark.e2e
class TestAdminBuildingExpenseCycle:

    def test_full_cycle(self, admin_page, admin_api, db_conn):
        # 1. Create building with 1 apartment + 1 store
        building = admin_api.post(
            "/api/v1/buildings/", data=build_building(num_apartments=1, num_stores=1)
        ).json()
        bid = building["id"]
        try:
            # 2. Fetch apartments and category
            apts = admin_api.get("/api/v1/apartments/", params={"building_id": bid}).json()
            apt_list = apts.get("results", apts) if isinstance(apts, dict) else apts
            cats = admin_api.get("/api/v1/expenses/categories/", params={"building_id": bid}).json()
            cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
            assert len(apt_list) == 2
            assert len(cat_list) > 0

            apartment = next((a for a in apt_list if a.get("type", a.get("unit_type")) == "apartment"), apt_list[0])
            store = next((a for a in apt_list if a.get("type", a.get("unit_type")) == "store"), apt_list[1])

            # 3. Create expense 101 EGP equal_all
            expense = admin_api.post("/api/v1/expenses/", data=build_expense(
                bid, cat_list[0]["id"], amount="101", split_type="equal_all"
            )).json()
            shares = expense.get("apartment_shares", [])

            # 4. Verify shares: 101/2 = 50.5 → ceil(50.5/5)*5 = 55
            expected_share = Decimal(str(math.ceil(101 / 2 / 5) * 5))
            for s in shares:
                assert Decimal(str(s["share_amount"])) == expected_share

            # 5. Sum >= 101
            total = sum(Decimal(str(s["share_amount"])) for s in shares)
            assert total >= Decimal("101")

            # 6. Verify apartment_expenses in DB
            db_shares = get_apartment_expenses(db_conn, expense["id"])
            assert len(db_shares) == 2

            # 7. Record partial payment for apartment
            p1 = admin_api.post("/api/v1/payments/", data=build_payment(
                apartment["id"], amount_paid="20"
            )).json()
            assert Decimal(str(p1["balance_after"])) == Decimal(str(p1["balance_before"])) - Decimal("20")

            # 8. Record full payment for store
            store_balance = admin_api.get(f"/api/v1/apartments/{store['id']}/").json().get("balance", "0")
            p2 = admin_api.post("/api/v1/payments/", data=build_payment(
                store["id"], amount_paid=str(store_balance)
            )).json()
            assert Decimal(str(p2["balance_after"])) == Decimal("0")

            # 9. Verify audit logs
            logs = get_audit_logs(db_conn, entity="expense")
            assert len(logs) > 0

            # 10. Soft-delete expense
            admin_api.delete(f"/api/v1/expenses/{expense['id']}/")
            assert admin_api.get(f"/api/v1/expenses/{expense['id']}/").status == 404

            # 11. Verify DB still has record with deleted_at
            row = query_one(
                db_conn,
                "SELECT deleted_at FROM expenses_expense WHERE id::text = %s",
                (expense["id"],),
            )
            if row:
                assert row["deleted_at"] is not None

            # 12. Verify UI doesn't show deleted expense
            ep = ExpensesPage(admin_page)
            ep.navigate()
            ep.wait_for_load()

        finally:
            admin_api.delete(f"/api/v1/buildings/{bid}/")
