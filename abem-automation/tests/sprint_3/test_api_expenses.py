"""
Sprint 3 – Expense Management API Tests
========================================

Covers all 40 API test cases from ABEM_QA_Strategy_v2.docx Sprint 3:
  TC-S3-API-001 … TC-S3-API-040

Categories:
  - Expense CRUD (TC-001 → 006)
  - Validation negatives (TC-007 → 011)
  - Split Engine (TC-012 → 021)
  - Data Integrity (TC-022)
  - Recurring Expenses (TC-023 → 027)
  - File Upload (TC-028 → 033)
  - RBAC (TC-034 → 036)
  - Categories (TC-037 → 038)
  - Filtering (TC-039 → 040)
"""
from __future__ import annotations

import io
import math
from decimal import Decimal

import pytest

from api.expense_api import ExpenseAPI
from api.category_api import CategoryAPI
from api.apartment_api import ApartmentAPI
from utils.test_data import ExpenseFactory, CategoryFactory, ApartmentFactory, BuildingFactory

pytestmark = [
    pytest.mark.api,
    pytest.mark.sprint_3,
]


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _round_up_5(amount: float) -> float:
    """Mirror the backend's rounding: ceiling to nearest 5."""
    return math.ceil(amount / 5) * 5


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S3-API-001 … 006  –  Expense CRUD
# ═══════════════════════════════════════════════════════════════════════════════

class TestExpenseCRUD:
    """Happy-path CRUD operations."""

    @pytest.mark.positive
    def test_create_valid_expense_returns_201(
        self, admin_api, create_temp_building, create_temp_category
    ):
        """TC-S3-API-001: Admin POST /expenses/ with valid data returns 201."""
        expense_api = ExpenseAPI(admin_api)
        bld = create_temp_building(num_floors=3)
        cat = create_temp_category(building_id=bld["id"])

        payload = ExpenseFactory.valid(bld["id"], cat["id"], amount=200.0)
        resp = expense_api.create(**payload)
        assert resp.status_code == 201
        body = resp.json()
        expense_id = body["id"]
        expense_api.delete(expense_id)

    @pytest.mark.positive
    def test_create_response_contains_required_fields(
        self, admin_api, create_temp_building, create_temp_category
    ):
        """TC-S3-API-002: Expense response contains id, amount, category_id, expense_date, building_id."""
        expense_api = ExpenseAPI(admin_api)
        bld = create_temp_building(num_floors=3)
        cat = create_temp_category(building_id=bld["id"])

        payload = ExpenseFactory.valid(bld["id"], cat["id"])
        resp = expense_api.create(**payload)
        body = resp.json()

        for field in ("id", "amount", "category_id", "expense_date", "building_id"):
            assert field in body, f"Missing field '{field}' in response"

        expense_api.delete(body["id"])

    @pytest.mark.positive
    def test_list_expenses_by_building(
        self, admin_api, create_temp_building, create_temp_category
    ):
        """TC-S3-API-003: GET /expenses/?building_id={id} returns expenses for that building."""
        expense_api = ExpenseAPI(admin_api)
        bld = create_temp_building(num_floors=3)
        cat = create_temp_category(building_id=bld["id"])

        exp1 = expense_api.create(**ExpenseFactory.valid(bld["id"], cat["id"])).json()
        exp2 = expense_api.create(**ExpenseFactory.valid(bld["id"], cat["id"])).json()

        resp = expense_api.list(building_id=bld["id"])
        assert resp.status_code == 200
        ids = [e["id"] for e in (resp.json().get("results") or resp.json())]
        assert exp1["id"] in ids
        assert exp2["id"] in ids

        expense_api.delete(exp1["id"])
        expense_api.delete(exp2["id"])

    @pytest.mark.positive
    def test_retrieve_expense_detail_contains_shares(
        self, admin_api, create_temp_building, create_temp_category, create_temp_apartment
    ):
        """TC-S3-API-004: GET /expenses/{id}/ returns expense detail with apartment_shares."""
        expense_api = ExpenseAPI(admin_api)
        bld = create_temp_building(num_floors=3)
        create_temp_apartment(building_id=bld["id"], num_floors=3)
        cat = create_temp_category(building_id=bld["id"])

        exp = expense_api.create(**ExpenseFactory.valid(bld["id"], cat["id"])).json()

        resp = expense_api.get(exp["id"])
        assert resp.status_code == 200
        body = resp.json()
        assert "apartment_shares" in body

        expense_api.delete(exp["id"])

    @pytest.mark.positive
    def test_patch_expense_updates_amount(
        self, admin_api, create_temp_building, create_temp_category
    ):
        """TC-S3-API-005: PATCH /expenses/{id}/ updates amount."""
        expense_api = ExpenseAPI(admin_api)
        bld = create_temp_building(num_floors=3)
        cat = create_temp_category(building_id=bld["id"])

        exp = expense_api.create(**ExpenseFactory.valid(bld["id"], cat["id"], amount=100.0)).json()
        resp = expense_api.update(exp["id"], amount="250.00")
        assert resp.status_code == 200
        assert resp.json()["amount"] == "250.00"

        expense_api.delete(exp["id"])

    @pytest.mark.positive
    def test_delete_expense_soft_deletes(
        self, admin_api, create_temp_building, create_temp_category
    ):
        """TC-S3-API-006: DELETE /expenses/{id}/ soft-deletes — subsequent GET returns 404."""
        expense_api = ExpenseAPI(admin_api)
        bld = create_temp_building(num_floors=3)
        cat = create_temp_category(building_id=bld["id"])

        exp = expense_api.create(**ExpenseFactory.valid(bld["id"], cat["id"])).json()
        del_resp = expense_api.delete(exp["id"])
        assert del_resp.status_code == 204

        get_resp = expense_api.get(exp["id"])
        assert get_resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S3-API-007 … 011  –  Validation
