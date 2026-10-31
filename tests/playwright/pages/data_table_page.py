"""Page object for the shared DataTable component (frontend/src/components/DataTable.jsx).

A plain MUI Table with a search box, sortable headers (TableSortLabel) and a TablePagination footer. The table
carries data-testid=<test_id>; the search input carries data-testid=<test_id>-search.
"""

from __future__ import annotations

import re

from playwright.sync_api import Locator, Page, expect


class DataTablePage:
    def __init__(self, page: Page, test_id: str) -> None:
        self._page = page
        self.test_id = test_id
        self.table: Locator = page.get_by_test_id(test_id)
        self.search_box: Locator = page.get_by_test_id(f"{test_id}-search")
        # The card around the table holds the toolbar and the pager.
        self.card: Locator = self.table.locator("xpath=ancestor::div[contains(@class,'MuiPaper-root')][1]")

    # ── Waiting ───────────────────────────────────────────────

    def wait_ready(self) -> None:
        self.table.wait_for(state="visible")
        expect(self.table.locator("[role='progressbar']")).to_have_count(0)

    # ── Search ────────────────────────────────────────────────

    def search_placeholder(self) -> str:
        return self.search_box.get_attribute("placeholder") or ""

    def search(self, text: str) -> None:
        self.search_box.fill(text)

    def clear_search(self) -> None:
        self.search_box.fill("")

    # ── Rows ──────────────────────────────────────────────────

    @property
    def rows(self) -> Locator:
        return self.table.locator("tbody tr")

    def row_texts(self) -> list[str]:
        return [r.inner_text() for r in self.rows.all()]

    def column_texts(self, column_index: int) -> list[str]:
        return [r.locator("td").nth(column_index).inner_text().strip() for r in self.rows.all()]

    def row_with(self, text: str) -> Locator:
        return self.rows.filter(has_text=text)

    def empty_message(self) -> Locator:
        return self.table.locator("tbody tr td[colspan]")

    # ── Sorting ───────────────────────────────────────────────

    def header(self, label: str) -> Locator:
        return self.table.locator("thead th").filter(has_text=re.compile(rf"^\s*{re.escape(label)}\s*$"))

    def sort_by(self, label: str) -> None:
        self.header(label).locator(".MuiTableSortLabel-root").click()

    def sort_direction(self, label: str) -> str | None:
        """'ascending' / 'descending' from aria-sort, or None when the column is not the sorted one."""
        return self.header(label).get_attribute("aria-sort")

    def header_labels(self) -> list[str]:
        return [h.inner_text().strip() for h in self.table.locator("thead th").all()]

    # ── Pagination ────────────────────────────────────────────

    @property
    def pager(self) -> Locator:
        return self.card.locator(".MuiTablePagination-root")

    def displayed_rows_text(self) -> str:
        return self.pager.locator(".MuiTablePagination-displayedRows").inner_text()

    def next_page(self) -> None:
        self.pager.get_by_role("button", name=re.compile("next page|الصفحة التالية", re.I)).click()

    def previous_page(self) -> None:
        self.pager.get_by_role("button", name=re.compile("previous page|الصفحة السابقة", re.I)).click()

    def is_next_enabled(self) -> bool:
        return self.pager.get_by_role("button", name=re.compile("next page|الصفحة التالية", re.I)).is_enabled()

    def rows_per_page_options(self) -> list[str]:
        self.pager.get_by_role("combobox").click()
        options = [o.inner_text().strip() for o in self._page.get_by_role("option").all()]
        self._page.keyboard.press("Escape")
        return options

    def set_rows_per_page(self, value: int) -> None:
        self.pager.get_by_role("combobox").click()
        self._page.get_by_role("option", name=str(value), exact=True).click()
