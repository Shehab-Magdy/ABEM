"""E2E Journey 3: Owner read-only view cycle."""
import pytest
from pages.expenses_page import ExpensesPage
from pages.dashboard_page import DashboardPage
from utils.data_factory import build_building, build_expense, build_payment
from config.settings import settings


@pytest.mark.e2e
class TestOwnerBalanceViewCycle:

    def test_owner_readonly(self, admin_api, owner_api, owner_page):
        # Owner can view dashboard
        dp = DashboardPage(owner_page)
        dp.navigate()
        dp.wait_for_load()

        # Owner expense page has no add button
        ep = ExpensesPage(owner_page)
        ep.navigate()
        ep.wait_for_load()
        assert not ep.is_add_button_visible()

        # Owner API POST /expenses/ gets 403
        resp = owner_api.post("/api/v1/expenses/", data={"title": "blocked"})
        assert resp.status == 403
