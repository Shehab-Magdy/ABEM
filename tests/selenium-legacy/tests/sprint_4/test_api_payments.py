"""
Sprint 4 – Payment Management API Tests
========================================

Covers TC-S4-API-001 … TC-S4-API-035 from ABEM_QA_Strategy_v2.docx

Test class layout:
  TestPaymentCRUD           (5)   – Basic create / list / get, immutability
  TestBalanceEngine         (8)   – Exact / partial / overpayment, balance snapshots
  TestBalanceEndpoint       (4)   – GET /apartments/{id}/balance/ breakdown
  TestPaymentValidation     (9)   – Field-level + cross-field validation
  TestPaymentRBAC           (5)   – Admin vs. owner permissions
  TestPaymentFiltering      (4)   – apartment_id / date / method query params
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from api.payment_api import PaymentAPI
from utils.test_data import PaymentFactory

pytestmark = [
    pytest.mark.api,
    pytest.mark.sprint_4,
]


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S4-API-001 … 005  –  Basic CRUD + immutability
# ═══════════════════════════════════════════════════════════════════════════════

class TestPaymentCRUD:

    @pytest.mark.positive
    def test_create_payment_returns_201(
        self, admin_api, create_temp_building, create_temp_apartment,
        create_temp_category, create_temp_expense
    ):
        """TC-S4-API-001: Recording a valid payment returns HTTP 201."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        cat = create_temp_category(building_id=bld["id"])
        exp = create_temp_expense(building_id=bld["id"], category_id=cat["id"],
                                  amount="100.00", split_type="equal_all")
        pmt_api = PaymentAPI(admin_api)
        resp = pmt_api.create(**PaymentFactory.valid(
            apartment_id=apt["id"], expense_id=exp["id"], amount=50.00
        ))
        assert resp.status_code == 201
        body = resp.json()
        assert "id" in body
        assert "balance_after" in body
        assert "remaining_balance" in body

    @pytest.mark.positive
    def test_list_payments_by_apartment(
        self, admin_api, create_temp_building, create_temp_apartment,
        create_temp_category, create_temp_expense, create_temp_payment
    ):
        """TC-S4-API-002: GET /payments/?apartment_id= returns paginated results."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        cat = create_temp_category(building_id=bld["id"])
        exp = create_temp_expense(building_id=bld["id"], category_id=cat["id"],
                                  amount="200.00", split_type="equal_all")
        create_temp_payment(apartment_id=apt["id"], expense_id=exp["id"], amount=50.00)
        create_temp_payment(apartment_id=apt["id"], amount=30.00)

        pmt_api = PaymentAPI(admin_api)
        resp = pmt_api.list(apartment_id=apt["id"])
        assert resp.status_code == 200
        results = resp.json().get("results", resp.json())
        assert isinstance(results, list)
        assert len(results) >= 2

    @pytest.mark.positive
    def test_get_single_payment(
        self, admin_api, create_temp_building, create_temp_apartment,
        create_temp_category, create_temp_expense, create_temp_payment
    ):
        """TC-S4-API-003: GET /payments/{id}/ returns the payment detail."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        cat = create_temp_category(building_id=bld["id"])
        exp = create_temp_expense(building_id=bld["id"], category_id=cat["id"])
        pmt = create_temp_payment(apartment_id=apt["id"], expense_id=exp["id"])

        pmt_api = PaymentAPI(admin_api)
        resp = pmt_api.get(pmt["id"])
        assert resp.status_code == 200
        assert resp.json()["id"] == pmt["id"]

    @pytest.mark.negative
    def test_patch_payment_returns_405(
        self, admin_api, create_temp_building, create_temp_apartment,
        create_temp_category, create_temp_expense, create_temp_payment
    ):
        """TC-S4-API-004: PATCH on a payment returns 405 (payments are immutable)."""
        from core.api_client import APIClient
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        cat = create_temp_category(building_id=bld["id"])
        exp = create_temp_expense(building_id=bld["id"], category_id=cat["id"])
        pmt = create_temp_payment(apartment_id=apt["id"], expense_id=exp["id"])

        resp = admin_api.patch(f"/payments/{pmt['id']}/", json={"notes": "changed"})
        assert resp.status_code == 405

    @pytest.mark.negative
    def test_delete_payment_returns_405(
        self, admin_api, create_temp_building, create_temp_apartment,
        create_temp_category, create_temp_expense, create_temp_payment
    ):
        """TC-S4-API-005: DELETE on a payment returns 405 (payments are immutable)."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        cat = create_temp_category(building_id=bld["id"])
        exp = create_temp_expense(building_id=bld["id"], category_id=cat["id"])
        pmt = create_temp_payment(apartment_id=apt["id"], expense_id=exp["id"])

        resp = admin_api.delete(f"/payments/{pmt['id']}/")
        assert resp.status_code == 405


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S4-API-006 … 013  –  Balance engine
# ═══════════════════════════════════════════════════════════════════════════════

class TestBalanceEngine:

    def _setup(self, create_temp_building, create_temp_apartment,
               create_temp_category, create_temp_expense,
               amount: float = 100.0):
        """Helper: return (bld, apt, exp) with a fresh split."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        cat = None  # will set below
        return bld, apt

    @pytest.mark.positive
    def test_exact_payment_zeroes_balance(
        self, admin_api, create_temp_building, create_temp_apartment,
        create_temp_category, create_temp_expense, create_temp_payment
    ):
        """TC-S4-API-006: Paying exactly the share amount → balance_after = 0."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        cat = create_temp_category(building_id=bld["id"])
        # 100.00 / 1 apt rounds up to nearest 5 → share = 100.00
        exp = create_temp_expense(building_id=bld["id"], category_id=cat["id"],
                                  amount="100.00", split_type="equal_all")

        pmt_api = PaymentAPI(admin_api)
        # Get balance endpoint to find exact share owed
        bal_resp = pmt_api.get_balance(apt["id"])
        assert bal_resp.status_code == 200
        share = float(bal_resp.json()["current_balance"])

        pmt = create_temp_payment(apartment_id=apt["id"], expense_id=exp["id"],
                                  amount=share)
        assert float(pmt["balance_after"]) == 0.0

    @pytest.mark.positive
    def test_partial_payment_reduces_balance(
        self, admin_api, create_temp_building, create_temp_apartment,
        create_temp_category, create_temp_expense, create_temp_payment
    ):
        """TC-S4-API-007: Partial payment → balance_after = share - payment."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        cat = create_temp_category(building_id=bld["id"])
        exp = create_temp_expense(building_id=bld["id"], category_id=cat["id"],
                                  amount="100.00", split_type="equal_all")

        pmt_api = PaymentAPI(admin_api)
        bal_before = float(pmt_api.get_balance(apt["id"]).json()["current_balance"])

        partial = round(bal_before / 2, 2)
        pmt = create_temp_payment(apartment_id=apt["id"], expense_id=exp["id"],
                                  amount=partial)

        expected_after = round(bal_before - partial, 2)
        assert abs(float(pmt["balance_after"]) - expected_after) < 0.01

    @pytest.mark.positive
    def test_overpayment_creates_credit(
        self, admin_api, create_temp_building, create_temp_apartment,
        create_temp_category, create_temp_expense, create_temp_payment
    ):
        """TC-S4-API-008: Paying more than owed → balance_after < 0 (credit)."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        cat = create_temp_category(building_id=bld["id"])
        exp = create_temp_expense(building_id=bld["id"], category_id=cat["id"],
                                  amount="100.00", split_type="equal_all")

        pmt_api = PaymentAPI(admin_api)
        share = float(pmt_api.get_balance(apt["id"]).json()["current_balance"])

        overpayment = share + 50.00
        pmt = create_temp_payment(apartment_id=apt["id"], expense_id=exp["id"],
                                  amount=overpayment)

        assert float(pmt["balance_after"]) < 0.0, "Overpayment should produce negative balance"

    @pytest.mark.positive
    def test_credit_balance_persists_as_negative(
        self, admin_api, create_temp_building, create_temp_apartment,
        create_temp_category, create_temp_expense, create_temp_payment
    ):
        """TC-S4-API-009: Credit balance is visible on the balance endpoint."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        cat = create_temp_category(building_id=bld["id"])
        exp = create_temp_expense(building_id=bld["id"], category_id=cat["id"],
                                  amount="100.00", split_type="equal_all")

        pmt_api = PaymentAPI(admin_api)
        share = float(pmt_api.get_balance(apt["id"]).json()["current_balance"])
        create_temp_payment(apartment_id=apt["id"], expense_id=exp["id"],
                            amount=share + 50.00)

        bal = pmt_api.get_balance(apt["id"]).json()
        assert float(bal["current_balance"]) < 0.0
        assert bal["is_credit"] is True

    @pytest.mark.positive
    def test_multiple_partial_payments_accumulate(
        self, admin_api, create_temp_building, create_temp_apartment,
        create_temp_category, create_temp_expense, create_temp_payment
    ):
        """TC-S4-API-010: Three partial payments summing to share → balance = 0."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        cat = create_temp_category(building_id=bld["id"])
        # 150 / 1 apt rounds up to 150 (already multiple of 5)
        exp = create_temp_expense(building_id=bld["id"], category_id=cat["id"],
                                  amount="150.00", split_type="equal_all")

        pmt_api = PaymentAPI(admin_api)
        share = float(pmt_api.get_balance(apt["id"]).json()["current_balance"])
        third = round(share / 3, 2)

        create_temp_payment(apartment_id=apt["id"], expense_id=exp["id"], amount=third)
        create_temp_payment(apartment_id=apt["id"], amount=third)
        create_temp_payment(apartment_id=apt["id"], amount=share - 2 * third)

        final_bal = float(pmt_api.get_balance(apt["id"]).json()["current_balance"])
        assert abs(final_bal) < 0.05  # allow small Decimal rounding

    @pytest.mark.positive
    def test_balance_before_snapshot_captured(
        self, admin_api, create_temp_building, create_temp_apartment,
        create_temp_category, create_temp_expense, create_temp_payment
    ):
        """TC-S4-API-011: balance_before = apartment balance before the payment."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        cat = create_temp_category(building_id=bld["id"])
        exp = create_temp_expense(building_id=bld["id"], category_id=cat["id"],
                                  amount="100.00", split_type="equal_all")

        pmt_api = PaymentAPI(admin_api)
        bal_before = float(pmt_api.get_balance(apt["id"]).json()["current_balance"])
        pmt = create_temp_payment(apartment_id=apt["id"], expense_id=exp["id"], amount=40.00)

        assert abs(float(pmt["balance_before"]) - bal_before) < 0.01

    @pytest.mark.positive
    def test_balance_after_equals_before_minus_paid(
        self, admin_api, create_temp_building, create_temp_apartment,
        create_temp_category, create_temp_expense, create_temp_payment
    ):
        """TC-S4-API-012: balance_after = balance_before - amount_paid."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        cat = create_temp_category(building_id=bld["id"])
        exp = create_temp_expense(building_id=bld["id"], category_id=cat["id"],
                                  amount="100.00", split_type="equal_all")

        amount = 35.00
        pmt = create_temp_payment(apartment_id=apt["id"], expense_id=exp["id"], amount=amount)
        expected = float(pmt["balance_before"]) - amount
        assert abs(float(pmt["balance_after"]) - expected) < 0.01

    @pytest.mark.positive
    def test_decimal_precision_no_float_errors(
        self, admin_api, create_temp_building, create_temp_apartment,
        create_temp_category, create_temp_expense, create_temp_payment
    ):
        """TC-S4-API-013: Decimal arithmetic — no floating-point precision loss."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        cat = create_temp_category(building_id=bld["id"])
        exp = create_temp_expense(building_id=bld["id"], category_id=cat["id"],
                                  amount="99.99", split_type="equal_all")

        pmt = create_temp_payment(apartment_id=apt["id"], expense_id=exp["id"], amount=33.33)
        # balance_after should be balance_before - 33.33 (exact Decimal, not float)
        diff = Decimal(str(pmt["balance_before"])) - Decimal("33.33")
        assert abs(Decimal(str(pmt["balance_after"])) - diff) < Decimal("0.01")


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S4-API-014 … 017  –  Balance endpoint
# ═══════════════════════════════════════════════════════════════════════════════

