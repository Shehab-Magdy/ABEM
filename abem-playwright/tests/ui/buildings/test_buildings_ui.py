"""UI tests for buildings management page."""
import pytest
from pages.buildings_page import BuildingsPage
from utils.data_factory import unique_prefix
from config.settings import settings


@pytest.mark.ui
@pytest.mark.buildings
class TestBuildingsUI:
    def test_buildings_page_renders(self, admin_page):
        bp = BuildingsPage(admin_page)
        bp.navigate()
        bp.wait_for_load()
        assert bp.is_add_button_visible()

    def test_create_building_form(self, admin_page):
        bp = BuildingsPage(admin_page)
        bp.navigate()
        bp.wait_for_load()
        bp.click_add_building()
        name = f"{unique_prefix()} UI Building"
        bp.fill_building_form(name=name, address="123 Test St")
        bp.submit_building_form()
        admin_page.wait_for_timeout(2000)

    def test_owner_cannot_see_add_button(self, owner_page):
        owner_page.goto(f"{settings.BASE_URL}/buildings")
        owner_page.wait_for_timeout(3000)
        # Owner should be redirected or see no add button
        bp = BuildingsPage(owner_page)
        assert not bp.is_add_button_visible() or "/dashboard" in owner_page.url or "/403" in owner_page.url
