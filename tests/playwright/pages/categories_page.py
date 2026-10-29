"""Expense categories page object model (admin-only)."""

from __future__ import annotations

from playwright.sync_api import Page

from pages.base_page import BasePage


class CategoriesPage(BasePage):
    URL = "/expense-categories"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    # ── Navigation ────────────────────────────────────────────

    def wait_for_load(self) -> None:
        self._page.wait_for_load_state("networkidle")

    # ── Actions ───────────────────────────────────────────────

    def click_add_category(self) -> None:
        self._page.get_by_role("button", name="Add").or_(
            self._page.get_by_role("button", name="Create")
        ).click()

    def fill_category_form(
        self,
        name: str,
        description: str = "",
        icon: str = "category",
        color: str = "#2563EB",
    ) -> None:
        self._page.get_by_label("Name", exact=False).fill(name)
        if description:
            self._page.get_by_label("Description", exact=False).fill(description)

    def submit_category_form(self) -> None:
        dialog = self._page.locator("[role='dialog']")
        dialog.get_by_role("button", name="Create").or_(
            dialog.get_by_role("button", name="Save")
        ).click()

    def click_delete_category(self, name: str) -> None:
        row = self._page.locator(f"[role='row']:has-text('{name}'), tr:has-text('{name}')")
        row.locator("[aria-label*='Delete'], [aria-label*='delete']").first.click()

    def confirm_delete(self) -> None:
        self._page.get_by_role("button", name="Delete").or_(
            self._page.get_by_role("button", name="Confirm")
        ).click()

    # ── State readers ─────────────────────────────────────────

    def get_category_names(self) -> list[str]:
        self._page.wait_for_load_state("networkidle")
        cells = self._page.locator(
            "[role='row'] td:first-child, [role='row'] [data-field='name']"
        ).all()
        return [c.inner_text().strip() for c in cells if c.inner_text().strip()]

    def get_category_count(self) -> int:
        return len(self.get_category_names())

    def is_category_visible(self, name: str) -> bool:
        return self._page.locator(f"text='{name}'").count() > 0

    def is_add_button_visible(self) -> bool:
        try:
            self._page.get_by_role("button", name="Add").or_(
                self._page.get_by_role("button", name="Create")
            ).wait_for(state="visible", timeout=3_000)
            return True
        except Exception:
            return False

    def is_delete_button_visible(self) -> bool:
        return self._page.locator("[aria-label*='Delete'], [aria-label*='delete']").count() > 0
