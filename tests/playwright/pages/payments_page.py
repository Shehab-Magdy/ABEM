"""Payments management page object model."""

from __future__ import annotations

import re

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

    # ── Shared DataTable / reversal (Phase 5) ─────────────────

    TABLE_ID = "payments-data-table"

    def choose_building(self, building_name: str) -> None:
        """Pick the building in the MUI Select (the label is not wired to the combobox, so find it by group)."""
        group = self._page.locator(".MuiFormControl-root").filter(has_text="Building").first
        group.get_by_role("combobox").click()
        self._page.get_by_role("option", name=building_name).click()

    def choose_unit(self, unit_number: str) -> None:
        group = self._page.locator(".MuiFormControl-root").filter(has_text="Apartment").first
        group.get_by_role("combobox").click()
        self._page.get_by_role("option", name=re.compile(rf"Unit {re.escape(unit_number)}(\s|$)")).click()

    def table(self):
        from pages.data_table_page import DataTablePage

        return DataTablePage(self._page, self.TABLE_ID)

    def reverse_buttons(self):
        return self._page.get_by_test_id("reverse-payment")

    def click_reverse(self, row_index: int = 0) -> None:
        self.reverse_buttons().nth(row_index).click()

    def reverse_dialog(self):
        return self._page.get_by_role("dialog").filter(has=self._page.get_by_test_id("reverse-reason"))

    def fill_reverse_reason(self, reason: str) -> None:
        self._page.get_by_test_id("reverse-reason").fill(reason)

    def confirm_reverse(self) -> None:
        self.reverse_dialog().get_by_role("button", name="Reverse", exact=True).click()

    def voided_chips(self):
        return self._page.get_by_test_id(self.TABLE_ID).get_by_text("Voided", exact=True)

    def reversal_chips(self):
        return self._page.get_by_test_id(self.TABLE_ID).get_by_text("Reversal", exact=True)

    def receipt_numbers(self) -> list[str]:
        """The '#<n>' receipt numbers shown in the first column."""
        cells = self._page.get_by_test_id(self.TABLE_ID).locator("tbody tr td:first-child").all()
        return [c.inner_text().strip().split("\n")[0] for c in cells]