class TestBalanceEndpoint:

    @pytest.mark.positive
    def test_balance_endpoint_returns_200(
        self, admin_api, create_temp_building, create_temp_apartment
    ):
        """TC-S4-API-014: GET /apartments/{id}/balance/ returns 200."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        pmt_api = PaymentAPI(admin_api)
        resp = pmt_api.get_balance(apt["id"])
        assert resp.status_code == 200

    @pytest.mark.positive
    def test_balance_endpoint_fields(
        self, admin_api, create_temp_building, create_temp_apartment
    ):
        """TC-S4-API-015: Balance breakdown includes required fields."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        pmt_api = PaymentAPI(admin_api)
        body = pmt_api.get_balance(apt["id"]).json()
        for field in ("apartment_id", "current_balance", "total_owed", "total_paid", "is_credit"):
            assert field in body, f"Missing field: {field}"

    @pytest.mark.positive
    def test_balance_total_owed_matches_expense_share(
        self, admin_api, create_temp_building, create_temp_apartment,
        create_temp_category, create_temp_expense
    ):
        """TC-S4-API-016: total_owed reflects sum of ApartmentExpense shares."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        cat = create_temp_category(building_id=bld["id"])
        # 100 / 1 = 100 (already multiple of 5)
        create_temp_expense(building_id=bld["id"], category_id=cat["id"],
                            amount="100.00", split_type="equal_all")

        pmt_api = PaymentAPI(admin_api)
        body = pmt_api.get_balance(apt["id"]).json()
        assert float(body["total_owed"]) >= 100.0

    @pytest.mark.positive
    def test_balance_is_credit_false_for_fresh_apartment(
        self, admin_api, create_temp_building, create_temp_apartment
    ):
        """TC-S4-API-017: Fresh apartment with no payments has is_credit = False."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        pmt_api = PaymentAPI(admin_api)
        body = pmt_api.get_balance(apt["id"]).json()
        assert body["is_credit"] is False


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S4-API-018 … 026  –  Validation
# ═══════════════════════════════════════════════════════════════════════════════

