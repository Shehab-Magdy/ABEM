"""Plan page (/plan): tiers with the yearly discount."""

from __future__ import annotations

import re

from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class PlanPage(BasePage):
    URL = "/plan"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def wait_for_load(self) -> None:
        self._page.get_by_role("button", name="Yearly", exact=True).wait_for(state="visible")
        self._page.get_by_text(re.compile(r"Save \d+%|وفّر")).first.wait_for(state="visible")

    def choose_period(self, label: str) -> None:
        self._page.get_by_role("button", name=label, exact=True).click()

    def saving_chips(self) -> Locator:
        return self._page.locator(".MuiChip-root").filter(has_text=re.compile(r"^Save \d+%$"))

    def monthly_hints(self) -> Locator:
        return self._page.get_by_text(re.compile(r"Save \d+% with the yearly plan"))

    def line_through_elements(self) -> list[str]:
        """Texts of elements whose computed text-decoration is line-through."""
        return self._page.evaluate(
            """() => [...document.querySelectorAll('p,span')]
                .filter(e => getComputedStyle(e).textDecorationLine === 'line-through')
                .map(e => e.textContent.trim())"""
        )

    def displayed_percent(self) -> int:
        text = self.saving_chips().first.inner_text()
        return int(re.search(r"(\d+)", text).group(1))
