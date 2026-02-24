"""
Base Page Object for Selenium web tests.

All web page objects inherit from this class.

NOTE: For the most robust and maintainable selectors, add `data-testid`
attributes to React components. Example:
    <input data-testid="email-input" ... />
Then locate with: By.CSS_SELECTOR, "[data-testid='email-input']"
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from utils.logger import get_logger

logger = get_logger(__name__)


class BasePage:
    """Wraps Selenium's raw API with explicit waits and helpful utilities."""

    def __init__(self, driver: WebDriver, timeout: int = 15):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)
        self.actions = ActionChains(driver)

    # ── Navigation ─────────────────────────────────────────────────────────────

    def open(self, url: str) -> None:
        logger.debug("Navigating to %s", url)
        self.driver.get(url)

    def get_current_url(self) -> str:
        return self.driver.current_url

    def get_page_title(self) -> str:
        return self.driver.title

    # ── Element interactions ───────────────────────────────────────────────────

    def find(self, locator: Tuple[str, str]) -> WebElement:
        """Wait for element presence and return it."""
        return self.wait.until(EC.presence_of_element_located(locator))

    def find_all(self, locator: Tuple[str, str]) -> List[WebElement]:
        """Return all matching elements (waits for at least one)."""
        self.wait.until(EC.presence_of_element_located(locator))
        return self.driver.find_elements(*locator)

    def click(self, locator: Tuple[str, str]) -> None:
        el = self.wait.until(EC.element_to_be_clickable(locator))
        logger.debug("Click → %s", locator)
        el.click()

    def type_text(self, locator: Tuple[str, str], text: str, clear: bool = True) -> None:
        el = self.find(locator)
        if clear:
            el.clear()
        el.send_keys(text)
        logger.debug("Type '%s' → %s", text[:20] if len(text) > 20 else text, locator)

    def clear_field(self, locator: Tuple[str, str]) -> None:
        el = self.find(locator)
        el.send_keys(Keys.CONTROL + "a")
        el.send_keys(Keys.DELETE)

    def get_text(self, locator: Tuple[str, str]) -> str:
        return self.find(locator).text

    def get_attribute(self, locator: Tuple[str, str], attr: str) -> Optional[str]:
        return self.find(locator).get_attribute(attr)

    # ── Visibility checks ──────────────────────────────────────────────────────

    def is_visible(self, locator: Tuple[str, str], timeout: int = 5) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False

    def is_present(self, locator: Tuple[str, str], timeout: int = 3) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False

    def wait_until_visible(self, locator: Tuple[str, str], timeout: Optional[int] = None) -> WebElement:
        t = timeout or self.timeout
        return WebDriverWait(self.driver, t).until(
            EC.visibility_of_element_located(locator)
        )

    def wait_until_invisible(self, locator: Tuple[str, str], timeout: Optional[int] = None) -> bool:
        t = timeout or self.timeout
        return WebDriverWait(self.driver, t).until(
            EC.invisibility_of_element_located(locator)
        )

    def wait_for_url_contains(self, partial_url: str, timeout: Optional[int] = None) -> bool:
        t = timeout or self.timeout
        return WebDriverWait(self.driver, t).until(EC.url_contains(partial_url))

    # ── Screenshots ────────────────────────────────────────────────────────────

    def screenshot(self, name: str = "screenshot") -> str:
        Path("screenshots").mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"screenshots/{name}_{ts}.png"
        self.driver.save_screenshot(path)
        logger.debug("Screenshot → %s", path)
        return path

    # ── JavaScript helpers ─────────────────────────────────────────────────────

    def scroll_to(self, locator: Tuple[str, str]) -> None:
        el = self.find(locator)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", el)
        time.sleep(0.3)

    def js_click(self, locator: Tuple[str, str]) -> None:
        el = self.find(locator)
        self.driver.execute_script("arguments[0].click();", el)