class TestPaymentValidation:

    @pytest.mark.negative
    def test_zero_amount_returns_400(
        self, admin_api, create_temp_building, create_temp_apartment
    ):
        """TC-S4-API-018: amount_paid = 0 → 400."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        pmt_api = PaymentAPI(admin_api)
        resp = pmt_api.create(**PaymentFactory.zero_amount(apt["id"]))
        assert resp.status_code == 400

    @pytest.mark.negative
    def test_negative_amount_returns_400(
        self, admin_api, create_temp_building, create_temp_apartment
    ):
        """TC-S4-API-019: amount_paid < 0 → 400."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        pmt_api = PaymentAPI(admin_api)
        resp = pmt_api.create(**PaymentFactory.negative_amount(apt["id"]))
        assert resp.status_code == 400

    @pytest.mark.negative
    def test_missing_amount_returns_400(
        self, admin_api, create_temp_building, create_temp_apartment
    ):
        """TC-S4-API-020: Missing amount_paid → 400."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        pmt_api = PaymentAPI(admin_api)
        resp = pmt_api.create(**PaymentFactory.missing_amount(apt["id"]))
        assert resp.status_code == 400

    @pytest.mark.negative
    def test_missing_date_returns_400(
        self, admin_api, create_temp_building, create_temp_apartment
    ):
        """TC-S4-API-021: Missing payment_date → 400."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        pmt_api = PaymentAPI(admin_api)
        resp = pmt_api.create(**PaymentFactory.missing_date(apt["id"]))
        assert resp.status_code == 400

    @pytest.mark.positive
    def test_payment_method_cash_accepted(
        self, admin_api, create_temp_building, create_temp_apartment
    ):
        """TC-S4-API-022: payment_method=cash → 201."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        pmt_api = PaymentAPI(admin_api)
        resp = pmt_api.create(**PaymentFactory.valid(apt["id"], amount=10.00))
        assert resp.status_code == 201

    @pytest.mark.positive
    def test_payment_method_bank_transfer_accepted(
        self, admin_api, create_temp_building, create_temp_apartment
    ):
        """TC-S4-API-023: payment_method=bank_transfer → 201."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        pmt_api = PaymentAPI(admin_api)
        resp = pmt_api.create(**PaymentFactory.bank_transfer(apt["id"]))
        assert resp.status_code == 201

    @pytest.mark.positive
    def test_payment_method_cheque_accepted(
        self, admin_api, create_temp_building, create_temp_apartment
    ):
        """TC-S4-API-024: payment_method=cheque → 201."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        pmt_api = PaymentAPI(admin_api)
        resp = pmt_api.create(**PaymentFactory.cheque(apt["id"]))
        assert resp.status_code == 201

    @pytest.mark.negative
    def test_invalid_payment_method_returns_400(
        self, admin_api, create_temp_building, create_temp_apartment
    ):
        """TC-S4-API-025: Unknown payment_method → 400."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        pmt_api = PaymentAPI(admin_api)
        resp = pmt_api.create(**PaymentFactory.invalid_method(apt["id"]))
        assert resp.status_code == 400

    @pytest.mark.negative
    def test_payment_for_unassigned_expense_returns_400(
        self, admin_api, create_temp_building, create_temp_apartment,
        create_temp_category, create_temp_expense
    ):
        """TC-S4-API-026: Expense not assigned to the apartment → 400."""
        bld1 = create_temp_building(num_floors=10)
        bld2 = create_temp_building(num_floors=10)
        apt1 = create_temp_apartment(building_id=bld1["id"])
        apt2 = create_temp_apartment(building_id=bld2["id"])
        cat = create_temp_category(building_id=bld2["id"])
        # Expense belongs to bld2 and is split across apt2 — NOT apt1
        exp = create_temp_expense(building_id=bld2["id"], category_id=cat["id"],
                                  amount="100.00", split_type="equal_all")

        pmt_api = PaymentAPI(admin_api)
        resp = pmt_api.create(**PaymentFactory.valid(
            apartment_id=apt1["id"], expense_id=exp["id"]
        ))
        assert resp.status_code == 400


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S4-API-027 … 031  –  RBAC
# ═══════════════════════════════════════════════════════════════════════════════

