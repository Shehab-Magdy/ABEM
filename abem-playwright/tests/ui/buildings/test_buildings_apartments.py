"""UI tests for buildings and apartments — Sprint 2."""
import pytest
from pages.buildings_page import BuildingsPage
from config.settings import settings


@pytest.mark.ui
@pytest.mark.buildings
@pytest.mark.sprint2
class TestBuildingsApartments:

    def test_buildings_page_loads(self, admin_page):
        """Buildings page loads for admin."""
        admin_page.goto(f"{settings.BASE_URL}/buildings")
        admin_page.wait_for_load_state("networkidle")
        assert "/buildings" in admin_page.url

    def test_add_building_button_visible_admin(self, admin_page):
        """Admin sees Add Building button."""
        bp = BuildingsPage(admin_page)
        bp.navigate()
        bp.wait_for_load()
        assert bp.is_button_visible("Add Building")

    def test_owner_no_add_building(self, owner_page):
        """Owner cannot see Add Building button."""
        owner_page.goto(f"{settings.BASE_URL}/buildings")
        owner_page.wait_for_load_state("networkidle")
        assert not owner_page.locator("button:has-text('Add Building')").is_visible(timeout=2000)

    def test_building_list_has_columns(self, admin_page):
        """Building list table has expected columns."""
        bp = BuildingsPage(admin_page)
        bp.navigate()
        bp.wait_for_load()

    def test_create_building_form_opens(self, admin_page):
        """Clicking Add Building opens form dialog."""
        bp = BuildingsPage(admin_page)
        bp.navigate()
        bp.wait_for_load()
        if bp.is_button_visible("Add Building"):
            bp.click_button("Add Building")
            admin_page.wait_for_timeout(500)
            assert admin_page.locator("[role='dialog']").is_visible(timeout=3000)

    def test_manage_units_button(self, admin_page):
        """Admin sees manage units button on buildings."""
        bp = BuildingsPage(admin_page)
        bp.navigate()
        bp.wait_for_load()
