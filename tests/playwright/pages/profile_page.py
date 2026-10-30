"""Profile page object model."""

from __future__ import annotations

from playwright.sync_api import Page

from pages.base_page import BasePage


class ProfilePage(BasePage):
    URL = "/profile"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    # ── Navigation ────────────────────────────────────────────

    def wait_for_load(self) -> None:
        self._page.wait_for_load_state("networkidle")

    # ── State readers ─────────────────────────────────────────

    def get_displayed_name(self) -> str:
        return self._page.locator("[data-testid='profile-name'], h5, h6").first.inner_text().strip()

    def get_displayed_email(self) -> str:
        return self._page.locator("[data-testid='profile-email']").inner_text().strip()

    def get_displayed_phone(self) -> str:
        return self._page.locator("[data-testid='profile-phone']").inner_text().strip()

    def get_displayed_role(self) -> str:
        return self._page.locator("[data-testid='profile-role']").inner_text().strip()

    # ── Edit profile ──────────────────────────────────────────

    def click_edit_profile(self) -> None:
        self._page.get_by_role("button", name="Edit").or_(
            self._page.get_by_role("button", name="Edit Profile")
        ).click()

    def fill_name(self, first_name: str, last_name: str) -> None:
        self._page.get_by_label("First Name", exact=False).clear()
        self._page.get_by_label("First Name", exact=False).fill(first_name)
        self._page.get_by_label("Last Name", exact=False).clear()
        self._page.get_by_label("Last Name", exact=False).fill(last_name)

    def fill_phone(self, phone: str) -> None:
        self._page.get_by_label("Phone", exact=False).clear()
        self._page.get_by_label("Phone", exact=False).fill(phone)

    def save_profile(self) -> None:
        self._page.get_by_role("button", name="Save").click()

    # ── Change password ───────────────────────────────────────

    def click_change_password(self) -> None:
        self._page.get_by_role("button", name="Change Password").or_(
            self._page.get_by_role("button", name="Reset Password")
        ).click()

    def fill_password_form(
        self,
        current_password: str,
        new_password: str,
        confirm_password: str,
    ) -> None:
        self._page.get_by_label("Current Password", exact=False).fill(current_password)
        self._page.get_by_label("New Password", exact=False).fill(new_password)
        self._page.get_by_label("Confirm", exact=False).fill(confirm_password)

    def submit_password_change(self) -> None:
        self._page.get_by_role("button", name="Reset").or_(
            self._page.get_by_role("button", name="Change")
        ).click()

    # ── Validation errors ─────────────────────────────────────

    def get_form_error(self) -> str:
        alert = self._page.locator("[role='alert']").first
        try:
            alert.wait_for(state="visible", timeout=5_000)
            return alert.inner_text().strip()
        except Exception:
            return ""
