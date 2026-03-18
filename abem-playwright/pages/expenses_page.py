"""Expenses management page object model."""

from __future__ import annotations

from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class ExpensesPage(BasePage):
    URL = "/expenses"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._add_btn = page.locator("#add-expense-btn")
        self._table = page.locator("#expenses-table")

    # ── Navigation ────────────────────────────────────────────

    def wait_for_load(self) -> None:
        self._page.wait_for_load_state("networkidle")

    # ── Building selector ─────────────────────────────────────

    def select_building(self, building_name: str) -> None:
        self._page.get_by_label("Building").click()
        self._page.get_by_role("option", name=building_name).click()
        self._page.wait_for_load_state("networkidle")

    # ── Filters ───────────────────────────────────────────────

    def set_date_from(self, date_str: str) -> None:
        self._page.get_by_label("Date From", exact=False).fill(date_str)

    def set_date_to(self, date_str: str) -> None:
        self._page.get_by_label("Date To", exact=False).fill(date_str)

    def select_category_filter(self, category_name: str) -> None:
        self._page.get_by_label("Category", exact=False).click()
        self._page.get_by_role("option", name=category_name).click()

    def apply_filters(self) -> None:
        self._page.get_by_role("button", name="Apply").or_(
            self._page.locator("[aria-label*='filter']")
        ).first.click()
        self._page.wait_for_load_state("networkidle")

    # ── Actions ───────────────────────────────────────────────

    def click_add_expense(self) -> None:
        self._add_btn.click()

    def fill_expense_form(
        self,
        title: str,
        amount: str,
        category_name: str | None = None,
        expense_date: str | None = None,
        split_type: str = "equal_all",
        description: str = "",
        is_recurring: bool = False,
        frequency: str | None = None,
    ) -> None:
        """Fill the expense create/edit form."""
        self._page.get_by_label("Title", exact=False).fill(title)
        amt_field = self._page.get_by_label("Amount", exact=False)
        amt_field.clear()
        amt_field.fill(amount)
        if description:
            self._page.get_by_label("Description", exact=False).fill(description)
        if expense_date:
            self._page.get_by_label("Expense Date", exact=False).fill(expense_date)
        if category_name:
            self._page.get_by_label("Category", exact=False).click()
            self._page.get_by_role("option", name=category_name).click()
        # Split type
        self._page.get_by_label("Split Type", exact=False).click()
        split_labels = {
            "equal_all": "Equal",
            "equal_apartments": "Apartments",
            "equal_stores": "Stores",
            "custom": "Custom",
        }
        self._page.get_by_role(
            "option", name=split_labels.get(split_type, split_type)
        ).click()
        if is_recurring:
            self._page.get_by_label("Recurring", exact=False).check()
            if frequency:
                self._page.get_by_label("Frequency", exact=False).click()
                self._page.get_by_role("option", name=frequency.capitalize()).click()

    def submit_expense_form(self) -> None:
        dialog = self._page.locator("[role='dialog']")
        dialog.get_by_role("button", name="Create").or_(
            dialog.get_by_role("button", name="Save")
        ).click()

    def cancel_form(self) -> None:
        self._page.get_by_role("button", name="Cancel").click()

    def click_view_expense(self, title: str) -> None:
        row = self._page.locator(f"tr:has-text('{title}'), [role='row']:has-text('{title}')")
        row.locator("[aria-label*='View'], [aria-label*='view']").first.click()

    def click_edit_expense(self, title: str) -> None:
        row = self._page.locator(f"tr:has-text('{title}'), [role='row']:has-text('{title}')")
        row.locator("[aria-label*='Edit'], [aria-label*='edit']").first.click()

    def click_delete_expense(self, title: str) -> None:
        row = self._page.locator(f"tr:has-text('{title}'), [role='row']:has-text('{title}')")
        row.locator("[aria-label*='Delete'], [aria-label*='delete']").first.click()

    def confirm_delete(self) -> None:
        self._page.get_by_role("button", name="Delete").or_(
            self._page.get_by_role("button", name="Confirm")
        ).click()

    def click_upload_bill(self, title: str) -> None:
        """Click the upload bill icon for an expense row."""
        row = self._page.locator(f"tr:has-text('{title}'), [role='row']:has-text('{title}')")
        row.locator("[aria-label*='Upload'], [aria-label*='upload']").first.click()

    def upload_file(self, file_path: str) -> None:
        """Set input files on the hidden file input."""
        self._page.locator("input[type='file']").set_input_files(file_path)

    # ── State readers ─────────────────────────────────────────

    def get_expense_titles(self) -> list[str]:
        self._page.wait_for_load_state("networkidle")
        rows = self._page.locator(
            "#expenses-table tbody tr td:first-child, "
            "[role='row'] [data-field='title']"
        ).all()
        return [r.inner_text().strip() for r in rows if r.inner_text().strip()]

    def is_expense_visible(self, title: str) -> bool:
        return self._page.locator(f"text='{title}'").count() > 0

    def is_add_button_visible(self) -> bool:
        try:
            self._add_btn.wait_for(state="visible", timeout=3_000)
            return True
        except Exception:
            return False

    def get_expense_detail_shares(self) -> list[dict]:
        """Read the per-unit share breakdown from the detail dialog."""
        rows = self._page.locator("[role='dialog'] table tbody tr").all()
        shares = []
        for row in rows:
            cells = row.locator("td").all()
            if len(cells) >= 2:
                shares.append({
                    "unit": cells[0].inner_text().strip(),
                    "share_amount": cells[1].inner_text().strip(),
                })
        return shares

    def is_recurring_badge_visible(self, title: str) -> bool:
        row = self._page.locator(f"tr:has-text('{title}'), [role='row']:has-text('{title}')")
        return row.locator("[class*='recurring'], [aria-label*='recurring']").count() > 0

    def is_bill_attachment_visible(self, title: str) -> bool:
        row = self._page.locator(f"tr:has-text('{title}'), [role='row']:has-text('{title}')")
        return row.locator("[aria-label*='attachment'], [aria-label*='bill']").count() > 0
