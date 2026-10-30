"""Users management page object model (admin-only)."""

from __future__ import annotations

from playwright.sync_api import Page

from pages.base_page import BasePage


class UsersPage(BasePage):
    URL = "/users"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    # ── Navigation ────────────────────────────────────────────

    def wait_for_load(self) -> None:
        self._page.wait_for_load_state("networkidle")

    # ── Actions ───────────────────────────────────────────────

    def click_create_user(self) -> None:
        self._page.get_by_role("button", name="Create").or_(
            self._page.get_by_role("button", name="Add User")
        ).click()

    def fill_user_form(
        self,
        first_name: str,
        last_name: str,
        email: str,
        role: str = "owner",
        phone: str = "",
    ) -> None:
        self._page.get_by_label("First Name", exact=False).fill(first_name)
        self._page.get_by_label("Last Name", exact=False).fill(last_name)
        self._page.get_by_label("Email", exact=False).fill(email)
        if phone:
            self._page.get_by_label("Phone", exact=False).fill(phone)
        self._page.get_by_label("Role", exact=False).click()
        self._page.get_by_role("option", name=role.capitalize()).click()

    def submit_user_form(self) -> None:
        dialog = self._page.locator("[role='dialog']")
        dialog.get_by_role("button", name="Create").click()

    def cancel_form(self) -> None:
        self._page.get_by_role("button", name="Cancel").click()

    def click_edit_user(self, email: str) -> None:
        row = self._page.locator(f"[role='row']:has-text('{email}')")
        row.locator("[aria-label*='Edit'], [aria-label*='edit']").first.click()

    def click_deactivate_user(self, email: str) -> None:
        row = self._page.locator(f"[role='row']:has-text('{email}')")
        row.locator("[aria-label*='Deactivate'], [aria-label*='deactivate']").first.click()

    def click_activate_user(self, email: str) -> None:
        row = self._page.locator(f"[role='row']:has-text('{email}')")
        row.locator("[aria-label*='Activate'], [aria-label*='activate']").first.click()

    def click_reset_password(self, email: str) -> None:
        row = self._page.locator(f"[role='row']:has-text('{email}')")
        row.locator("[aria-label*='Reset'], [aria-label*='reset']").first.click()

    # ── State readers ─────────────────────────────────────────

    def get_user_emails(self) -> list[str]:
        self._page.wait_for_load_state("networkidle")
        cells = self._page.locator(
            "[role='row'] [data-field='email']"
        ).all()
        return [c.inner_text().strip() for c in cells if c.inner_text().strip()]

    def is_user_visible(self, email: str) -> bool:
        return self._page.locator(f"text='{email}'").count() > 0

    def get_user_status(self, email: str) -> str:
        row = self._page.locator(f"[role='row']:has-text('{email}')")
        chip = row.locator("[class*='Chip'], [class*='chip']").first
        return chip.inner_text().strip() if chip.count() > 0 else ""
