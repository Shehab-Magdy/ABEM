"""Payments management page object model."""

from __future__ import annotations

from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class PaymentsPage(BasePage):
    URL = "/payments"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    # ── Navigation ────────────────────────────────────────────

    def wait_for_load(self) -> None:
        self._page.wait_for_load_state("networkidle")

    # ── Selectors ─────────────────────────────────────────────

    def select_building(self, building_name: str) -> None:
        self._page.get_by_label("Building", exact=False).click()
        self._page.get_by_role("option", name=building_name).click()
        self._page.wait_for_load_state("networkidle")

    def select_apartment(self, unit_label: str) -> None:
        self._page.get_by_label("Apartment", exact=False).click()
        self._page.get_by_role("option", name=unit_label).click()
        self._page.wait_for_load_state("networkidle")

    # ── Actions ───────────────────────────────────────────────

    def click_record_payment(self) -> None:
        self._page.get_by_role("button", name="Record Payment").or_(
            self._page.get_by_role("button", name="Add Payment")
        ).click()

    def fill_payment_form(
        self,
        apartment_label: str | None = None,
        amount: str = "",
        payment_method: str = "cash",
        payment_date: str | None = None,
        notes: str = "",
    ) -> None:
        """Fill the record payment dialog form."""
        if apartment_label:
            self._page.get_by_label("Apartment", exact=False).click()
            self._page.get_by_role("option", name=apartment_label).click()
        amt = self._page.get_by_label("Amount", exact=False)
        amt.clear()
        amt.fill(amount)
        if payment_date:
            self._page.get_by_label("Payment Date", exact=False).fill(payment_date)
        self._page.get_by_label("Payment Method", exact=False).click()
        method_labels = {
            "cash": "Cash",
            "bank_transfer": "Bank Transfer",
            "cheque": "Cheque",
            "other": "Other",
        }
        self._page.get_by_role(
            "option", name=method_labels.get(payment_method, payment_method)
        ).click()
        if notes:
            self._page.get_by_label("Notes", exact=False).fill(notes)

    def submit_payment_form(self) -> None:
        dialog = self._page.locator("[role='dialog']")
        dialog.get_by_role("button", name="Record").or_(
            dialog.get_by_role("button", name="Save")
        ).click()

    def cancel_form(self) -> None:
        self._page.get_by_role("button", name="Cancel").click()

    def click_print_receipt(self, row_index: int = 0) -> None:
        """Click the print receipt button on a payment row."""
        self._page.get_by_test_id("print-receipt").nth(row_index).click()

    # ── State readers ─────────────────────────────────────────

    def get_current_balance(self) -> str:
        """Read the displayed balance for the selected apartment."""
        balance = self._page.locator("[class*='balance'], [data-testid*='balance']").first
        return balance.inner_text().strip()

    def get_payment_rows(self) -> list[dict]:
        """Read all visible payment history rows."""
        rows = self._page.locator("table tbody tr").all()
        result = []
        for row in rows:
            cells = row.locator("td").all()
            if len(cells) >= 3:
                result.append({
                    "date": cells[0].inner_text().strip(),
                    "amount": cells[1].inner_text().strip(),
                    "method": cells[2].inner_text().strip(),
                })
        return result

    def get_payment_count(self) -> int:
        return len(self.get_payment_rows())

    def is_record_button_visible(self) -> bool:
        try:
            self._page.get_by_role("button", name="Record Payment").or_(
                self._page.get_by_role("button", name="Add Payment")
            ).wait_for(state="visible", timeout=3_000)
            return True
        except Exception:
            return False

    def is_export_button_visible(self) -> bool:
        try:
            self._page.get_by_role("button", name="Export").or_(
                self._page.locator("[aria-label*='export']")
            ).first.wait_for(state="visible", timeout=3_000)
            return True
        except Exception:
            return False
