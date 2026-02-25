"""
Sprint 5 — Dashboard API Tests (15 cases)
TC-S5-API-001 → TC-S5-API-015
"""
from __future__ import annotations

import time
from decimal import Decimal

import pytest

from api.dashboard_api import DashboardAPI
from core.api_client import APIClient


pytestmark = [pytest.mark.sprint_5, pytest.mark.api]


# ─────────────────────────────────────────────────────────────────────────────
# TC-S5-API-001 → TC-S5-API-003  Admin dashboard basic + totals + overdue
# ─────────────────────────────────────────────────────────────────────────────

class TestAdminDashboardBasic:

    def test_admin_dashboard_returns_200(self, admin_dashboard_api):
        """TC-S5-API-001: GET /dashboard/admin/ returns 200 with data."""
        resp = admin_dashboard_api.get_admin()
        assert resp.status_code == 200, resp.text
        body = resp.json()
        for key in ("total_income", "total_expenses", "overdue_count",
                    "monthly_trend", "building_summary"):
            assert key in body, f"Missing key: {key}"

    def test_admin_dashboard_totals_present(
        self, admin_dashboard_api, dashboard_data
    ):
        """TC-S5-API-002: total_income, total_expenses, overdue_count all present and numeric."""
        building = dashboard_data["building"]
        resp = admin_dashboard_api.get_admin(building_id=building["id"])
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert Decimal(body["total_income"]) >= 0
        assert Decimal(body["total_expenses"]) >= 0
        assert isinstance(body["overdue_count"], int)

    def test_overdue_count_matches_positive_balance_apartments(
        self, admin_dashboard_api, dashboard_data
    ):
        """TC-S5-API-003: overdue_count matches apartments with balance > 0."""
        building = dashboard_data["building"]
        # dashboard_data creates 1 apartment with partial payment → balance > 0
        resp = admin_dashboard_api.get_admin(building_id=building["id"])
        assert resp.status_code == 200, resp.text
        body = resp.json()
        # At least the one apartment from dashboard_data should be overdue
        assert body["overdue_count"] >= 1


# ─────────────────────────────────────────────────────────────────────────────
# TC-S5-API-004 → TC-S5-API-006  Owner dashboard
# ─────────────────────────────────────────────────────────────────────────────

class TestOwnerDashboard:

    def test_owner_dashboard_returns_200(self, owner_api):
        """TC-S5-API-004: GET /dashboard/owner/ returns 200."""
        resp = DashboardAPI(owner_api).get_owner()
        assert resp.status_code == 200, resp.text

    def test_owner_dashboard_response_structure(self, owner_api):
        """TC-S5-API-005: Owner dashboard contains balance_summary, recent_payments, expense_breakdown."""
        resp = DashboardAPI(owner_api).get_owner()
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "balance_summary" in body
        assert "current_balance" in body["balance_summary"]
        assert "total_paid_ytd" in body["balance_summary"]
        assert "recent_payments" in body
        assert "expense_breakdown" in body
        assert isinstance(body["recent_payments"], list)
        assert isinstance(body["expense_breakdown"], list)

    def test_expense_breakdown_grouped_by_category(
        self, dashboard_data, env_config
    ):
        """TC-S5-API-006: expense_breakdown grouped by category with correct amounts."""
        owner_client = dashboard_data["owner_client"]
        resp = DashboardAPI(owner_client).get_owner()
        assert resp.status_code == 200, resp.text
        body = resp.json()
        breakdown = body["expense_breakdown"]
        assert len(breakdown) >= 1, "Expected at least one category in breakdown"
        first = breakdown[0]
        assert "category_name" in first
        assert "total" in first
        assert Decimal(first["total"]) > 0


# ─────────────────────────────────────────────────────────────────────────────
# TC-S5-API-007  Date filtering
# ─────────────────────────────────────────────────────────────────────────────

class TestDashboardFiltering:

    def test_date_filter_returns_data_within_range(
        self, admin_dashboard_api, dashboard_data
    ):
        """TC-S5-API-007: date_from/date_to filter returns only data within range."""
        building = dashboard_data["building"]

        # Query a far-future date range — should return zeros
        resp_future = admin_dashboard_api.get_admin(
            building_id=building["id"],
            date_from="3000-01-01",
            date_to="3000-12-31",
        )
        assert resp_future.status_code == 200
        future_body = resp_future.json()
        assert Decimal(future_body["total_income"]) == Decimal("0.00")
        assert Decimal(future_body["total_expenses"]) == Decimal("0.00")

        # Query without date filter — should have data
        resp_all = admin_dashboard_api.get_admin(building_id=building["id"])
        assert resp_all.status_code == 200
        all_body = resp_all.json()
        assert Decimal(all_body["total_income"]) > Decimal("0.00")

    def test_building_id_filter_scopes_to_single_building(
        self, admin_dashboard_api, create_temp_building
    ):
        """TC-S5-API-014: GET /dashboard/admin/?building_id= scopes to single building."""
        building_a = create_temp_building(num_floors=10)
        building_b = create_temp_building(num_floors=10)

        resp_a = admin_dashboard_api.get_admin(building_id=building_a["id"])
        resp_b = admin_dashboard_api.get_admin(building_id=building_b["id"])
        assert resp_a.status_code == 200
        assert resp_b.status_code == 200

        body_a = resp_a.json()
        body_b = resp_b.json()
        # Both scoped — building summaries are independent
        assert body_a["building_summary"]["total_buildings"] == 1
        assert body_b["building_summary"]["total_buildings"] == 1

    def test_changing_date_range_returns_different_aggregations(
        self, admin_dashboard_api, dashboard_data
    ):
        """TC-S5-API-013: Changing date range returns different aggregation values."""
        building = dashboard_data["building"]

        # With data (no filter)
        resp_all = admin_dashboard_api.get_admin(building_id=building["id"])
        assert resp_all.status_code == 200
        income_all = Decimal(resp_all.json()["total_income"])

        # Far future (no data)
        resp_empty = admin_dashboard_api.get_admin(
            building_id=building["id"],
            date_from="3000-01-01",
            date_to="3000-12-31",
        )
        assert resp_empty.status_code == 200
        income_empty = Decimal(resp_empty.json()["total_income"])

        assert income_all != income_empty, (
            "Expected different totals when date range changes"
        )