# ═══════════════════════════════════════════════════════════════════════════════

class TestExpenseValidation:

    @pytest.mark.negative
    def test_zero_amount_returns_400(
        self, admin_api, create_temp_building, create_temp_category
    ):
        """TC-S3-API-007: POST with amount=0 returns 400."""
        expense_api = ExpenseAPI(admin_api)
        bld = create_temp_building(num_floors=3)
        cat = create_temp_category(building_id=bld["id"])
        resp = expense_api.create(**ExpenseFactory.zero_amount(bld["id"], cat["id"]))
        assert resp.status_code == 400

    @pytest.mark.negative
    def test_negative_amount_returns_400(
        self, admin_api, create_temp_building, create_temp_category
    ):
        """TC-S3-API-008: POST with negative amount returns 400."""
        expense_api = ExpenseAPI(admin_api)
        bld = create_temp_building(num_floors=3)
        cat = create_temp_category(building_id=bld["id"])
        resp = expense_api.create(**ExpenseFactory.negative_amount(bld["id"], cat["id"]))
        assert resp.status_code == 400

    @pytest.mark.negative
    def test_missing_category_returns_400(
        self, admin_api, create_temp_building
    ):
        """TC-S3-API-009: POST with missing category_id returns 400."""
        expense_api = ExpenseAPI(admin_api)
        bld = create_temp_building(num_floors=3)
        resp = expense_api.create(**ExpenseFactory.missing_category(bld["id"]))
        assert resp.status_code == 400

    @pytest.mark.negative
    def test_missing_date_returns_400(
        self, admin_api, create_temp_building, create_temp_category
    ):
        """TC-S3-API-010: POST with missing expense_date returns 400."""
        expense_api = ExpenseAPI(admin_api)
        bld = create_temp_building(num_floors=3)
        cat = create_temp_category(building_id=bld["id"])
        resp = expense_api.create(**ExpenseFactory.missing_date(bld["id"], cat["id"]))
        assert resp.status_code == 400

    @pytest.mark.positive
    def test_future_date_is_accepted(
        self, admin_api, create_temp_building, create_temp_category
    ):
        """TC-S3-API-011: POST with future date_incurred is accepted (valid business case)."""
        expense_api = ExpenseAPI(admin_api)
        bld = create_temp_building(num_floors=3)
        cat = create_temp_category(building_id=bld["id"])
        payload = ExpenseFactory.future_date(bld["id"], cat["id"])
        resp = expense_api.create(**payload)
        assert resp.status_code == 201
        expense_api.delete(resp.json()["id"])


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S3-API-012 … 021  –  Split Engine
# ═══════════════════════════════════════════════════════════════════════════════

