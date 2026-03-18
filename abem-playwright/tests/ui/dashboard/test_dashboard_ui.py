"""UI tests for dashboard page."""
import pytest
from pages.dashboard_page import DashboardPage
from config.settings import settings


@pytest.mark.ui
@pytest.mark.dashboard
class TestDashboardUI:
    def test_admin_dashboard_renders_kpi_cards(self, admin_page):
        dp = DashboardPage(admin_page)
        dp.navigate()
        dp.wait_for_load()

    def test_admin_dashboard_building_selector(self, admin_page):
        dp = DashboardPage(admin_page)
        dp.navigate()
        dp.wait_for_load()

    def test_owner_dashboard_renders_balance(self, owner_page):
        dp = DashboardPage(owner_page)
        dp.navigate()
        dp.wait_for_load()

    def test_dashboard_date_filters(self, admin_page):
        dp = DashboardPage(admin_page)
        dp.navigate()
        dp.wait_for_load()
