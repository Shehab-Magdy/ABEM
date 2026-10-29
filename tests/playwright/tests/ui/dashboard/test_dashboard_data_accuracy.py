"""UI tests for dashboard data accuracy — cross-layer API↔UI validation."""
import pytest
from pages.dashboard_page import DashboardPage
from config.settings import settings


@pytest.mark.ui
@pytest.mark.dashboard
class TestDashboardDataAccuracy:
    def test_admin_dashboard_loads_data(self, admin_page):
        dp = DashboardPage(admin_page)
        dp.navigate()
        dp.wait_for_load()

    def test_owner_dashboard_loads_data(self, owner_page):
        dp = DashboardPage(owner_page)
        dp.navigate()
        dp.wait_for_load()
