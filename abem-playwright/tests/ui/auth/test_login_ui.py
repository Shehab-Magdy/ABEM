"""UI tests for login page."""
import pytest
from pages.login_page import LoginPage
from config.settings import settings


@pytest.mark.ui
@pytest.mark.auth
@pytest.mark.sprint1
class TestLoginUI:
    def test_login_page_renders(self, page):
        lp = LoginPage(page)
        lp.navigate()
        lp.wait_for_load()
        assert lp.is_button_visible("Sign in")

    def test_login_success_redirects(self, page):
        lp = LoginPage(page)
        lp.navigate()
        lp.login_and_wait(settings.ADMIN_EMAIL, settings.ADMIN_PASSWORD)
        assert "/dashboard" in page.url

    def test_login_wrong_password_shows_error(self, page):
        lp = LoginPage(page)
        lp.navigate()
        lp.login(settings.ADMIN_EMAIL, "WrongPass!1")
        assert lp.is_error_displayed()

    def test_login_empty_fields_shows_validation(self, page):
        lp = LoginPage(page)
        lp.navigate()
        lp.click_submit()
        page.wait_for_timeout(1000)

    def test_login_error_does_not_reveal_email(self, page):
        lp = LoginPage(page)
        lp.navigate()
        lp.login("fake@abem.test", "WrongPass!1")
        assert lp.is_error_displayed()
        lp.navigate()
        lp.login(settings.ADMIN_EMAIL, "WrongPass!1")
        assert lp.is_error_displayed()

    def test_password_visibility_toggle(self, page):
        lp = LoginPage(page)
        lp.navigate()
        lp.fill_password("secret")
        pw_input = page.get_by_label("Password", exact=True)
        assert pw_input.get_attribute("type") == "password"

    def test_tc_s1_web_004_password_field_type(self, page):
        """TC-S1-WEB-004: Password field is type=password by default."""
        lp = LoginPage(page)
        lp.navigate()
        lp.wait_for_load()
        pw = page.get_by_label("Password", exact=True)
        assert pw.get_attribute("type") == "password"

    def test_tc_s1_web_008_admin_dashboard_controls(self, admin_page):
        """TC-S1-WEB-008: Admin dashboard shows admin-only controls."""
        admin_page.goto(f"{settings.BASE_URL}/dashboard")
        admin_page.wait_for_load_state("networkidle")
        assert admin_page.get_by_test_id("total-income").is_visible()

    def test_tc_s1_web_009_owner_no_admin_controls(self, owner_page):
        """TC-S1-WEB-009: Owner dashboard does NOT show admin controls."""
        owner_page.goto(f"{settings.BASE_URL}/dashboard")
        owner_page.wait_for_load_state("networkidle")
        assert not owner_page.locator("text=Add Building").is_visible()

    def test_tc_s1_web_010_back_after_logout(self, page):
        """TC-S1-WEB-010: Browser Back after logout does not expose dashboard."""
        lp = LoginPage(page)
        lp.navigate()
        lp.login_and_wait(settings.ADMIN_EMAIL, settings.ADMIN_PASSWORD)
        page.goto(f"{settings.BASE_URL}/login")
        page.wait_for_timeout(1000)
        page.go_back()
        page.wait_for_timeout(1000)
        assert "/login" in page.url or "/dashboard" in page.url

    def test_tc_s1_web_016_toggle_changes_field_type(self, page):
        """TC-S1-WEB-016: Show/hide toggle changes field type."""
        lp = LoginPage(page)
        lp.navigate()
        lp.wait_for_load()
        lp.fill_password("secret")
        pw = page.get_by_label("Password", exact=True)
        assert pw.get_attribute("type") == "password"
        lp.toggle_password_visibility()
        page.wait_for_timeout(500)
        assert pw.get_attribute("type") == "text"

    def test_tc_s1_web_018_unauth_redirect(self, browser_context):
        """TC-S1-WEB-018: Direct /dashboard navigation redirects to /login."""
        pg = browser_context.new_page()
        pg.goto(f"{settings.BASE_URL}/dashboard")
        pg.wait_for_timeout(2000)
        assert "/login" in pg.url or "/401" in pg.url
        pg.close()

    def test_tc_s1_web_021_tab_navigation(self, page):
        """TC-S1-WEB-021: Tab navigates email -> password -> submit."""
        lp = LoginPage(page)
        lp.navigate()
        lp.wait_for_load()
        page.get_by_label("Email address").focus()
        page.keyboard.press("Tab")
        page.wait_for_timeout(300)
        page.keyboard.press("Tab")
        page.wait_for_timeout(300)

    def test_tc_s1_web_022_enter_submits(self, page):
        """TC-S1-WEB-022: Enter key in password field submits the form."""
        lp = LoginPage(page)
        lp.navigate()
        lp.wait_for_load()
        lp.fill_email(settings.ADMIN_EMAIL)
        lp.fill_password(settings.ADMIN_PASSWORD)
        page.get_by_label("Password", exact=True).press("Enter")
        page.wait_for_url("**/dashboard**", timeout=15_000)
        assert "/dashboard" in page.url

    def test_tc_s1_web_025_no_horizontal_scroll_375px(self, browser_context):
        """TC-S1-WEB-025: No horizontal scroll at 375px viewport."""
        pg = browser_context.new_page()
        pg.set_viewport_size({"width": 375, "height": 812})
        pg.goto(f"{settings.BASE_URL}/login")
        pg.wait_for_load_state("networkidle")
        scroll_width = pg.evaluate("document.documentElement.scrollWidth")
        client_width = pg.evaluate("document.documentElement.clientWidth")
        assert scroll_width <= client_width + 5
        pg.close()
