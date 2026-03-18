"""Buildings management page object model."""

from __future__ import annotations

from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class BuildingsPage(BasePage):
    URL = "/buildings"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._add_btn = page.locator("#add-building-btn")

    # ── Navigation ────────────────────────────────────────────

    def wait_for_load(self) -> None:
        self._page.wait_for_load_state("networkidle")

    # ── Actions ───────────────────────────────────────────────

    def click_add_building(self) -> None:
        self._add_btn.click()

    def fill_building_form(
        self,
        name: str,
        address: str,
        city: str = "Cairo",
        country: str = "Egypt",
        num_floors: int = 5,
        num_apartments: int = 2,
        num_stores: int = 1,
    ) -> None:
        """Fill the building create/edit dialog form."""
        self._page.get_by_label("Name", exact=False).fill(name)
        self._page.get_by_label("Address", exact=False).fill(address)
        self._page.get_by_label("City", exact=False).fill(city)
        self._page.get_by_label("Country", exact=False).fill(country)
        floors = self._page.get_by_label("Floors", exact=False)
        floors.clear()
        floors.fill(str(num_floors))
        apts = self._page.get_by_label("Apartments", exact=False)
        apts.clear()
        apts.fill(str(num_apartments))
        stores = self._page.get_by_label("Stores", exact=False)
        stores.clear()
        stores.fill(str(num_stores))

    def submit_building_form(self) -> None:
        """Click the Create or Save button in the dialog."""
        dialog = self._page.locator("[role='dialog']")
        dialog.get_by_role("button", name="Create").or_(
            dialog.get_by_role("button", name="Save")
        ).click()

    def cancel_form(self) -> None:
        self._page.get_by_role("button", name="Cancel").click()

    def click_edit_building(self, building_name: str) -> None:
        """Click the edit icon for a building row."""
        row = self._page.locator(f"[role='row']:has-text('{building_name}')")
        row.get_by_role("button", name="Edit").or_(
            row.locator("[aria-label*='edit'], [aria-label*='Edit']")
        ).first.click()

    def click_delete_building(self, building_name: str) -> None:
        """Click the delete icon for a building row."""
        row = self._page.locator(f"[role='row']:has-text('{building_name}')")
        row.get_by_role("button", name="Delete").or_(
            row.locator("[aria-label*='delete'], [aria-label*='Delete']")
        ).first.click()

    def confirm_delete(self) -> None:
        """Confirm the delete dialog."""
        self._page.get_by_role("button", name="Delete").or_(
            self._page.get_by_role("button", name="Confirm")
        ).click()

    def cancel_delete(self) -> None:
        self._page.get_by_role("button", name="Cancel").click()

    def click_manage_units(self, building_name: str) -> None:
        """Click the manage units icon for a building row."""
        row = self._page.locator(f"[role='row']:has-text('{building_name}')")
        row.locator("[aria-label*='unit'], [aria-label*='apartment']").first.click()

    # ── State readers ─────────────────────────────────────────

    def get_building_names(self) -> list[str]:
        """Return all visible building names from the list/table."""
        self._page.wait_for_load_state("networkidle")
        cells = self._page.locator("[role='row'] [data-field='name']").all()
        return [cell.inner_text().strip() for cell in cells if cell.inner_text().strip()]

    def is_building_visible(self, name: str) -> bool:
        return self._page.locator(f"[role='row']:has-text('{name}')").count() > 0

    def is_add_button_visible(self) -> bool:
        try:
            self._add_btn.wait_for(state="visible", timeout=3_000)
            return True
        except Exception:
            return False

    def get_row_count(self) -> int:
        """Return the number of data rows in the buildings grid."""
        return self._page.locator("[role='row']").count() - 1  # minus header
