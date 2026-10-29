"""UI tests for profile page."""
import pytest
from pages.profile_page import ProfilePage
from config.settings import settings


@pytest.mark.ui
class TestProfileUI:
    def test_profile_page_renders(self, admin_page):
        pp = ProfilePage(admin_page)
        pp.navigate()
        pp.wait_for_load()

    def test_edit_profile_name(self, admin_page):
        pp = ProfilePage(admin_page)
        pp.navigate()
        pp.wait_for_load()
