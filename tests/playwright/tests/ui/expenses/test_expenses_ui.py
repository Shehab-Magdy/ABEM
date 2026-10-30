"""UI tests for expenses management page."""
import pytest
from pages.expenses_page import ExpensesPage
from config.settings import settings


@pytest.mark.ui
@pytest.mark.expenses
class TestExpensesUI:
    def test_expenses_page_renders(self, admin_page):
        ep = ExpensesPage(admin_page)
        ep.navigate()
        ep.wait_for_load()
        assert ep.is_add_button_visible()

    def test_owner_no_add_button(self, owner_page):
        ep = ExpensesPage(owner_page)
        ep.navigate()
        ep.wait_for_load()
        assert not ep.is_add_button_visible()
