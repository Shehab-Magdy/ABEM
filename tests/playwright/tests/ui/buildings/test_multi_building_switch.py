"""UI tests for multi-building context switching."""
import pytest
from pages.expenses_page import ExpensesPage
from config.settings import settings


@pytest.mark.ui
@pytest.mark.buildings
class TestMultiBuildingSwitch:
    def test_building_selector_visible_on_expenses(self, admin_page):
        ep = ExpensesPage(admin_page)
        ep.navigate()
        ep.wait_for_load()
        # Building selector may be a Select, FormControl, or dropdown
        selector = admin_page.get_by_label("Building", exact=False).or_(
            admin_page.locator("[data-testid='building-selector']")
        ).or_(
            admin_page.locator("select, [role='combobox']").first
        )
        assert selector.count() > 0
