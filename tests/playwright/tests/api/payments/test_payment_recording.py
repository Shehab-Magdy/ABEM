"""API tests for payment recording."""

from decimal import Decimal

import pytest
from playwright.sync_api import APIRequestContext

from utils.data_factory import build_payment


@pytest.mark.api
@pytest.mark.payments
class TestPaymentRecording:

    def test_record_payment_success(self, admin_api: APIRequestContext, seeded_expense):
        apt = seeded_expense["apartment"]
        if not apt:
            pytest.skip("No apartment")
        resp = admin_api.post("/api/v1/payments/", data=build_payment(
            apt["id"], amount_paid="50", payment_method="cash"
        ))
        assert resp.status == 201
        body = resp.json()
        assert "id" in body
        assert "balance_before" in body
        assert "balance_after" in body

    def test_payment_updates_balance(self, admin_api: APIRequestContext, seeded_expense):
        apt = seeded_expense["apartment"]
        if not apt:
            pytest.skip("No apartment")
        resp = admin_api.post("/api/v1/payments/", data=build_payment(
            apt["id"], amount_paid="30"
        ))
        body = resp.json()
        before = Decimal(str(body["balance_before"]))
        after = Decimal(str(body["balance_after"]))
        paid = Decimal(str(body["amount_paid"]))
        assert after == before - paid

    @pytest.mark.parametrize("method", ["cash", "bank_transfer", "cheque"])
    def test_payment_with_all_methods(
        self, admin_api: APIRequestContext, seeded_expense, method
    ):
        apt = seeded_expense["apartment"]
        if not apt:
            pytest.skip("No apartment")
        resp = admin_api.post("/api/v1/payments/", data=build_payment(
            apt["id"], amount_paid="10", payment_method=method
        ))
        assert resp.status == 201
        assert resp.json()["payment_method"] == method

    def test_payment_zero_amount_rejected(
        self, admin_api: APIRequestContext, seeded_expense
    ):
        apt = seeded_expense["apartment"]
        if not apt:
            pytest.skip("No apartment")
        resp = admin_api.post("/api/v1/payments/", data=build_payment(
            apt["id"], amount_paid="0"
        ))
        assert resp.status == 400

    def test_payment_negative_amount_rejected(
        self, admin_api: APIRequestContext, seeded_expense
    ):
        apt = seeded_expense["apartment"]
        if not apt:
            pytest.skip("No apartment")
        resp = admin_api.post("/api/v1/payments/", data=build_payment(
            apt["id"], amount_paid="-50"
        ))
        assert resp.status == 400

    def test_payment_missing_apartment_id(self, admin_api: APIRequestContext):
        resp = admin_api.post("/api/v1/payments/", data={
            "amount_paid": "50", "payment_method": "cash",
            "payment_date": "2026-01-01",
        })
        assert resp.status == 400

    def test_payment_nonexistent_apartment(self, admin_api: APIRequestContext):
        resp = admin_api.post("/api/v1/payments/", data=build_payment(
            "00000000-0000-0000-0000-000000000000", amount_paid="50"
        ))
        assert resp.status in (400, 404)

    def test_payment_invalid_method(self, admin_api: APIRequestContext, seeded_expense):
        apt = seeded_expense["apartment"]
        if not apt:
            pytest.skip("No apartment")
        resp = admin_api.post("/api/v1/payments/", data=build_payment(
            apt["id"], payment_method="bitcoin"
        ))
        assert resp.status == 400

    def test_owner_cannot_record_payment(
        self, owner_api: APIRequestContext, seeded_expense
    ):
        apt = seeded_expense["apartment"]
        if not apt:
            pytest.skip("No apartment")
        resp = owner_api.post("/api/v1/payments/", data=build_payment(apt["id"]))
        assert resp.status == 403

    def test_unauthenticated_payment(self, unauthenticated_api: APIRequestContext):
        resp = unauthenticated_api.post("/api/v1/payments/", data={
            "apartment_id": "fake", "amount_paid": "50",
        })
        assert resp.status == 401
