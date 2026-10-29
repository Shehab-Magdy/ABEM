"""
Page Object for the ABEM Web Dashboard (/dashboard).

Covers the DashboardLayout shell (sidebar + top bar) and the
root dashboard landing page — role-differentiated between Admin and Owner.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from pages.web.base_page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class DashboardPage(BasePage):
    """Interactions with the authenticated dashboard shell."""

    # ── Sidebar nav items ──────────────────────────────────────────────────────
    NAV_DASHBOARD    = (By.XPATH, "//a[@href='/dashboard' or contains(.,'Dashboard')]")
    NAV_BUILDINGS    = (By.XPATH, "//a[@href='/buildings' or contains(.,'Buildings')]")
    NAV_EXPENSES     = (By.XPATH, "//a[@href='/expenses' or contains(.,'Expenses')]")
    NAV_PAYMENTS     = (By.XPATH, "//a[@href='/payments' or contains(.,'Payments')]")
    NAV_USERS        = (By.XPATH, "//a[@href='/users' or contains(.,'Users')]")
    NAV_NOTIF        = (By.XPATH, "//a[@href='/notifications' or contains(.,'Notifications')]")

    # ── Top bar ────────────────────────────────────────────────────────────────
    AVATAR_BUTTON    = (By.CSS_SELECTOR, ".MuiAvatar-root, [data-testid='avatar-btn']")
    ACCOUNT_MENU     = (By.CSS_SELECTOR, ".MuiMenu-paper, [data-testid='account-menu']")
    MY_PROFILE_ITEM  = (By.XPATH, "//li[contains(.,'My Profile')]")
    SIGN_OUT_ITEM    = (By.XPATH, "//li[contains(.,'Sign Out')]")
    USER_EMAIL_ITEM  = (By.CSS_SELECTOR, ".MuiMenu-paper .MuiTypography-body2")
    HAMBURGER_BTN    = (By.CSS_SELECTOR, "[aria-label='open drawer'], button[edge='start']")

    # ── Page content area ──────────────────────────────────────────────────────
    PAGE_CONTENT     = (By.CSS_SELECTOR, "main, [role='main']")
    SIDEBAR          = (By.CSS_SELECTOR, "nav, .MuiDrawer-root")

    # ── Brand ─────────────────────────────────────────────────────────────────
    BRAND_TITLE      = (By.XPATH, "//*[contains(text(),'ABEM')]")

    # ── Actions ────────────────────────────────────────────────────────────────

    def open_account_menu(self) -> "DashboardPage":
        self.click(self.AVATAR_BUTTON)
        self.wait_until_visible(self.ACCOUNT_MENU)
        return self

    def sign_out(self) -> None:
        self.open_account_menu()
        self.click(self.SIGN_OUT_ITEM)
        self.wait_for_url_contains("/login", timeout=5)
        logger.info("Signed out")

    def navigate_to_profile(self) -> None:
        self.open_account_menu()
        self.click(self.MY_PROFILE_ITEM)
        self.wait_for_url_contains("/profile", timeout=5)

    def navigate_to(self, section: str) -> None:
        """Click a named sidebar item. section = 'dashboard'|'users'|..."""
        locators = {
            "dashboard":    self.NAV_DASHBOARD,
            "buildings":    self.NAV_BUILDINGS,
            "expenses":     self.NAV_EXPENSES,
            "payments":     self.NAV_PAYMENTS,
            "users":        self.NAV_USERS,
            "notifications":self.NAV_NOTIF,
        }
        locator = locators.get(section.lower())
        if not locator:
            raise ValueError(f"Unknown section: '{section}'")
        self.click(locator)
        logger.info("Navigated to %s", section)

    # ── State queries ──────────────────────────────────────────────────────────

    def is_sidebar_visible(self) -> bool:
        return self.is_visible(self.SIDEBAR, timeout=5)

    def is_nav_item_visible(self, section: str) -> bool:
        locators = {
            "dashboard":    self.NAV_DASHBOARD,
            "buildings":    self.NAV_BUILDINGS,
            "expenses":     self.NAV_EXPENSES,
            "payments":     self.NAV_PAYMENTS,
            "users":        self.NAV_USERS,
            "notifications":self.NAV_NOTIF,
        }
        return self.is_visible(locators.get(section, self.NAV_DASHBOARD), timeout=3)

    def get_user_email_from_menu(self) -> str:
        self.open_account_menu()
        email = self.get_text(self.USER_EMAIL_ITEM)
        # Close the menu
        self.driver.execute_script("document.body.click()")
        return email

    def wait_until_loaded(self, timeout: int = 10) -> "DashboardPage":
        self.wait_until_visible(self.SIDEBAR, timeout=timeout)
        return self
