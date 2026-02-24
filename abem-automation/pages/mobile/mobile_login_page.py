"""
Mobile Page Object for the ABEM Flutter Login Screen.

Maps to: mobile/lib/features/auth/screens/login_screen.dart

Flutter Semantics labels are used as the primary accessibility_id selector.
Add Semantics wrappers to the Flutter widgets if not already present:

    Semantics(
      label: 'email-input',
      child: TextFormField(controller: _emailController, ...),
    )

Widget labels used in this POM:
    'email-input'           → Email TextFormField
    'password-input'        → Password TextFormField
    'toggle-password-btn'   → Visibility toggle IconButton
    'sign-in-btn'           → FilledButton
    'error-banner'          → _ErrorBanner container
    'loading-indicator'     → CircularProgressIndicator
    'brand-title'           → 'ABEM' Text widget
"""

from __future__ import annotations

from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pages.mobile.base_mobile_page import BaseMobilePage
from utils.logger import get_logger

logger = get_logger(__name__)


class MobileLoginPage(BaseMobilePage):
    """Interactions with the Flutter Login Screen."""

    # ── Accessibility ID labels (add Semantics in Flutter source) ──────────────
    EMAIL_INPUT        = "email-input"
    PASSWORD_INPUT     = "password-input"
    TOGGLE_PWD_BTN     = "toggle-password-btn"
    SIGN_IN_BUTTON     = "sign-in-btn"
    ERROR_BANNER       = "error-banner"
    LOADING_INDICATOR  = "loading-indicator"
    BRAND_TITLE        = "brand-title"

    # Fallback XPath selectors (Android UiAutomator2 native)
    _SIGN_IN_XPATH     = "//android.widget.Button[@text='Sign In' or @content-desc='Sign In']"
    _ERROR_XPATH       = "//*[contains(@text,'Invalid') or contains(@text,'incorrect') or contains(@text,'locked')]"
    _BRAND_XPATH       = "//*[@text='ABEM']"

    # ── Navigation ─────────────────────────────────────────────────────────────

    def wait_for_login_screen(self, timeout: int = 15) -> "MobileLoginPage":
        """Block until the login screen is fully rendered."""
        try:
            self.wait_for(self.EMAIL_INPUT, timeout=timeout)
        except Exception:
            # Fallback to XPath if accessibility IDs aren't set
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(
                    (AppiumBy.XPATH, "//android.widget.EditText")
                )
            )
        logger.info("Login screen ready")
        return self

    # ── Actions ────────────────────────────────────────────────────────────────

    def enter_email(self, email: str) -> "MobileLoginPage":
        try:
            self.type_into(self.EMAIL_INPUT, email)
        except Exception:
            # Fallback: first EditText on screen
            fields = self.driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
            if fields:
                fields[0].clear()
                fields[0].send_keys(email)
        self.hide_keyboard()
        return self

    def enter_password(self, password: str) -> "MobileLoginPage":
        try:
            self.type_into(self.PASSWORD_INPUT, password)
        except Exception:
            fields = self.driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
            if len(fields) > 1:
                fields[1].clear()
                fields[1].send_keys(password)
        self.hide_keyboard()
        return self

    def tap_sign_in(self) -> "MobileLoginPage":
        try:
            self.tap(self.SIGN_IN_BUTTON)
        except Exception:
            self.tap_by_text("Sign In")
        logger.info("Sign-In tapped")
        return self

    def toggle_password_visibility(self) -> "MobileLoginPage":
        try:
            self.tap(self.TOGGLE_PWD_BTN)
        except Exception:
            # Fallback: locate by icon description
            btns = self.driver.find_elements(
                AppiumBy.XPATH,
                "//android.widget.ImageButton | //android.widget.Button",
            )
            if len(btns) > 0:
                btns[-1].click()
        return self

    def login(self, email: str, password: str) -> "MobileLoginPage":
        """High-level: fill both fields and submit."""
        self.enter_email(email)
        self.enter_password(password)
        self.tap_sign_in()
        return self

    # ── State queries ──────────────────────────────────────────────────────────

    def is_error_displayed(self, timeout: int = 6) -> bool:
        try:
            return self.is_visible(self.ERROR_BANNER, timeout=timeout)
        except Exception:
            return self.is_text_visible("Invalid", timeout=timeout) or \
                   self.is_text_visible("incorrect", timeout=timeout)

    def get_error_text(self) -> str:
        try:
            return self.get_text(self.ERROR_BANNER)
        except Exception:
            el = self.find_by_xpath(self._ERROR_XPATH)
            return el.text

    def is_lockout_error_displayed(self, timeout: int = 6) -> bool:
        if not self.is_error_displayed(timeout=timeout):
            return False
        err = self.get_error_text().lower()
        return "lock" in err or "attempt" in err or "minutes" in err

    def is_loading_displayed(self) -> bool:
        return self.is_visible(self.LOADING_INDICATOR, timeout=3)

    def is_brand_visible(self) -> bool:
        try:
            return self.is_visible(self.BRAND_TITLE, timeout=3)
        except Exception:
            return self.is_text_visible("ABEM", timeout=3)
