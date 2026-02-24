"""
Page Object for the ABEM Web Login screen (/login).

Selectors target the React + MUI v6 DOM structure produced by
frontend/src/pages/auth/LoginPage.jsx.

Recommendation: add data-testid attributes to the React components
for more resilient selectors:
    <input data-testid="email-input" />
    <input data-testid="password-input" />
    <button data-testid="sign-in-btn" />
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from pages.web.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class LoginPage(BasePage):
    """Interactions with the /login page."""

    # ── Locators ───────────────────────────────────────────────────────────────
    # MUI TextField renders the native <input> inside a wrapper div.
    EMAIL_INPUT       = (By.CSS_SELECTOR, "input[type='email'], input[name='email']")
    PASSWORD_INPUT    = (By.CSS_SELECTOR, "input[type='password'], input[name='password']")
    SHOW_PWD_TOGGLE   = (By.XPATH, "//button[.//input[@type='checkbox']] | //button[@aria-label='toggle password visibility'] | //input[@type='password']/ancestor::div[contains(@class,'MuiInputBase')]//button")
    SUBMIT_BUTTON     = (By.XPATH, "//button[@type='submit' or (contains(@class,'MuiButton') and contains(.,'Sign In'))]")

    # Error / lockout banner  (MUI Alert or custom Container)
    ERROR_BANNER      = (By.CSS_SELECTOR, ".MuiAlert-root, [data-testid='error-banner']")
    ERROR_MESSAGE     = (By.CSS_SELECTOR, ".MuiAlert-message, [data-testid='error-message']")
    LOCKOUT_BANNER    = (By.CSS_SELECTOR, ".MuiAlert-root[severity='error'], [data-testid='lockout-banner']")

    # Loading indicator while form is submitting
    LOADING_SPINNER   = (By.CSS_SELECTOR, ".MuiCircularProgress-root")

    # Brand text
    BRAND_TITLE       = (By.XPATH, "//h4[contains(.,'ABEM')] | //h5[contains(.,'ABEM')]")
    BRAND_SUBTITLE    = (By.XPATH, "//*[contains(.,'Apartment') and contains(.,'Expense')]")

    # ── Navigation ─────────────────────────────────────────────────────────────

    def open(self, base_url: str) -> "LoginPage":
        super().open(f"{base_url.rstrip('/')}/login")
        self.wait_until_visible(self.EMAIL_INPUT)
        logger.info("Login page opened")
        return self

    # ── Actions ────────────────────────────────────────────────────────────────

    def enter_email(self, email: str) -> "LoginPage":
        self.type_text(self.EMAIL_INPUT, email)
        return self

    def enter_password(self, password: str) -> "LoginPage":
        self.type_text(self.PASSWORD_INPUT, password)
        return self

    def click_submit(self) -> "LoginPage":
        self.click(self.SUBMIT_BUTTON)
        logger.info("Submit clicked")
        return self

    def toggle_password_visibility(self) -> "LoginPage":
        self.click(self.SHOW_PWD_TOGGLE)
        return self

    def login(self, email: str, password: str) -> "LoginPage":
        """High-level: fill form and submit."""
        self.enter_email(email)
        self.enter_password(password)
        self.click_submit()
        return self

    def login_and_wait_for_redirect(self, email: str, password: str) -> "LoginPage":
        """Login and wait until the URL changes away from /login."""
        self.login(email, password)
        self.wait_for_url_contains("/dashboard", timeout=10)
        return self

    # ── Assertions / state queries ─────────────────────────────────────────────

    def is_error_displayed(self) -> bool:
        return self.is_visible(self.ERROR_BANNER, timeout=5)

    def get_error_message(self) -> str:
        return self.get_text(self.ERROR_MESSAGE)

    def is_lockout_displayed(self) -> bool:
        """Returns True if the account-locked UI element is visible."""
        if not self.is_visible(self.ERROR_BANNER, timeout=5):
            return False
        msg = self.get_error_message().lower()
        return "lock" in msg or "attempt" in msg or "minutes" in msg

    def is_loading(self) -> bool:
        return self.is_visible(self.LOADING_SPINNER, timeout=3)

    def is_submit_disabled(self) -> bool:
        el = self.find(self.SUBMIT_BUTTON)
        return el.get_attribute("disabled") is not None

    def get_password_input_type(self) -> str:
        """Returns 'password' (hidden) or 'text' (visible)."""
        return self.get_attribute(self.PASSWORD_INPUT, "type")

    def is_brand_visible(self) -> bool:
        return self.is_visible(self.BRAND_TITLE, timeout=5)

    def get_email_validation_message(self) -> str:
        """Returns browser built-in HTML5 validation message for email field."""
        el = self.find(self.EMAIL_INPUT)
        return el.get_attribute("validationMessage") or ""
