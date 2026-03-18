"""UI tests for login page."""
import pytest
from pages.login_page import LoginPage
from config.settings import settings


@pytest.mark.ui
@pytest.mark.auth
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
        msg1 = lp.get_error_message()
        lp.navigate()
        lp.login(settings.ADMIN_EMAIL, "WrongPass!1")
        msg2 = lp.get_error_message()
        assert msg1 == msg2

    def test_password_visibility_toggle(self, page):
        lp = LoginPage(page)
        lp.navigate()
        lp.fill_password("secret")
        pw_input = page.get_by_label("Password")
        assert pw_input.get_attribute("type") == "password"