class TestSplitEngine:

    def _setup_building_with_apartments(
        self, create_temp_building, create_temp_apartment, n: int, unit_type: str = "apartment"
    ):
        """Helper: create a building with exactly n apartments of given type."""
        bld = create_temp_building(num_floors=10)
        for _ in range(n):
            create_temp_apartment(
                building_id=bld["id"], num_floors=10, unit_type=unit_type
            )
        return bld

    @pytest.mark.positive
    def test_equal_split_exact_no_rounding(
        self, admin_api, create_temp_building, create_temp_category, create_temp_apartment
    ):
        """TC-S3-API-012: 100.00 / 4 apartments = 25.00 each (exact, no rounding)."""
        expense_api = ExpenseAPI(admin_api)
        bld = self._setup_building_with_apartments(
            create_temp_building, create_temp_apartment, n=4
        )
        cat = create_temp_category(building_id=bld["id"])

        exp = expense_api.create(
            **ExpenseFactory.valid(bld["id"], cat["id"], amount=100.0)
        ).json()

        detail = expense_api.get(exp["id"]).json()
        shares = detail["apartment_shares"]
        assert len(shares) == 4
        for s in shares:
            assert float(s["share_amount"]) == 25.0

        expense_api.delete(exp["id"])

    @pytest.mark.positive
    def test_equal_split_rounds_up_to_nearest_5(
        self, admin_api, create_temp_building, create_temp_category, create_temp_apartment
    ):
        """TC-S3-API-013: 101.00 / 4 apartments rounds UP to 30.00 each."""
        expense_api = ExpenseAPI(admin_api)
        bld = self._setup_building_with_apartments(
            create_temp_building, create_temp_apartment, n=4
        )
        cat = create_temp_category(building_id=bld["id"])

        exp = expense_api.create(
            **ExpenseFactory.valid(bld["id"], cat["id"], amount=101.0)
        ).json()

        detail = expense_api.get(exp["id"]).json()
        for s in detail["apartment_shares"]:
            assert float(s["share_amount"]) == 30.0, (
                f"Expected 30.00 but got {s['share_amount']}"
            )

        expense_api.delete(exp["id"])

    @pytest.mark.positive
    def test_equal_split_103_over_3_rounds_up_to_35(
        self, admin_api, create_temp_building, create_temp_category, create_temp_apartment
    ):
        """TC-S3-API-014: 103.00 / 3 apartments rounds UP to 35.00 each."""
        expense_api = ExpenseAPI(admin_api)
        bld = self._setup_building_with_apartments(
            create_temp_building, create_temp_apartment, n=3
        )
        cat = create_temp_category(building_id=bld["id"])

        exp = expense_api.create(
            **ExpenseFactory.valid(bld["id"], cat["id"], amount=103.0)
        ).json()

        detail = expense_api.get(exp["id"]).json()
        for s in detail["apartment_shares"]:
            assert float(s["share_amount"]) == 35.0

        expense_api.delete(exp["id"])

    @pytest.mark.positive
    def test_type_based_split_apartments_only(
        self, admin_api, create_temp_building, create_temp_category, create_temp_apartment
    ):
        """TC-S3-API-015: equal_apartments split excludes stores."""
        expense_api = ExpenseAPI(admin_api)
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"], num_floors=10, unit_type="apartment")
        store = create_temp_apartment(building_id=bld["id"], num_floors=10, unit_type="store")
        cat = create_temp_category(building_id=bld["id"])

        payload = ExpenseFactory.valid(bld["id"], cat["id"], amount=100.0)
        payload["split_type"] = "equal_apartments"
        exp = expense_api.create(**payload).json()

        detail = expense_api.get(exp["id"]).json()
        share_apt_ids = [str(s["apartment_id"]) for s in detail["apartment_shares"]]
        assert apt["id"] in share_apt_ids
        assert store["id"] not in share_apt_ids

        expense_api.delete(exp["id"])

    @pytest.mark.positive
    def test_type_based_split_stores_only(
        self, admin_api, create_temp_building, create_temp_category, create_temp_apartment
    ):
        """TC-S3-API-016: equal_stores split excludes apartments."""
        expense_api = ExpenseAPI(admin_api)
        bld = create_temp_building(num_floors=10)
        apt = create_temp_apartment(building_id=bld["id"], num_floors=10, unit_type="apartment")
        store = create_temp_apartment(building_id=bld["id"], num_floors=10, unit_type="store")
        cat = create_temp_category(building_id=bld["id"])

        payload = ExpenseFactory.valid(bld["id"], cat["id"], amount=100.0)
        payload["split_type"] = "equal_stores"
        exp = expense_api.create(**payload).json()

        detail = expense_api.get(exp["id"]).json()
        share_apt_ids = [str(s["apartment_id"]) for s in detail["apartment_shares"]]
        assert store["id"] in share_apt_ids
        assert apt["id"] not in share_apt_ids

        expense_api.delete(exp["id"])

    @pytest.mark.positive
    def test_custom_split_assigns_only_selected_apartments(
        self, admin_api, create_temp_building, create_temp_category, create_temp_apartment
    ):
        """TC-S3-API-017: Custom subset split — only selected apartments receive a share."""
        expense_api = ExpenseAPI(admin_api)
        bld = create_temp_building(num_floors=10)
        apt1 = create_temp_apartment(building_id=bld["id"], num_floors=10)
        apt2 = create_temp_apartment(building_id=bld["id"], num_floors=10)
        apt3 = create_temp_apartment(building_id=bld["id"], num_floors=10)
        cat = create_temp_category(building_id=bld["id"])

        payload = ExpenseFactory.custom_split(bld["id"], cat["id"], [apt1["id"], apt2["id"]])
        exp = expense_api.create(**payload).json()

        detail = expense_api.get(exp["id"]).json()
        share_apt_ids = [str(s["apartment_id"]) for s in detail["apartment_shares"]]
        assert apt1["id"] in share_apt_ids
        assert apt2["id"] in share_apt_ids
        assert apt3["id"] not in share_apt_ids

        expense_api.delete(exp["id"])

    @pytest.mark.positive
    def test_rounding_is_always_up(
        self, admin_api, create_temp_building, create_temp_category, create_temp_apartment
    ):
        """TC-S3-API-018: Rounding is always UP — never down."""
        expense_api = ExpenseAPI(admin_api)
        bld = self._setup_building_with_apartments(
            create_temp_building, create_temp_apartment, n=3
        )
        cat = create_temp_category(building_id=bld["id"])

        # 50.01 / 3 = 16.67 → should round UP to 20.00 (nearest 5 above 16.67)
        exp = expense_api.create(
            **ExpenseFactory.valid(bld["id"], cat["id"], amount=50.01)
        ).json()

        detail = expense_api.get(exp["id"]).json()
        for s in detail["apartment_shares"]:
            share = float(s["share_amount"])
            raw = 50.01 / 3
            assert share >= raw, f"share {share} is below raw {raw}"
            assert share % 5 == 0, f"share {share} is not a multiple of 5"

        expense_api.delete(exp["id"])

    @pytest.mark.positive
    def test_single_apartment_receives_full_expense_rounded(
        self, admin_api, create_temp_building, create_temp_category, create_temp_apartment
    ):
        """TC-S3-API-019: Single apartment gets full expense amount (rounded up)."""
        expense_api = ExpenseAPI(admin_api)
        bld = create_temp_building(num_floors=5)
        create_temp_apartment(building_id=bld["id"], num_floors=5)
        cat = create_temp_category(building_id=bld["id"])

        exp = expense_api.create(
            **ExpenseFactory.valid(bld["id"], cat["id"], amount=103.0)
        ).json()

        detail = expense_api.get(exp["id"]).json()
        assert len(detail["apartment_shares"]) == 1
        assert float(detail["apartment_shares"][0]["share_amount"]) == 105.0

        expense_api.delete(exp["id"])

    @pytest.mark.positive
    def test_total_collected_gte_original_expense(
        self, admin_api, create_temp_building, create_temp_category, create_temp_apartment
    ):
        """TC-S3-API-020: Total collected after rounding >= original expense amount."""
        expense_api = ExpenseAPI(admin_api)
        bld = self._setup_building_with_apartments(
            create_temp_building, create_temp_apartment, n=3
        )
        cat = create_temp_category(building_id=bld["id"])

        original_amount = 101.0
        exp = expense_api.create(
            **ExpenseFactory.valid(bld["id"], cat["id"], amount=original_amount)
        ).json()

        detail = expense_api.get(exp["id"]).json()
        total_collected = sum(float(s["share_amount"]) for s in detail["apartment_shares"])
        assert total_collected >= original_amount, (
            f"Total collected {total_collected} < original {original_amount}"
        )

        expense_api.delete(exp["id"])

    @pytest.mark.positive
    def test_create_expense_triggers_apartment_expense_rows(
        self, admin_api, create_temp_building, create_temp_category, create_temp_apartment
    ):
        """TC-S3-API-021: Creating expense triggers apartment_expenses rows for all units."""
        expense_api = ExpenseAPI(admin_api)
        bld = create_temp_building(num_floors=5)
        apts = [
            create_temp_apartment(building_id=bld["id"], num_floors=5) for _ in range(3)
        ]
        cat = create_temp_category(building_id=bld["id"])

        exp = expense_api.create(**ExpenseFactory.valid(bld["id"], cat["id"])).json()

        detail = expense_api.get(exp["id"]).json()
        assert len(detail["apartment_shares"]) == 3

        expense_api.delete(exp["id"])


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S3-API-022  –  Data Integrity
# ═══════════════════════════════════════════════════════════════════════════════

