"""API tests for overpayment and credit carry-forward."""

from decimal import Decimal

import pytest
from playwright.sync_api import APIRequestContext

from utils.data_factory import build_building, build_expense, build_payment


@pytest.mark.api
@pytest.mark.payments
class TestOverpayment:

    def _setup(self, admin_api):
        building = admin_api.post(
            "/api/v1/buildings/", data=build_building(num_apartments=1, num_stores=0)
        ).json()
        bid = building["id"]
        apts = admin_api.get("/api/v1/apartments/", params={"building_id": bid}).json()
        apt_list = apts.get("results", apts) if isinstance(apts, dict) else apts
        cats = admin_api.get(
            "/api/v1/expenses/categories/", params={"building_id": bid}
        ).json()
        cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
        return building, apt_list[0], cat_list[0]

    def test_overpayment_creates_credit(self, admin_api: APIRequestContext):
        building, apt, cat = self._setup(admin_api)
        try:
            # Create expense 100
            admin_api.post("/api/v1/expenses/", data=build_expense(
                building["id"], cat["id"], amount="100"
            ))
            # Pay 150 (overpay by 50)
            payment = admin_api.post("/api/v1/payments/", data=build_payment(
                apt["id"], amount_paid="150"
            )).json()
            balance_after = Decimal(str(payment["balance_after"]))
            assert balance_after < 0, f"Expected negative balance (credit), got {balance_after}"
        finally:
            admin_api.delete(f"/api/v1/buildings/{building['id']}/")

    def test_credit_carries_forward(self, admin_api: APIRequestContext):
        building, apt, cat = self._setup(admin_api)
        try:
            # Create expense 100
            admin_api.post("/api/v1/expenses/", data=build_expense(
                building["id"], cat["id"], amount="100"
            ))
            # Overpay
            admin_api.post("/api/v1/payments/", data=build_payment(
                apt["id"], amount_paid="150"
            ))
            # Create second expense 200
            admin_api.post("/api/v1/expenses/", data=build_expense(
                building["id"], cat["id"], amount="200"
            ))
            # Check balance via apartment endpoint
            apt_resp = admin_api.get(f"/api/v1/apartments/{apt['id']}/")
            new_balance = Decimal(str(apt_resp.json().get("balance", "0")))
            # Balance should be less than the new expense share due to credit
            assert new_balance < Decimal("200"), f"Credit not applied: balance={new_balance}"
        finally:
            admin_api.delete(f"/api/v1/buildings/{building['id']}/")

    def test_exact_payment_zeroes_balance(self, admin_api: APIRequestContext):
        building, apt, cat = self._setup(admin_api)
        try:
            admin_api.post("/api/v1/expenses/", data=build_expense(
                building["id"], cat["id"], amount="100"
            ))
            # Get the actual share amount
            apt_data = admin_api.get(f"/api/v1/apartments/{apt['id']}/").json()
            balance = apt_data.get("balance", "0")
            # Pay exact balance
            payment = admin_api.post("/api/v1/payments/", data=build_payment(
                apt["id"], amount_paid=str(balance)
            )).json()
            assert Decimal(str(payment["balance_after"])) == Decimal("0")
        finally:
            admin_api.delete(f"/api/v1/buildings/{building['id']}/")
