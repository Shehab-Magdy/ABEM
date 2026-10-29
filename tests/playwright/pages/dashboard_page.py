"""Dashboard page object model — handles both admin and owner views."""

from __future__ import annotations

from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class DashboardPage(BasePage):
    URL = "/dashboard"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    # ── Navigation ────────────────────────────────────────────

    def wait_for_load(self) -> None:
        self._page.wait_for_load_state("networkidle")

    # ── Building selector (admin) ─────────────────────────────

    def select_building(self, building_name: str) -> None:
        """Select a building from the building selector dropdown."""
        selector = self._page.get_by_test_id("building-selector")
        selector.click()
        self._page.get_by_role("option", name=building_name).click()

    def get_selected_building(self) -> str:
        """Return the currently selected building name."""
        return self._page.get_by_test_id("building-selector").input_value()

    def is_building_selector_visible(self) -> bool:
        try:
            self._page.get_by_test_id("building-selector").wait_for(
                state="visible", timeout=3_000
            )
            return True
        except Exception:
            return False

    # ── Admin KPI cards ───────────────────────────────────────

    def get_total_income(self) -> str:
        return self._page.get_by_test_id("total-income").inner_text()

    def get_total_expenses(self) -> str:
        return self._page.get_by_test_id("total-expenses").inner_text()

    def get_overdue_count(self) -> str:
        return self._page.get_by_test_id("overdue-units-count").inner_text()

    def is_overdue_card_visible(self) -> bool:
        try:
            self._page.get_by_test_id("overdue-units-card").wait_for(
                state="visible", timeout=3_000
            )
            return True
        except Exception:
            return False

    # ── Owner dashboard ───────────────────────────────────────

    def get_current_balance(self) -> str:
        return self._page.get_by_test_id("current-balance").inner_text()

    def get_total_paid_ytd(self) -> str:
        return self._page.get_by_test_id("total-paid-ytd").inner_text()

    def is_credit_label_visible(self) -> bool:
        try:
            self._page.get_by_test_id("credit-label").wait_for(
                state="visible", timeout=3_000
            )
            return True
        except Exception:
            return False

    def is_settled_label_visible(self) -> bool:
        try:
            self._page.get_by_test_id("settled-label").wait_for(
                state="visible", timeout=3_000
            )
            return True
        except Exception:
            return False

    # ── Date filters ──────────────────────────────────────────

    def set_date_from(self, date_str: str) -> None:
        self._page.get_by_test_id("date-from").fill(date_str)

    def set_date_to(self, date_str: str) -> None:
        self._page.get_by_test_id("date-to").fill(date_str)

    # ── Download ──────────────────────────────────────────────

    def click_download_report(self) -> None:
        self._page.get_by_test_id("download-report").click()

    def is_download_report_visible(self) -> bool:
        try:
            self._page.get_by_test_id("download-report").wait_for(
                state="visible", timeout=3_000
            )
            return True
        except Exception:
            return False

    # ── Empty state ───────────────────────────────────────────

    def is_empty_state_visible(self) -> bool:
        try:
            self._page.get_by_test_id("empty-state").wait_for(
                state="visible", timeout=3_000
            )
            return True
        except Exception:
            return False
