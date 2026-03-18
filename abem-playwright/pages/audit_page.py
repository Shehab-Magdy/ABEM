"""Audit log page object model (admin-only)."""

from __future__ import annotations

from playwright.sync_api import Page

from pages.base_page import BasePage


class AuditPage(BasePage):
    URL = "/audit"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    # ── Navigation ────────────────────────────────────────────

    def wait_for_load(self) -> None:
        self._page.wait_for_load_state("networkidle")

    # ── Filters ───────────────────────────────────────────────

    def filter_by_entity(self, entity: str) -> None:
        self._page.get_by_label("Entity", exact=False).click()
        self._page.get_by_role("option", name=entity).click()
        self._page.wait_for_load_state("networkidle")

    def filter_by_action(self, action: str) -> None:
        self._page.get_by_label("Action", exact=False).click()
        self._page.get_by_role("option", name=action).click()
        self._page.wait_for_load_state("networkidle")

    # ── State readers ─────────────────────────────────────────

    def get_log_entries(self) -> list[dict]:
        """Read all visible audit log entries."""
        self._page.wait_for_load_state("networkidle")
        rows = self._page.locator("table tbody tr, [role='row']").all()
        entries = []
        for row in rows:
            cells = row.locator("td").all()
            if len(cells) >= 3:
                entries.append({
                    "action": cells[0].inner_text().strip(),
                    "entity": cells[1].inner_text().strip(),
                    "user": cells[2].inner_text().strip(),
                })
        return entries

    def get_entry_count(self) -> int:
        return len(self.get_log_entries())

    def is_entry_visible(self, action: str, entity: str) -> bool:
        for entry in self.get_log_entries():
            if action in entry["action"] and entity in entry["entity"]:
                return True
        return False
