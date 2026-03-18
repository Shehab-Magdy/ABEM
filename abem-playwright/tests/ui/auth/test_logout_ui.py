"""UI tests for logout flow."""
import pytest
from config.settings import settings


@pytest.mark.ui
@pytest.mark.auth
class TestLogoutUI:
    def test_logout_redirects_to_login(self, admin_page):
        admin_page.goto(f"{settings.BASE_URL}/dashboard")
        admin_page.wait_for_load_state("networkidle")
        # Click the Account icon button (Tooltip title="Account")
        admin_page.get_by_role("button", name="Account").click()
        admin_page.wait_for_timeout(500)
        # Click Sign Out menu item
        admin_page.locator(
            "[role='menuitem']:has-text('Sign Out'),"
            "li:has-text('Sign Out'),"
            "a:has-text('Sign Out')"
        ).first.click()
        admin_page.wait_for_url("**/login**", timeout=10_000)
        assert "/login" in admin_page.url

    def test_direct_url_without_auth_redirects(self, browser_context):
        page = browser_context.new_page()
        page.goto(f"{settings.BASE_URL}/dashboard")
        page.wait_for_timeout(3000)
        assert "/login" in page.url or "/401" in page.url
        page.close()
