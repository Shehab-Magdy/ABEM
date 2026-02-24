"""
Base Mobile Page Object for Appium tests.

All mobile page objects inherit from this class.

Flutter-rendered apps on Android are best targeted with:
- accessibility_id  (set via Semantics widget's `label` in Flutter)
- xpath             (for complex hierarchies)
- resource-id       (Android-specific View IDs)

For the ABEM Flutter app, ensure key widgets have Semantics labels:
    Semantics(label: 'email-input', child: TextFormField(...))
"""

from __future__ import annotations

import time
from typing import List, Optional, Tuple

from appium.webdriver.common.appiumby import AppiumBy
from appium.webdriver.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from utils.logger import get_logger

logger = get_logger(__name__)


class BaseMobilePage:
    """Wraps Appium's raw API with explicit waits and Flutter-friendly helpers."""

    def __init__(self, driver: WebDriver, timeout: int = 15):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)

    # ── Element finders ────────────────────────────────────────────────────────

    def find_by_accessibility_id(self, label: str):
        return self.wait.until(
            EC.presence_of_element_located((AppiumBy.ACCESSIBILITY_ID, label))
        )

    def find_by_xpath(self, xpath: str):
        return self.wait.until(
            EC.presence_of_element_located((AppiumBy.XPATH, xpath))
        )

    def find_by_text(self, text: str):
        return self.find_by_xpath(
            f"//*[@text='{text}' or @content-desc='{text}' or @label='{text}']"
        )

    def find_by_resource_id(self, resource_id: str):
        return self.wait.until(
            EC.presence_of_element_located((AppiumBy.ID, resource_id))
        )

    # ── Interactions ───────────────────────────────────────────────────────────

    def tap(self, label: str) -> None:
        logger.debug("Tap → '%s'", label)
        self.find_by_accessibility_id(label).click()

    def tap_by_text(self, text: str) -> None:
        logger.debug("Tap text → '%s'", text)
        self.find_by_text(text).click()

    def type_into(self, label: str, text: str, clear: bool = True) -> None:
        el = self.find_by_accessibility_id(label)
        if clear:
            el.clear()
        el.send_keys(text)
        logger.debug("Type '%s' → '%s'", text[:20], label)

    def get_text(self, label: str) -> str:
        return self.find_by_accessibility_id(label).text

    def get_text_by_xpath(self, xpath: str) -> str:
        return self.find_by_xpath(xpath).text

    # ── Visibility ─────────────────────────────────────────────────────────────

    def is_visible(self, label: str, timeout: int = 5) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((AppiumBy.ACCESSIBILITY_ID, label))
            )
            return True
        except TimeoutException:
            return False

    def is_text_visible(self, text: str, timeout: int = 5) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(
                    (AppiumBy.XPATH, f"//*[@text='{text}' or contains(@content-desc,'{text}')]")
                )
            )
            return True
        except TimeoutException:
            return False

    def wait_for(self, label: str, timeout: Optional[int] = None) -> None:
        t = timeout or self.timeout
        WebDriverWait(self.driver, t).until(
            EC.presence_of_element_located((AppiumBy.ACCESSIBILITY_ID, label))
        )

    # ── Device helpers ─────────────────────────────────────────────────────────

    def press_back(self) -> None:
        self.driver.back()

    def hide_keyboard(self) -> None:
        try:
            self.driver.hide_keyboard()
        except Exception:
            pass  # keyboard may already be hidden

    def dismiss_alert(self) -> None:
        try:
            self.driver.switch_to.alert.dismiss()
        except Exception:
            pass

    def scroll_down(self) -> None:
        size = self.driver.get_window_size()
        start_x = size["width"] // 2
        start_y = int(size["height"] * 0.8)
        end_y = int(size["height"] * 0.2)
        self.driver.swipe(start_x, start_y, start_x, end_y, duration=600)

    def screenshot(self, name: str = "mobile") -> str:
        from datetime import datetime
        from pathlib import Path

        Path("screenshots").mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"screenshots/{name}_{ts}.png"
        self.driver.save_screenshot(path)
        return path
