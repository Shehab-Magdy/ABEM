"""API tests for balance calculation accuracy and payment immutability."""

from decimal import Decimal

import pytest
from playwright.sync_api import APIRequestContext

from utils.data_factory import build_payment


@pytest.mark.api
@pytest.mark.payments
class TestBalanceCalculation:

    def test_balance_after_single_payment(
        self, admin_api: APIRequestContext, seeded_expense
    ):
        apt = seeded_expense["apartment"]
        if not apt:
            pytest.skip("No apartment")
        payment = admin_api.post("/api/v1/payments/", data=build_payment(
            apt["id"], amount_paid="25"
        )).json()
        before = Decimal(str(payment["balance_before"]))
        after = Decimal(str(payment["balance_after"]))
        assert after == before - Decimal("25")

    def test_balance_after_multiple_payments(
        self, admin_api: APIRequestContext, seeded_expense
    ):
        apt = seeded_expense["apartment"]
        if not apt:
            pytest.skip("No apartment")
        p1 = admin_api.post("/api/v1/payments/", data=build_payment(
            apt["id"], amount_paid="10"
        )).json()
        p2 = admin_api.post("/api/v1/payments/", data=build_payment(
            apt["id"], amount_paid="15"
        )).json()
        assert Decimal(str(p2["balance_before"])) == Decimal(str(p1["balance_after"]))
        expected = Decimal(str(p1["balance_after"])) - Decimal("15")
        assert Decimal(str(p2["balance_after"])) == expected

    def test_payment_immutable_no_patch(
        self, admin_api: APIRequestContext, seeded_payment
    ):
        pid = seeded_payment["payment"]["id"]
        resp = admin_api.patch(f"/api/v1/payments/{pid}/", data={"amount_paid": "999"})
        assert resp.status in (405, 403, 404)

    def test_payment_immutable_no_delete(
        self, admin_api: APIRequestContext, seeded_payment
    ):
        pid = seeded_payment["payment"]["id"]
        resp = admin_api.delete(f"/api/v1/payments/{pid}/")
        assert resp.status in (405, 403, 404)

    def test_balance_before_snapshot_correct(
        self, admin_api: APIRequestContext, seeded_expense
    ):
        apt = seeded_expense["apartment"]
        if not apt:
            pytest.skip("No apartment")
        apt_before = admin_api.get(f"/api/v1/apartments/{apt['id']}/").json()
        payment = admin_api.post("/api/v1/payments/", data=build_payment(
            apt["id"], amount_paid="5"
        )).json()
        assert Decimal(str(payment["balance_before"])) == Decimal(
            str(apt_before.get("balance", "0"))
        )
