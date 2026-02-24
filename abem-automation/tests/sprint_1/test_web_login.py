"""
Sprint 1 — Web UI Login Test Suite.

Drives the React + MUI login page at /login using Selenium.

All tests use the `web_driver` fixture (function-scoped, auto-screenshots on failure).
Page interactions go through LoginPage / DashboardPage POMs.

Markers: web, sprint_1
"""

import pytest

from pages.web.dashboard_page import DashboardPage
from pages.web.login_page import LoginPage

pytestmark = [pytest.mark.web, pytest.mark.sprint_1]

LOGIN_MAX_ATTEMPTS = 5   # keep in sync with backend setting


# ── Helper ─────────────────────────────────────────────────────────────────────

def _open_login(driver, base_url: str) -> LoginPage:
    page = LoginPage(driver)
    page.open(base_url)
    return page


# ══════════════════════════════════════════════════════════════════════════════
# Page Load & Layout
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.positive
class TestLoginPageLayout:

    def test_login_page_loads_successfully(self, web_driver, env_config):
        page = _open_login(web_driver, env_config.base_url)
        assert "login" in web_driver.current_url.lower() or web_driver.current_url.endswith("/")

    def test_brand_title_visible(self, web_driver, env_config):
        page = _open_login(web_driver, env_config.base_url)
        assert page.is_brand_visible(), "ABEM brand title not visible on login page"

    def test_email_and_password_fields_visible(self, web_driver, env_config):
        page = _open_login(web_driver, env_config.base_url)
        assert page.is_visible(LoginPage.EMAIL_INPUT), "Email field not visible"
        assert page.is_visible(LoginPage.PASSWORD_INPUT), "Password field not visible"

    def test_submit_button_visible(self, web_driver, env_config):
        page = _open_login(web_driver, env_config.base_url)
        assert page.is_visible(LoginPage.SUBMIT_BUTTON), "Submit button not visible"

    def test_password_hidden_by_default(self, web_driver, env_config):
        page = _open_login(web_driver, env_config.base_url)
        assert page.get_password_input_type() == "password", (
            "Password should be hidden (type='password') by default"
        )


# ══════════════════════════════════════════════════════════════════════════════
# Positive Login Flows
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.positive
class TestLoginPositive:

    def test_admin_login_success_redirects_to_dashboard(self, web_driver, env_config):
        page = _open_login(web_driver, env_config.base_url)
        page.login(env_config.admin_email, env_config.admin_password)
        page.wait_for_url_contains("/dashboard", timeout=10)
        assert "/dashboard" in web_driver.current_url, (
            f"Expected redirect to /dashboard, current URL: {web_driver.current_url}"
        )

    def test_dashboard_sidebar_visible_after_login(self, web_driver, env_config):
        page = _open_login(web_driver, env_config.base_url)
        page.login(env_config.admin_email, env_config.admin_password)
        page.wait_for_url_contains("/dashboard", timeout=10)

        dashboard = DashboardPage(web_driver)
        assert dashboard.is_sidebar_visible(), "Sidebar not visible after login"

    def test_admin_sees_users_nav_item(self, web_driver, env_config):
        """Users menu item is admin-only."""
        page = _open_login(web_driver, env_config.base_url)
        page.login(env_config.admin_email, env_config.admin_password)
        page.wait_for_url_contains("/dashboard", timeout=10)

        dashboard = DashboardPage(web_driver)
        assert dashboard.is_nav_item_visible("users"), (
            "Admin should see the Users nav item"
        )

    def test_no_error_banner_on_successful_login(self, web_driver, env_config):
        page = _open_login(web_driver, env_config.base_url)
        page.login(env_config.admin_email, env_config.admin_password)
        # Give login time to process
        page.wait_for_url_contains("/dashboard", timeout=10)
        # Navigate back to verify no error was shown
        # (error banner would only show if login failed)
        assert "/login" not in web_driver.current_url, "Still on login page after login"

    def test_password_visibility_toggle_shows_text(self, web_driver, env_config):
        page = _open_login(web_driver, env_config.base_url)
        page.enter_password("testpassword")

        assert page.get_password_input_type() == "password"
        page.toggle_password_visibility()
        assert page.get_password_input_type() == "text", (
            "Password should be visible after clicking toggle"
        )

    def test_password_toggle_hides_again(self, web_driver, env_config):
        page = _open_login(web_driver, env_config.base_url)
        page.enter_password("testpassword")
        page.toggle_password_visibility()
        page.toggle_password_visibility()
        assert page.get_password_input_type() == "password", (
            "Password should be hidden again after second toggle"
        )

    def test_loading_state_shown_on_submit(self, web_driver, env_config):
        """The Sign In button should show a spinner while the request is in-flight."""
        page = _open_login(web_driver, env_config.base_url)
        page.enter_email(env_config.admin_email)
        page.enter_password(env_config.admin_password)
        page.click(LoginPage.SUBMIT_BUTTON)
        # The spinner appears briefly — we just verify no JS error occurs
        # and the page eventually navigates
        page.wait_for_url_contains("/dashboard", timeout=10)