class TestPaymentRBAC:

    @pytest.mark.positive
    def test_owner_can_get_own_payment_history(
        self, admin_api, owner_api, owner_with_id,
        create_temp_building, create_temp_apartment,
        create_temp_category, create_temp_expense, create_temp_payment
    ):
        """TC-S4-API-027: Owner GET /payments/?apartment_id=<own> → 200."""
        owner_client, owner_id = owner_with_id
        bld = create_temp_building(num_floors=10)
        # Assign the apartment to the owner
        from api.apartment_api import ApartmentAPI
        apt = create_temp_apartment(building_id=bld["id"])
        ApartmentAPI(admin_api).update(apt["id"], owner_id=owner_id)

        cat = create_temp_category(building_id=bld["id"])
        exp = create_temp_expense(building_id=bld["id"], category_id=cat["id"])
        create_temp_payment(apartment_id=apt["id"], expense_id=exp["id"])

        pmt_api = PaymentAPI(owner_client)
        resp = pmt_api.list(apartment_id=apt["id"])
        assert resp.status_code == 200

    @pytest.mark.negative
    def test_owner_cannot_get_other_apartment_payments(
        self, admin_api, owner_api, owner_with_id,
        create_temp_building, create_temp_apartment,
        create_temp_category, create_temp_expense, create_temp_payment
    ):
        """TC-S4-API-028: Owner GET /payments/?apartment_id=<other> → empty list."""
        owner_client, owner_id = owner_with_id
        bld = create_temp_building(num_floors=10)
        apt_other = create_temp_apartment(building_id=bld["id"])  # owner NOT assigned

        cat = create_temp_category(building_id=bld["id"])
        exp = create_temp_expense(building_id=bld["id"], category_id=cat["id"])
        create_temp_payment(apartment_id=apt_other["id"], expense_id=exp["id"])

        pmt_api = PaymentAPI(owner_client)
        resp = pmt_api.list(apartment_id=apt_other["id"])
        assert resp.status_code == 200
        results = resp.json().get("results", resp.json())
        # Owner should see no payments for apartments they don't own
        assert len(results) == 0

    @pytest.mark.negative
    def test_owner_cannot_create_payment(
        self, owner_api, owner_with_id,
        create_temp_building, create_temp_apartment
    ):
        """TC-S4-API-029: Owner POST /payments/ → 403."""
        owner_client, _ = owner_with_id
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        pmt_api = PaymentAPI(owner_client)
        resp = pmt_api.create(**PaymentFactory.valid(apartment_id=apt["id"]))
        assert resp.status_code == 403

    @pytest.mark.positive
    def test_admin_sees_all_payments(
        self, admin_api, create_temp_building, create_temp_apartment,
        create_temp_category, create_temp_expense, create_temp_payment
    ):
        """TC-S4-API-030: Admin GET /payments/ returns payments across all apartments."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        cat = create_temp_category(building_id=bld["id"])
        exp = create_temp_expense(building_id=bld["id"], category_id=cat["id"])
        create_temp_payment(apartment_id=apt["id"], expense_id=exp["id"])

        pmt_api = PaymentAPI(admin_api)
        resp = pmt_api.list()
        assert resp.status_code == 200
        results = resp.json().get("results", resp.json())
        assert len(results) >= 1

    @pytest.mark.positive
    def test_unauthenticated_returns_401(self, unauthenticated_api):
        """TC-S4-API-031: Unauthenticated GET /payments/ → 401."""
        pmt_api = PaymentAPI(unauthenticated_api)
        resp = pmt_api.list()
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S4-API-032 … 035  –  Filtering
# ═══════════════════════════════════════════════════════════════════════════════

class TestPaymentFiltering:

    @pytest.mark.positive
    def test_filter_by_apartment_id(
        self, admin_api, create_temp_building, create_temp_apartment,
        create_temp_category, create_temp_expense, create_temp_payment
    ):
        """TC-S4-API-032: ?apartment_id= returns only that apartment's payments."""
        bld = create_temp_building(num_floors=10)
        apt1 = create_temp_apartment(building_id=bld["id"])
        apt2 = create_temp_apartment(building_id=bld["id"])
        cat = create_temp_category(building_id=bld["id"])
        exp = create_temp_expense(building_id=bld["id"], category_id=cat["id"],
                                  amount="200.00", split_type="equal_all")

        create_temp_payment(apartment_id=apt1["id"], expense_id=exp["id"], amount=20.00)
        create_temp_payment(apartment_id=apt2["id"], amount=15.00)

        pmt_api = PaymentAPI(admin_api)
        resp = pmt_api.list(apartment_id=apt1["id"])
        assert resp.status_code == 200
        results = resp.json().get("results", resp.json())
        assert all(r["apartment_id"] == apt1["id"] for r in results)

    @pytest.mark.positive
    def test_filter_by_date_range(
        self, admin_api, create_temp_building, create_temp_apartment,
        create_temp_category, create_temp_expense, create_temp_payment
    ):
        """TC-S4-API-033: ?date_from=&date_to= narrows results to date range."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        cat = create_temp_category(building_id=bld["id"])
        exp = create_temp_expense(building_id=bld["id"], category_id=cat["id"])

        create_temp_payment(apartment_id=apt["id"], expense_id=exp["id"],
                            amount=10.00, payment_date="2026-01-15")

        pmt_api = PaymentAPI(admin_api)
        resp = pmt_api.list(
            apartment_id=apt["id"],
            date_from="2026-01-01",
            date_to="2026-01-31",
        )
        assert resp.status_code == 200
        results = resp.json().get("results", resp.json())
        for r in results:
            assert "2026-01" in r["payment_date"]

    @pytest.mark.positive
    def test_filter_by_payment_method(
        self, admin_api, create_temp_building, create_temp_apartment,
        create_temp_category, create_temp_expense, create_temp_payment
    ):
        """TC-S4-API-034: ?payment_method=cash returns only cash payments."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        cat = create_temp_category(building_id=bld["id"])
        exp = create_temp_expense(building_id=bld["id"], category_id=cat["id"],
                                  amount="200.00", split_type="equal_all")

        create_temp_payment(apartment_id=apt["id"], expense_id=exp["id"],
                            amount=10.00, payment_method="cash")
        create_temp_payment(apartment_id=apt["id"], amount=10.00, payment_method="cheque")

        pmt_api = PaymentAPI(admin_api)
        resp = pmt_api.list(apartment_id=apt["id"], payment_method="cash")
        assert resp.status_code == 200
        results = resp.json().get("results", resp.json())
        assert all(r["payment_method"] == "cash" for r in results)

    @pytest.mark.positive
    def test_payment_without_expense_returns_201(
        self, admin_api, create_temp_building, create_temp_apartment
    ):
        """TC-S4-API-035: General payment (no expense_id) records successfully → 201."""
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"])
        pmt_api = PaymentAPI(admin_api)
        # No expense_id — general payment / advance
        resp = pmt_api.create(**PaymentFactory.valid(apartment_id=apt["id"], amount=25.00))
        assert resp.status_code == 201
        assert resp.json().get("expense_id") is None