class TestDataIntegrity:

    @pytest.mark.positive
    def test_each_apartment_expense_row_has_correct_share_amount(
        self, admin_api, create_temp_building, create_temp_category, create_temp_apartment
    ):
        """TC-S3-API-022: Each apartment_expenses row has correct share_amount after split."""
        expense_api = ExpenseAPI(admin_api)
        bld = create_temp_building(num_floors=5)
        for _ in range(4):
            create_temp_apartment(building_id=bld["id"], num_floors=5)
        cat = create_temp_category(building_id=bld["id"])

        exp = expense_api.create(
            **ExpenseFactory.valid(bld["id"], cat["id"], amount=100.0)
        ).json()

        detail = expense_api.get(exp["id"]).json()
        for s in detail["apartment_shares"]:
            expected = _round_up_5(100.0 / 4)  # 25.0 exact
            assert float(s["share_amount"]) == expected

        expense_api.delete(exp["id"])


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S3-API-023 … 027  –  Recurring Expenses
# ═══════════════════════════════════════════════════════════════════════════════

class TestRecurringExpenses:

    @pytest.mark.positive
    def test_recurring_true_creates_recurring_config(
        self, admin_api, create_temp_building, create_temp_category
    ):
        """TC-S3-API-023: POST with is_recurring=true creates a recurring_config row."""
        expense_api = ExpenseAPI(admin_api)
        bld = create_temp_building(num_floors=3)
        cat = create_temp_category(building_id=bld["id"])

        resp = expense_api.create(**ExpenseFactory.recurring(bld["id"], cat["id"]))
        exp = resp.json()
        assert resp.status_code == 201

        detail = expense_api.get(exp["id"]).json()
        assert detail["recurring_config"] is not None
        assert detail["recurring_config"]["frequency"] == "monthly"

        expense_api.delete(exp["id"])

    @pytest.mark.positive
    def test_recurring_config_monthly_stores_next_due(
        self, admin_api, create_temp_building, create_temp_category
    ):
        """TC-S3-API-024: Monthly recurring config stores next_due_date one month ahead."""
        expense_api = ExpenseAPI(admin_api)
        bld = create_temp_building(num_floors=3)
        cat = create_temp_category(building_id=bld["id"])

        payload = ExpenseFactory.valid(bld["id"], cat["id"])
        payload["is_recurring"] = True
        payload["frequency"] = "monthly"
        expense_date = payload["expense_date"]

        exp = expense_api.create(**payload).json()
        detail = expense_api.get(exp["id"]).json()

        next_due = detail["recurring_config"]["next_due"]
        assert next_due is not None and len(next_due) == 10  # YYYY-MM-DD

        # next_due should be 1 month after expense_date
        from datetime import date
        from dateutil.relativedelta import relativedelta
        expected = (date.fromisoformat(expense_date) + relativedelta(months=1)).isoformat()
        assert next_due == expected

        expense_api.delete(exp["id"])

    @pytest.mark.positive
    def test_recurring_config_quarterly_stores_next_due(
        self, admin_api, create_temp_building, create_temp_category
    ):
        """TC-S3-API-025: Quarterly recurring config stores next_due 3 months ahead."""
        expense_api = ExpenseAPI(admin_api)
        bld = create_temp_building(num_floors=3)
        cat = create_temp_category(building_id=bld["id"])

        payload = ExpenseFactory.valid(bld["id"], cat["id"])
        payload["is_recurring"] = True
        payload["frequency"] = "quarterly"
        expense_date = payload["expense_date"]

        exp = expense_api.create(**payload).json()
        detail = expense_api.get(exp["id"]).json()

        from datetime import date
        from dateutil.relativedelta import relativedelta
        expected = (date.fromisoformat(expense_date) + relativedelta(months=3)).isoformat()
        assert detail["recurring_config"]["next_due"] == expected

        expense_api.delete(exp["id"])

    @pytest.mark.positive
    def test_recurring_expense_inherits_category_and_split(
        self, admin_api, create_temp_building, create_temp_category
    ):
        """TC-S3-API-027: Recurring expense inherits category and split type."""
        expense_api = ExpenseAPI(admin_api)
        bld = create_temp_building(num_floors=3)
        cat = create_temp_category(building_id=bld["id"])

        payload = ExpenseFactory.valid(bld["id"], cat["id"])
        payload["is_recurring"] = True
        payload["frequency"] = "annual"
        payload["split_type"] = "equal_all"

        exp = expense_api.create(**payload).json()
        assert exp["split_type"] == "equal_all"
        assert exp["category_id"] == cat["id"]

        expense_api.delete(exp["id"])

    @pytest.mark.positive
    def test_is_recurring_false_no_config_created(
        self, admin_api, create_temp_building, create_temp_category
    ):
        """TC-S3-API-026 (verify): Non-recurring expense has no recurring_config."""
        expense_api = ExpenseAPI(admin_api)
        bld = create_temp_building(num_floors=3)
        cat = create_temp_category(building_id=bld["id"])

        exp = expense_api.create(**ExpenseFactory.valid(bld["id"], cat["id"])).json()
        detail = expense_api.get(exp["id"]).json()
        assert detail.get("recurring_config") is None

        expense_api.delete(exp["id"])


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S3-API-028 … 033  –  File Upload
# ═══════════════════════════════════════════════════════════════════════════════

