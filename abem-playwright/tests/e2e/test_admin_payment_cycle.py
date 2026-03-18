"""E2E Journey 2: Admin payment with overpayment carry-forward."""
from decimal import Decimal
import pytest
from utils.data_factory import build_building, build_expense, build_payment
from config.settings import settings


@pytest.mark.e2e
class TestAdminPaymentCycle:

    def test_overpayment_carry_forward(self, admin_api):
        building = admin_api.post(
            "/api/v1/buildings/", data=build_building(num_apartments=1, num_stores=0)
        ).json()
        bid = building["id"]
        try:
            apts = admin_api.get("/api/v1/apartments/", params={"building_id": bid}).json()
            apt_list = apts.get("results", apts) if isinstance(apts, dict) else apts
            apt = apt_list[0]
            cats = admin_api.get("/api/v1/expenses/categories/", params={"building_id": bid}).json()
            cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats

            # Create expense 100
            admin_api.post("/api/v1/expenses/", data=build_expense(
                bid, cat_list[0]["id"], amount="100"
            ))

            # Pay 150 (overpay by 50)
            p1 = admin_api.post("/api/v1/payments/", data=build_payment(
                apt["id"], amount_paid="150"
            )).json()
            assert Decimal(str(p1["balance_after"])) < 0

            # Create second expense 200
            admin_api.post("/api/v1/expenses/", data=build_expense(
                bid, cat_list[0]["id"], amount="200"
            ))

            # Check new balance
            apt_data = admin_api.get(f"/api/v1/apartments/{apt['id']}/").json()
            balance = Decimal(str(apt_data.get("balance", "0")))

            # Pay remaining
            if balance > 0:
                p2 = admin_api.post("/api/v1/payments/", data=build_payment(
                    apt["id"], amount_paid=str(balance)
                )).json()
                assert Decimal(str(p2["balance_after"])) == Decimal("0")

        finally:
            admin_api.delete(f"/api/v1/buildings/{bid}/")
