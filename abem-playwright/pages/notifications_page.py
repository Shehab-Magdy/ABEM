"""Notifications center page object model."""

from __future__ import annotations

from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class NotificationsPage(BasePage):
    URL = "/notifications"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    # ── Navigation ────────────────────────────────────────────

    def wait_for_load(self) -> None:
        self._page.wait_for_load_state("networkidle")

    # ── Bell icon (in layout, not notifications page) ─────────

    def get_unread_badge_count(self) -> int:
        """Read the notification bell badge count from the layout."""
        badge = self._page.get_by_test_id("notification-badge")
        try:
            badge.wait_for(state="visible", timeout=3_000)
            text = badge.inner_text().strip()
            return int(text) if text.isdigit() else 0
        except Exception:
            return 0

    def click_notification_bell(self) -> None:
        self._page.get_by_test_id("notification-bell").click()

    # ── Filter chips ──────────────────────────────────────────

    def click_filter_all(self) -> None:
        self._page.get_by_test_id("filter-all").click()

    def click_filter_unread(self) -> None:
        self._page.get_by_test_id("filter-unread").click()

    # ── Notification list ─────────────────────────────────────

    def get_notification_items(self) -> list[dict]:
        """Read all visible notification items."""
        items = self._page.get_by_test_id("notification-item").all()
        result = []
        for item in items:
            result.append({
                "text": item.inner_text().strip(),
                "type": item.get_by_test_id("notification-type-chip").inner_text().strip()
                if item.get_by_test_id("notification-type-chip").count() > 0
                else "",
            })
        return result

    def get_notification_count(self) -> int:
        return self._page.get_by_test_id("notification-item").count()

    def mark_as_read(self, index: int = 0) -> None:
        """Click the mark-as-read button on a notification item."""
        items = self._page.get_by_test_id("notification-item").all()
        if index < len(items):
            btn = items[index].get_by_test_id("mark-read-btn")
            if btn.count() > 0:
                btn.click()

    def is_empty_state_visible(self) -> bool:
        try:
            self._page.get_by_test_id("empty-notifications").wait_for(
                state="visible", timeout=3_000
            )
            return True
        except Exception:
            return False

    # ── Broadcast (admin) ─────────────────────────────────────

    def toggle_broadcast_panel(self) -> None:
        self._page.get_by_test_id("broadcast-toggle").click()

    def fill_broadcast_form(
        self,
        building_name: str,
        subject: str,
        message: str,
    ) -> None:
        self._page.get_by_test_id("broadcast-building").click()
        self._page.get_by_role("option", name=building_name).click()
        self._page.get_by_test_id("broadcast-subject").fill(subject)
        self._page.get_by_test_id("broadcast-message").fill(message)

    def submit_broadcast(self) -> None:
        self._page.get_by_test_id("broadcast-send").click()

    def get_broadcast_status(self) -> str:
        status = self._page.get_by_test_id("broadcast-status")
        try:
            status.wait_for(state="visible", timeout=5_000)
            return status.inner_text().strip()
        except Exception:
            return ""

    def is_broadcast_toggle_visible(self) -> bool:
        try:
            self._page.get_by_test_id("broadcast-toggle").wait_for(
                state="visible", timeout=3_000
            )
            return True
        except Exception:
            return False