class TestFileUpload:

    def _get_temp_expense(self, admin_api, create_temp_building, create_temp_category):
        expense_api = ExpenseAPI(admin_api)
        bld = create_temp_building(num_floors=3)
        cat = create_temp_category(building_id=bld["id"])
        exp = expense_api.create(**ExpenseFactory.valid(bld["id"], cat["id"])).json()
        return expense_api, exp

    @pytest.mark.positive
    def test_upload_jpeg_returns_200_and_media_record(
        self, admin_api, create_temp_building, create_temp_category
    ):
        """TC-S3-API-028: POST /expenses/{id}/upload/ with JPEG returns 200 + media record."""
        expense_api, exp = self._get_temp_expense(
            admin_api, create_temp_building, create_temp_category
        )
        # Minimal 1×1 JPEG
        jpeg_bytes = (
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
            b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
            b"\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a"
            b"\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\x1e"
            b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00"
            b"\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01"
            b"\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b"
            b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xf5\x7f\xff\xd9"
        )
        resp = expense_api.upload(exp["id"], jpeg_bytes, "bill.jpg", "image/jpeg")
        assert resp.status_code == 200
        body = resp.json()
        assert "id" in body
        assert "url" in body
        assert body["mime_type"] == "image/jpeg"

        expense_api.delete(exp["id"])

    @pytest.mark.positive
    def test_upload_png_returns_200(
        self, admin_api, create_temp_building, create_temp_category
    ):
        """TC-S3-API-029: POST upload with PNG returns 200."""
        expense_api, exp = self._get_temp_expense(
            admin_api, create_temp_building, create_temp_category
        )
        # Minimal 1×1 PNG
        png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
            b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        resp = expense_api.upload(exp["id"], png_bytes, "bill.png", "image/png")
        assert resp.status_code == 200

        expense_api.delete(exp["id"])

    @pytest.mark.positive
    def test_upload_pdf_returns_200(
        self, admin_api, create_temp_building, create_temp_category
    ):
        """TC-S3-API-030: POST upload with PDF returns 200."""
        expense_api, exp = self._get_temp_expense(
            admin_api, create_temp_building, create_temp_category
        )
        # Minimal valid PDF
        pdf_bytes = b"%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 3 3]>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"
        resp = expense_api.upload(exp["id"], pdf_bytes, "bill.pdf", "application/pdf")
        assert resp.status_code == 200

        expense_api.delete(exp["id"])

    @pytest.mark.negative
    def test_upload_unsupported_type_returns_400(
        self, admin_api, create_temp_building, create_temp_category
    ):
        """TC-S3-API-031: POST upload with EXE file type returns 400."""
        expense_api, exp = self._get_temp_expense(
            admin_api, create_temp_building, create_temp_category
        )
        resp = expense_api.upload(exp["id"], b"MZfake_exe_content", "virus.exe", "application/x-msdownload")
        assert resp.status_code == 400

        expense_api.delete(exp["id"])

    @pytest.mark.negative
    def test_upload_too_large_returns_413(
        self, admin_api, create_temp_building, create_temp_category
    ):
        """TC-S3-API-032: POST upload with file > 10MB returns 413."""
        expense_api, exp = self._get_temp_expense(
            admin_api, create_temp_building, create_temp_category
        )
        # 11 MB of zeros (JPEG mime but oversized)
        large_file = b"\x00" * (11 * 1024 * 1024)
        resp = expense_api.upload(exp["id"], large_file, "huge.jpg", "image/jpeg")
        assert resp.status_code == 413

        expense_api.delete(exp["id"])

    @pytest.mark.positive
    def test_upload_response_contains_url(
        self, admin_api, create_temp_building, create_temp_category
    ):
        """TC-S3-API-033: Uploaded file URL is present in response."""
        expense_api, exp = self._get_temp_expense(
            admin_api, create_temp_building, create_temp_category
        )
        png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
            b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        resp = expense_api.upload(exp["id"], png_bytes, "receipt.png", "image/png")
        body = resp.json()
        assert "url" in body
        assert body["url"]  # non-empty

        expense_api.delete(exp["id"])


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S3-API-034 … 036  –  RBAC
# ═══════════════════════════════════════════════════════════════════════════════

