"""UI tests for logout flow."""
import pytest
from config.settings import settings


@pytest.mark.ui
@pytest.mark.auth
class TestLogoutUI:
    def test_logout_redirects_to_login(self, admin_page):
        admin_page.goto(f"{settings.BASE_URL}/dashboard")
        admin_page.wait_for_load_state("networkidle")
        admin_page.get_by_role("link", name="Sign Out").or_(
            admin_page.locator("text=Sign Out")
        ).click()
        admin_page.wait_for_url("**/login**", timeout=10_000)
        assert "/login" in admin_page.url

    def test_direct_url_without_auth_redirects(self, browser_context):
        page = browser_context.new_page()
        page.goto(f"{settings.BASE_URL}/dashboard")
        page.wait_for_timeout(3000)
        assert "/login" in page.url or "/401" in page.url
        page.close()