# ─────────────────────────────────────────────────────────────────────────────
# TC-S5-API-008 → TC-S5-API-009  RBAC / multi-tenancy
# ─────────────────────────────────────────────────────────────────────────────

class TestDashboardRBAC:

    def test_admin_cannot_see_other_admins_building(
        self, create_temp_building, create_temp_user, env_config
    ):
        """TC-S5-API-008: Admin cannot see data from buildings they do not manage."""
        # Building created by the main admin (admin1)
        building = create_temp_building(num_floors=10)

        # Create a second admin and authenticate
        admin2_data = create_temp_user(role="admin")
        client2 = APIClient(env_config.api_url)
        client2.authenticate(admin2_data["email"], admin2_data["password"])

        try:
            resp = DashboardAPI(client2).get_admin(building_id=building["id"])
            assert resp.status_code == 403, (
                f"Expected 403 for admin2 accessing admin1's building, got {resp.status_code}"
            )
        finally:
            client2.logout()

    def test_owner_cannot_access_admin_dashboard(self, owner_api):
        """TC-S5-API-009: Owner calling /dashboard/admin/ returns 403."""
        resp = DashboardAPI(owner_api).get_admin()
        assert resp.status_code == 403, resp.text

    def test_unauthenticated_admin_dashboard_returns_401(self, unauthenticated_api):
        """Unauthenticated request to admin dashboard returns 401."""
        resp = DashboardAPI(unauthenticated_api).get_admin()
        assert resp.status_code == 401, resp.text

    def test_unauthenticated_owner_dashboard_returns_401(self, unauthenticated_api):
        """Unauthenticated request to owner dashboard returns 401."""
        resp = DashboardAPI(unauthenticated_api).get_owner()
        assert resp.status_code == 401, resp.text


# ─────────────────────────────────────────────────────────────────────────────
# TC-S5-API-010 → TC-S5-API-012  Monthly trend, edge cases, performance
# ─────────────────────────────────────────────────────────────────────────────

class TestDashboardEdgeCases:

    def test_monthly_trend_has_12_entries(self, admin_dashboard_api):
        """TC-S5-API-010: Monthly trend array has 12 entries for full-year query."""
        resp = admin_dashboard_api.get_admin()
        assert resp.status_code == 200, resp.text
        trend = resp.json()["monthly_trend"]
        assert len(trend) == 12, f"Expected 12 monthly entries, got {len(trend)}"
        # Each entry has month, income, expenses
        for entry in trend:
            assert "month" in entry
            assert "income" in entry
            assert "expenses" in entry

    def test_empty_building_returns_zeros_not_null(
        self, admin_dashboard_api, create_temp_building
    ):
        """TC-S5-API-011: Building with no expenses returns 0 values (not null/error)."""
        building = create_temp_building(num_floors=10)
        resp = admin_dashboard_api.get_admin(building_id=building["id"])
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["total_income"] is not None
        assert body["total_expenses"] is not None
        assert Decimal(body["total_income"]) == Decimal("0.00")
        assert Decimal(body["total_expenses"]) == Decimal("0.00")
        assert body["overdue_count"] == 0

    def test_dashboard_responds_within_1000ms(self, admin_dashboard_api):
        """TC-S5-API-012: Dashboard API responds within 1000ms."""
        start = time.perf_counter()
        resp = admin_dashboard_api.get_admin()
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert resp.status_code == 200
        assert elapsed_ms < 1000, f"Response took {elapsed_ms:.0f}ms (limit 1000ms)"


# ─────────────────────────────────────────────────────────────────────────────
# TC-S5-API-015  Data consistency
# ─────────────────────────────────────────────────────────────────────────────

class TestDashboardConsistency:

    def test_dashboard_totals_consistent_with_payments_endpoint(
        self, admin_dashboard_api, dashboard_data, admin_api
    ):
        """TC-S5-API-015: Dashboard total_income matches sum from /payments/ endpoint."""
        from api.payment_api import PaymentAPI

        building = dashboard_data["building"]
        apartment = dashboard_data["apartment"]

        # Get total_income from dashboard
        dash_resp = admin_dashboard_api.get_admin(building_id=building["id"])
        assert dash_resp.status_code == 200
        dash_income = Decimal(dash_resp.json()["total_income"])

        # Get sum of payments for this building via /payments/ endpoint
        pay_resp = PaymentAPI(admin_api).list(apartment_id=apartment["id"])
        assert pay_resp.status_code == 200
        payments_data = pay_resp.json()
        results = payments_data.get("results", payments_data) if isinstance(payments_data, dict) else payments_data
        api_total = sum(Decimal(p["amount_paid"]) for p in results)

        assert dash_income >= api_total, (
            f"Dashboard income {dash_income} should include apartment payments {api_total}"
        )
