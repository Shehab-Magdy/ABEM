"""
Selenium WebDriver factory.

Supports:
- Chrome / Firefox (local)
- Remote Grid (Selenium Grid / BrowserStack / LambdaTest)
- Headless mode toggle
- Automatic chromedriver / geckodriver installation via webdriver-manager
"""

from __future__ import annotations

import os
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.remote.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from utils.logger import get_logger

logger = get_logger(__name__)


class DriverFactory:
    """Creates configured WebDriver instances."""

    @staticmethod
    def create_driver(
        browser: str = "chrome",
        headless: bool = True,
        remote_url: Optional[str] = None,
        implicit_wait: int = 10,
    ) -> WebDriver:
        """
        Return a ready-to-use WebDriver.

        Args:
            browser:       "chrome" | "firefox"
            headless:      Run without a visible window (default True)
            remote_url:    Selenium Grid hub URL; if set, uses RemoteWebDriver
            implicit_wait: Seconds to wait for elements implicitly
        """
        browser = browser.lower()
        logger.info(
            "Creating %s driver | headless=%s remote=%s",
            browser,
            headless,
            remote_url or "local",
        )

        if remote_url:
            driver = DriverFactory._remote_driver(browser, headless, remote_url)
        elif browser == "chrome":
            driver = DriverFactory._chrome_driver(headless)
        elif browser == "firefox":
            driver = DriverFactory._firefox_driver(headless)
        else:
            raise ValueError(f"Unsupported browser: '{browser}'. Use 'chrome' or 'firefox'.")

        driver.implicitly_wait(implicit_wait)
        driver.maximize_window()
        logger.info("Driver created: session_id=%s", driver.session_id)
        return driver

    # ── Private builders ───────────────────────────────────────────────────────

    @staticmethod
    def _chrome_driver(headless: bool) -> WebDriver:
        opts = ChromeOptions()
        if headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--disable-extensions")
        opts.add_argument("--disable-infobars")
        opts.add_experimental_option("excludeSwitches", ["enable-logging"])
        service = ChromeService(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=opts)

    @staticmethod
    def _firefox_driver(headless: bool) -> WebDriver:
        opts = FirefoxOptions()
        if headless:
            opts.add_argument("--headless")
        opts.add_argument("--width=1920")
        opts.add_argument("--height=1080")
        service = FirefoxService(GeckoDriverManager().install())
        return webdriver.Firefox(service=service, options=opts)

    @staticmethod
    def _remote_driver(browser: str, headless: bool, remote_url: str) -> WebDriver:
        if browser == "chrome":
            opts = ChromeOptions()
            if headless:
                opts.add_argument("--headless=new")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
        elif browser == "firefox":
            opts = FirefoxOptions()
            if headless:
                opts.add_argument("--headless")
        else:
            raise ValueError(f"Unsupported remote browser: '{browser}'")

        return webdriver.Remote(
            command_executor=remote_url,
            options=opts,
        )
