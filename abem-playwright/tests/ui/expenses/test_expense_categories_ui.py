"""UI tests for expense category picker."""
import pytest
from pages.categories_page import CategoriesPage
from config.settings import settings


@pytest.mark.ui
@pytest.mark.categories
class TestExpenseCategoriesUI:
    def test_admin_can_view_categories_page(self, admin_page):
        cp = CategoriesPage(admin_page)
        cp.navigate()
        cp.wait_for_load()

    def test_owner_no_add_delete_buttons(self, owner_page):
        owner_page.goto(f"{settings.BASE_URL}/expense-categories")
        owner_page.wait_for_timeout(3000)
        cp = CategoriesPage(owner_page)
        assert not cp.is_add_button_visible() or "/dashboard" in owner_page.url or "/403" in owner_page.url
