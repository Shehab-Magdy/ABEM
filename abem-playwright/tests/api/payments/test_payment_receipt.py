"""API tests for payment receipt PDF generation."""

import pytest
from playwright.sync_api import APIRequestContext

from utils.assertions import assert_valid_pdf


@pytest.mark.api
@pytest.mark.payments
class TestPaymentReceipt:

    def test_receipt_returns_pdf(self, admin_api: APIRequestContext, seeded_payment):
        pid = seeded_payment["payment"]["id"]
        resp = admin_api.get(f"/api/v1/payments/{pid}/receipt/")
        assert resp.status == 200
        content_type = resp.headers.get("content-type", "")
        assert "pdf" in content_type.lower(), f"Expected PDF, got {content_type}"
        assert_valid_pdf(resp.body())

    def test_admin_can_access_any_receipt(
        self, admin_api: APIRequestContext, seeded_payment
    ):
        pid = seeded_payment["payment"]["id"]
        resp = admin_api.get(f"/api/v1/payments/{pid}/receipt/")
        assert resp.status == 200

    def test_nonexistent_payment_receipt(self, admin_api: APIRequestContext):
        resp = admin_api.get(
            "/api/v1/payments/00000000-0000-0000-0000-000000000000/receipt/"
        )
        assert resp.status == 404