class TestExpenseRBAC:

    @pytest.mark.positive
    def test_owner_can_get_building_expenses(
        self,
        admin_api,
        owner_with_id,
        create_temp_building,
        create_temp_category,
    ):
        """TC-S3-API-034: Owner can GET expenses for their building (200)."""
        owner_client, owner_id = owner_with_id
        bld = create_temp_building(num_floors=3)

        from api.building_api import BuildingAPI
        BuildingAPI(admin_api).assign_user(bld["id"], owner_id)

        cat = create_temp_category(building_id=bld["id"])
        expense_api_admin = ExpenseAPI(admin_api)
        exp = expense_api_admin.create(**ExpenseFactory.valid(bld["id"], cat["id"])).json()

        owner_expense_api = ExpenseAPI(owner_client)
        resp = owner_expense_api.list(building_id=bld["id"])
        assert resp.status_code == 200

        expense_api_admin.delete(exp["id"])

    @pytest.mark.negative
    def test_owner_cannot_post_expense(
        self, owner_api, create_temp_building, create_temp_category, admin_api
    ):
        """TC-S3-API-035: Owner cannot POST new expenses (403)."""
        bld = create_temp_building(num_floors=3)
        cat = create_temp_category(building_id=bld["id"])
        owner_expense_api = ExpenseAPI(owner_api)
        resp = owner_expense_api.create(**ExpenseFactory.valid(bld["id"], cat["id"]))
        assert resp.status_code == 403

    @pytest.mark.negative
    def test_owner_cannot_patch_expense(
        self,
        admin_api,
        owner_with_id,
        create_temp_building,
        create_temp_category,
    ):
        """TC-S3-API-036: Owner cannot PATCH existing expense (403)."""
        owner_client, owner_id = owner_with_id
        bld = create_temp_building(num_floors=3)

        from api.building_api import BuildingAPI
        BuildingAPI(admin_api).assign_user(bld["id"], owner_id)

        cat = create_temp_category(building_id=bld["id"])
        expense_api_admin = ExpenseAPI(admin_api)
        exp = expense_api_admin.create(**ExpenseFactory.valid(bld["id"], cat["id"])).json()

        owner_expense_api = ExpenseAPI(owner_client)
        resp = owner_expense_api.update(exp["id"], amount="999.00")
        assert resp.status_code == 403

        expense_api_admin.delete(exp["id"])


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S3-API-037 … 038  –  Categories
# ═══════════════════════════════════════════════════════════════════════════════

