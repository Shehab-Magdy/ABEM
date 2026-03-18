"""Login page object model."""

from __future__ import annotations

from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class LoginPage(BasePage):
    URL = "/login"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._email_input = page.get_by_label("Email address")
        self._password_input = page.get_by_label("Password", exact=True)
        self._submit_btn = page.get_by_role("button", name="Sign in")

    # ── Navigation ────────────────────────────────────────────

    def wait_for_load(self) -> None:
        self._submit_btn.wait_for(state="visible", timeout=10_000)

    # ── Actions ───────────────────────────────────────────────

    def fill_email(self, email: str) -> None:
        self._email_input.fill(email)

    def fill_password(self, password: str) -> None:
        self._password_input.fill(password)

    def click_submit(self) -> None:
        self._submit_btn.click()

    def login(self, email: str, password: str) -> None:
        """Fill credentials and click submit."""
        self.fill_email(email)
        self.fill_password(password)
        self.click_submit()

    def login_and_wait(self, email: str, password: str) -> None:
        """Login and wait for redirect to dashboard."""
        self.login(email, password)
        self._page.wait_for_url("**/dashboard**", timeout=15_000)

    def toggle_password_visibility(self) -> None:
        """Click the show/hide password toggle."""
        self._page.locator("[aria-label*='password'], button:has(svg)").first.click()

    # ── State readers ─────────────────────────────────────────

    def get_error_message(self) -> str:
        """Return the login error message text."""
        alert = self._page.locator("[role='alert']").first
        alert.wait_for(state="visible", timeout=5_000)
        return alert.inner_text()

    def is_error_displayed(self) -> bool:
        """Check if an error alert is visible."""
        try:
            self._page.locator("[role='alert']").first.wait_for(
                state="visible", timeout=3_000
            )
            return True
        except Exception:
            return False

    def is_submit_enabled(self) -> bool:
        """Check if the Sign in button is enabled."""
        return self._submit_btn.is_enabled()

    def has_email_validation_error(self) -> bool:
        """Check if the email field shows a validation error."""
        return self._page.locator("#email-helper-text, [id*='email'][class*='error']").is_visible()

    def has_password_validation_error(self) -> bool:
        """Check if the password field shows a validation error."""
        return self._page.locator("#password-helper-text, [id*='password'][class*='error']").is_visible()
