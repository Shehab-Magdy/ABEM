"""Exports page object model — download CSV, XLSX, PDF receipts."""

from __future__ import annotations

from playwright.sync_api import Page

from pages.base_page import BasePage


class ExportsPage(BasePage):
    """Exports are typically accessed from Payments page or Dashboard."""

    URL = "/payments"  # exports are on payments page

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    # ── Navigation ────────────────────────────────────────────

    def wait_for_load(self) -> None:
        self._page.wait_for_load_state("networkidle")

    # ── Export actions ────────────────────────────────────────

    def click_export_csv(self) -> None:
        self._page.get_by_role("button", name="CSV").or_(
            self._page.get_by_role("button", name="Export CSV")
        ).click()

    def click_export_xlsx(self) -> None:
        self._page.get_by_role("button", name="XLSX").or_(
            self._page.get_by_role("button", name="Export XLSX")
        ).click()

    def click_print_receipt(self, row_index: int = 0) -> None:
        self._page.get_by_test_id("print-receipt").nth(row_index).click()

    # ── Download capture ──────────────────────────────────────

    def download_csv(self) -> bytes:
        """Click CSV export and capture the downloaded file content."""
        with self._page.expect_download() as download_info:
            self.click_export_csv()
        download = download_info.value
        path = download.path()
        with open(path, "rb") as f:
            return f.read()

    def download_xlsx(self) -> bytes:
        """Click XLSX export and capture the downloaded file content."""
        with self._page.expect_download() as download_info:
            self.click_export_xlsx()
        download = download_info.value
        path = download.path()
        with open(path, "rb") as f:
            return f.read()

    def download_receipt(self, row_index: int = 0) -> bytes:
        """Click print receipt and capture the downloaded PDF content."""
        with self._page.expect_download() as download_info:
            self.click_print_receipt(row_index)
        download = download_info.value
        path = download.path()
        with open(path, "rb") as f:
            return f.read()

    # ── State readers ─────────────────────────────────────────

    def is_csv_button_visible(self) -> bool:
        try:
            self._page.get_by_role("button", name="CSV").or_(
                self._page.get_by_role("button", name="Export CSV")
            ).wait_for(state="visible", timeout=3_000)
            return True
        except Exception:
            return False

    def is_xlsx_button_visible(self) -> bool:
        try:
            self._page.get_by_role("button", name="XLSX").or_(
                self._page.get_by_role("button", name="Export XLSX")
            ).wait_for(state="visible", timeout=3_000)
            return True
        except Exception:
            return False
