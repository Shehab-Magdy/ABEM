"""Records page (/records): minutes, documents and the whole-building export."""

from __future__ import annotations

from playwright.sync_api import Download, Page

from pages.base_page import BasePage


class RecordsPage(BasePage):
    URL = "/records"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def wait_for_load(self) -> None:
        self._page.get_by_role("heading").first.wait_for(state="visible")
        self._page.wait_for_load_state("networkidle")

    def choose_building(self, name: str) -> None:
        select = self._page.get_by_label("Building", exact=True)
        if select.count():
            select.click()
            self._page.get_by_role("option", name=name).click()

    def export_button(self):
        return self._page.get_by_test_id("export-building")

    def download_building_export(self) -> Download:
        with self._page.expect_download() as info:
            self.export_button().click()
        return info.value
