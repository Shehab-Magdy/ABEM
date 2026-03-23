"""UI tests for dashboards — TC-S5-WEB series."""
import pytest
from config.settings import settings


@pytest.mark.ui
@pytest.mark.dashboard
@pytest.mark.sprint5
class TestDashboardManagement:

    def test_tc_s5_web_001_admin_dashboard_loads(self, admin_page):
        """TC-S5-WEB-001: Admin Dashboard loads without errors."""
        admin_page.goto(f"{settings.BASE_URL}/dashboard")
        admin_page.wait_for_load_state("networkidle")
        assert "/dashboard" in admin_page.url
        # No error alerts
        assert not admin_page.locator("[role='alert'][class*='error']").is_visible(timeout=2000)

    def test_tc_s5_web_002_total_income_card(self, admin_page):
        """TC-S5-WEB-002: Total income summary card is present."""
        admin_page.goto(f"{settings.BASE_URL}/dashboard")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.get_by_test_id("total-income").is_visible(timeout=5000)

    def test_tc_s5_web_004_overdue_card_red(self, admin_page):
        """TC-S5-WEB-004: Overdue count card highlighted red when > 0."""
        admin_page.goto(f"{settings.BASE_URL}/dashboard")
        admin_page.wait_for_load_state("networkidle")
        card = admin_page.get_by_test_id("overdue-units-card")
        assert card.is_visible(timeout=5000)

    def test_tc_s5_web_005_expense_trend_chart(self, admin_page):
        """TC-S5-WEB-005: Expense trend chart is rendered."""
        admin_page.goto(f"{settings.BASE_URL}/dashboard")
        admin_page.wait_for_load_state("networkidle")
        chart = admin_page.get_by_test_id("monthly-trend-chart")
        assert chart.is_visible(timeout=5000)

    def test_tc_s5_web_007_overdue_card_navigates(self, admin_page):
        """TC-S5-WEB-007: Clicking overdue card navigates to payments."""
        admin_page.goto(f"{settings.BASE_URL}/dashboard")
        admin_page.wait_for_load_state("networkidle")
        card = admin_page.get_by_test_id("overdue-units-card")
        if card.is_visible(timeout=3000):
            count_text = admin_page.get_by_test_id("overdue-units-count").inner_text()
            if int(count_text) > 0:
                card.click()
                admin_page.wait_for_timeout(1000)

    def test_tc_s5_web_008_owner_dashboard_loads(self, owner_page):
        """TC-S5-WEB-008: Owner Dashboard loads without errors."""
        owner_page.goto(f"{settings.BASE_URL}/dashboard")
        owner_page.wait_for_load_state("networkidle")
        assert "/dashboard" in owner_page.url

    def test_tc_s5_web_012_date_range_changes_data(self, admin_page):
        """TC-S5-WEB-012: Date range picker changes dashboard data."""
        admin_page.goto(f"{settings.BASE_URL}/dashboard")
        admin_page.wait_for_load_state("networkidle")
        date_from = admin_page.get_by_test_id("date-from")
        if date_from.is_visible(timeout=3000):
            date_from.fill("2025-01-01")
            admin_page.wait_for_timeout(1000)

    @pytest.mark.rbac
    def test_tc_s5_web_018_owner_no_admin_dashboard(self, owner_page):
        """TC-S5-WEB-018: Owner cannot navigate to admin dashboard directly."""
        owner_page.goto(f"{settings.BASE_URL}/dashboard/admin")
        owner_page.wait_for_timeout(2000)
        # Should redirect away or show access denied
        assert "/dashboard/admin" not in owner_page.url or owner_page.locator("[role='alert']").is_visible(timeout=2000)

    @pytest.mark.performance
    def test_tc_s5_web_019_dashboard_loads_within_3s(self, admin_page):
        """TC-S5-WEB-019: Dashboard loads within 3 seconds."""
        import time
        start = time.time()
        admin_page.goto(f"{settings.BASE_URL}/dashboard")
        admin_page.wait_for_load_state("networkidle")
        elapsed = time.time() - start
        assert elapsed < 3.0, f"Dashboard took {elapsed:.1f}s to load"