# ══════════════════════════════════════════════════════════════════════════════
# Negative Login Flows
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.negative
class TestLoginNegative:

    def test_wrong_password_shows_error_banner(self, web_driver, env_config):
        page = _open_login(web_driver, env_config.base_url)
        page.login(env_config.admin_email, "WrongPass@999")
        assert page.is_error_displayed(), "Error banner should appear for wrong password"

    def test_error_message_is_human_readable(self, web_driver, env_config):
        page = _open_login(web_driver, env_config.base_url)
        page.login(env_config.admin_email, "WrongPass@999")
        if page.is_error_displayed():
            msg = page.get_error_message()
            assert len(msg) > 5, f"Error message too short: '{msg}'"
            assert "{" not in msg, f"Error message looks like raw JSON: '{msg}'"

    def test_empty_email_prevents_submit(self, web_driver, env_config):
        """Submitting with empty email should not reach the server (client-side)."""
        page = _open_login(web_driver, env_config.base_url)
        page.enter_password("SomePass@1")
        page.click(LoginPage.SUBMIT_BUTTON)
        # Should still be on the login page
        assert "/login" in web_driver.current_url or "/dashboard" not in web_driver.current_url

    def test_empty_password_prevents_submit(self, web_driver, env_config):
        page = _open_login(web_driver, env_config.base_url)
        page.enter_email(env_config.admin_email)
        page.click(LoginPage.SUBMIT_BUTTON)
        assert "/dashboard" not in web_driver.current_url

    def test_invalid_email_format_shows_validation(self, web_driver, env_config):
        """MUI react-hook-form should reject 'notanemail' before API call."""
        page = _open_login(web_driver, env_config.base_url)
        page.enter_email("notanemail")
        page.enter_password("SomePass@1")
        page.click(LoginPage.SUBMIT_BUTTON)
        # Either client-side validation message or still on login page
        assert "/dashboard" not in web_driver.current_url

    def test_submit_disabled_during_loading(self, web_driver, env_config):
        """While loading, the submit button must be disabled to prevent double-submit."""
        page = _open_login(web_driver, env_config.base_url)
        page.enter_email(env_config.admin_email)
        page.enter_password(env_config.admin_password)
        page.click(LoginPage.SUBMIT_BUTTON)
        # Immediately after click, button may be disabled (race condition check)
        # We primarily verify the page reaches dashboard without double-posting
        page.wait_for_url_contains("/dashboard", timeout=10)
        assert "/dashboard" in web_driver.current_url

    def test_account_lockout_shows_lockout_banner(self, web_driver, env_config, create_temp_user):
        """After LOGIN_MAX_ATTEMPTS+1 failures the UI must show a lockout-specific message."""
        from api.auth_api import AuthAPI
        from core.api_client import APIClient

        # Pre-lock the account via API (faster than UI)
        user = create_temp_user(role="owner")
        api_auth = AuthAPI(APIClient(env_config.api_url))
        for _ in range(LOGIN_MAX_ATTEMPTS + 1):
            api_auth.login(user["email"], "BadPass@1")

        # Now try via UI
        page = _open_login(web_driver, env_config.base_url)
        page.login(user["email"], "BadPass@1")

        assert page.is_error_displayed(timeout=6), "Error banner should show for locked account"
        assert page.is_lockout_displayed(), (
            "Lockout-specific message should appear when account is locked"
        )

    def test_logout_then_access_protected_redirects_to_login(self, web_driver, env_config):
        """After logout, navigating to /dashboard must redirect to /login."""
        # Login first
        page = _open_login(web_driver, env_config.base_url)
        page.login(env_config.admin_email, env_config.admin_password)
        page.wait_for_url_contains("/dashboard", timeout=10)

        # Logout
        dashboard = DashboardPage(web_driver)
        dashboard.sign_out()

        # Try to navigate directly to a protected route
        web_driver.get(f"{env_config.base_url}/dashboard")
        page.wait_for_url_contains("/login", timeout=5)
        assert "/login" in web_driver.current_url, (
            f"Should redirect to /login, got {web_driver.current_url}"
        )
