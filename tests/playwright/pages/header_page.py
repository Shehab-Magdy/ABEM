"""Header controls: language switch button and the notification bell popover."""

from __future__ import annotations

from playwright.sync_api import Locator, Page, expect

from config.settings import settings


class HeaderPage:
    def __init__(self, page: Page) -> None:
        self._page = page

    def goto(self, path: str = "/dashboard") -> None:
        self._page.goto(f"{settings.BASE_URL}{path}")
        self.language_button.wait_for(state="visible")

    # ── Language switch ───────────────────────────────────────

    @property
    def language_button(self) -> Locator:
        return self._page.get_by_test_id("language-switch")

    def language_button_text(self) -> str:
        return self.language_button.inner_text().strip()

    def click_language_switch(self) -> None:
        self.language_button.click()

    def document_dir(self) -> str:
        return self._page.evaluate("document.documentElement.dir || document.dir || ''")

    def expect_direction(self, direction: str) -> None:
        expect(self._page.locator("html")).to_have_attribute("dir", direction)

    # ── Notification menu ─────────────────────────────────────

    @property
    def bell(self) -> Locator:
        return self._page.get_by_test_id("notification-bell")

    @property
    def panel(self) -> Locator:
        return self._page.locator("#notification-menu-panel")

    @property
    def items(self) -> Locator:
        return self.panel.get_by_test_id("notification-menu-item")

    @property
    def unread_dots(self) -> Locator:
        return self.panel.get_by_test_id("notification-unread-dot")

    def badge_count(self) -> int:
        badge = self._page.get_by_test_id("notification-badge")
        text = badge.inner_text().strip() if badge.count() else ""
        return int("".join(ch for ch in text if ch.isdigit()) or 0)

    def open_menu(self) -> None:
        self.bell.click()
        self.panel.wait_for(state="visible")

    def close_menu(self) -> None:
        self._page.keyboard.press("Escape")
        self.panel.wait_for(state="hidden")

    def tab(self, name: str) -> Locator:
        return self.panel.get_by_test_id(f"menu-tab-{name}")

    def select_tab(self, name: str) -> None:
        self.tab(name).click()

    def mark_all_read_in_menu(self) -> None:
        self.panel.get_by_role("button", name="Mark all as read").click()

    def mark_all_read_button_in_menu(self) -> Locator:
        return self.panel.get_by_role("button", name="Mark all as read")

    def empty_state(self) -> Locator:
        return self.panel.get_by_test_id("notification-menu-empty")

    def open_center(self) -> None:
        self.panel.get_by_test_id("notification-menu-open-center").click()

    def scroll_list_to_end(self) -> None:
        self.panel.get_by_test_id("notification-menu-list").evaluate("el => { el.scrollTop = el.scrollHeight; }")
