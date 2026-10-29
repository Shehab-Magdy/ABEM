"""Base Page Object — shared navigation, wait, and utility methods."""

from __future__ import annotations

from playwright.sync_api import Page, expect


class BasePage:
    """Abstract base for all page objects."""

    URL: str = "/"

    def __init__(self, page: Page) -> None:
        self._page = page

    # ── Navigation ────────────────────────────────────────────

    def navigate(self) -> None:
        """Navigate to this page's URL."""
        from config.settings import settings
        self._page.goto(f"{settings.BASE_URL}{self.URL}")

    def wait_for_load(self) -> None:
        """Wait for the page's key element to be visible.

        Subclasses should override this with a page-specific wait.
        """
        self._page.wait_for_load_state("networkidle")

    def navigate_and_wait(self) -> None:
        """Navigate and then wait for full load."""
        self.navigate()
        self.wait_for_load()

    # ── State readers ─────────────────────────────────────────

    def get_page_title(self) -> str:
        """Return the document title."""
        return self._page.title()

    def get_current_url(self) -> str:
        """Return the current URL."""
        return self._page.url

    def get_toast_message(self) -> str:
        """Read the text of a MUI Snackbar / Alert toast."""
        toast = self._page.locator("[role='alert']").first
        toast.wait_for(state="visible", timeout=5_000)
        return toast.inner_text()

    def is_element_visible(self, selector: str, timeout: int = 3_000) -> bool:
        """Check if a CSS-selected element is visible."""
        try:
            self._page.locator(selector).wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def is_button_visible(self, label: str) -> bool:
        """Check if a button with the given label is visible."""
        try:
            btn = self._page.get_by_role("button", name=label)
            btn.wait_for(state="visible", timeout=3_000)
            return True
        except Exception:
            return False

    # ── Actions ───────────────────────────────────────────────

    def click_button(self, label: str) -> None:
        """Click a button identified by role + name."""
        self._page.get_by_role("button", name=label).click()

    def click_link(self, label: str) -> None:
        """Click a link identified by role + name."""
        self._page.get_by_role("link", name=label).click()

    # ── Table helpers ─────────────────────────────────────────

    def get_table_row_count(self, table_selector: str = "table tbody tr") -> int:
        """Return the number of rows in a table."""
        return self._page.locator(table_selector).count()

    def get_table_headers(self, table_selector: str = "table") -> list[str]:
        """Return the text of all <th> elements in a table."""
        headers = self._page.locator(f"{table_selector} th").all()
        return [h.inner_text().strip() for h in headers]

    # ── Loading & empty states ────────────────────────────────

    def is_loading(self) -> bool:
        """Check if a loading spinner (CircularProgress) is visible."""
        return self._page.locator("[role='progressbar']").is_visible()

    def get_empty_state_text(self) -> str:
        """Read empty-state message text."""
        el = self._page.get_by_test_id("empty-state")
        el.wait_for(state="visible", timeout=5_000)
        return el.inner_text()

    # ── Screenshot ────────────────────────────────────────────

    def screenshot(self, path: str) -> None:
        """Take a full-page screenshot."""
        self._page.screenshot(path=path, full_page=True)