class TestExpenseCategories:

    @pytest.mark.positive
    def test_categories_are_building_scoped(
        self, admin_api, create_temp_building
    ):
        """TC-S3-API-037: GET /categories/?building_id= returns only that building's categories."""
        category_api = CategoryAPI(admin_api)
        bld1 = create_temp_building(num_floors=3)
        bld2 = create_temp_building(num_floors=3)

        cat1 = category_api.create(**CategoryFactory.valid(bld1["id"])).json()
        cat2 = category_api.create(**CategoryFactory.valid(bld2["id"])).json()

        resp = category_api.list(building_id=bld1["id"])
        ids = [c["id"] for c in (resp.json().get("results") or resp.json())]
        assert cat1["id"] in ids
        assert cat2["id"] not in ids

        category_api.delete(cat1["id"])
        category_api.delete(cat2["id"])

    @pytest.mark.positive
    def test_admin_can_create_custom_category(
        self, admin_api, create_temp_building
    ):
        """TC-S3-API-038: Admin can create custom expense category for a building."""
        category_api = CategoryAPI(admin_api)
        bld = create_temp_building(num_floors=3)

        resp = category_api.create(**CategoryFactory.valid(bld["id"], name="Maintenance"))
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "Maintenance"

        category_api.delete(body["id"])


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S3-API-039 … 040  –  Filtering
# ═══════════════════════════════════════════════════════════════════════════════

class TestExpenseFiltering:

    @pytest.mark.positive
    def test_filter_by_date_range(
        self, admin_api, create_temp_building, create_temp_category
    ):
        """TC-S3-API-039: Filter /expenses/?date_from=&date_to= returns correct range."""
        expense_api = ExpenseAPI(admin_api)
        bld = create_temp_building(num_floors=3)
        cat = create_temp_category(building_id=bld["id"])

        in_range_payload = ExpenseFactory.valid(bld["id"], cat["id"])
        in_range_payload["expense_date"] = "2026-01-15"
        out_range_payload = ExpenseFactory.valid(bld["id"], cat["id"])
        out_range_payload["expense_date"] = "2025-06-01"

        exp_in = expense_api.create(**in_range_payload).json()
        exp_out = expense_api.create(**out_range_payload).json()

        resp = expense_api.list(building_id=bld["id"], date_from="2026-01-01", date_to="2026-01-31")
        results = resp.json().get("results") or resp.json()
        ids = [e["id"] for e in results]
        assert exp_in["id"] in ids
        assert exp_out["id"] not in ids

        expense_api.delete(exp_in["id"])
        expense_api.delete(exp_out["id"])

    @pytest.mark.positive
    def test_filter_by_category(
        self, admin_api, create_temp_building, create_temp_category
    ):
        """TC-S3-API-040: Filter /expenses/?category_id= returns only matching expenses."""
        expense_api = ExpenseAPI(admin_api)
        bld = create_temp_building(num_floors=3)
        cat_a = create_temp_category(building_id=bld["id"])
        cat_b = create_temp_category(building_id=bld["id"])

        exp_a = expense_api.create(**ExpenseFactory.valid(bld["id"], cat_a["id"])).json()
        exp_b = expense_api.create(**ExpenseFactory.valid(bld["id"], cat_b["id"])).json()

        resp = expense_api.list(building_id=bld["id"], category_id=cat_a["id"])
        results = resp.json().get("results") or resp.json()
        ids = [e["id"] for e in results]
        assert exp_a["id"] in ids
        assert exp_b["id"] not in ids

        expense_api.delete(exp_a["id"])
        expense_api.delete(exp_b["id"])
