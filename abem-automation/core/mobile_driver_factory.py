"""
Appium WebDriver factory for the ABEM Flutter mobile app.

Supports:
- Android (UiAutomator2)
- iOS (XCUITest)
- Local Appium server + remote Appium grid
- No-reset mode for faster repeated test runs

Prerequisites:
    pip install Appium-Python-Client
    Appium server running: appium --relaxed-security
"""

from __future__ import annotations

from typing import Optional

from appium import webdriver as appium_webdriver
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions

from utils.logger import get_logger

logger = get_logger(__name__)


class MobileDriverFactory:
    """Creates Appium WebDriver instances for Android or iOS."""

    @staticmethod
    def create_driver(mobile_cfg) -> appium_webdriver.Remote:
        """
        Build and return an Appium driver.

        Args:
            mobile_cfg: MobileConfig dataclass (from config.settings)

        Returns:
            appium_webdriver.Remote — ready for use
        """
        platform = mobile_cfg.platform_name.lower()
        logger.info(
            "Creating %s Appium driver | device=%s appium=%s",
            platform,
            mobile_cfg.device_name,
            mobile_cfg.appium_url,
        )

        if platform == "android":
            return MobileDriverFactory._android_driver(mobile_cfg)
        elif platform == "ios":
            return MobileDriverFactory._ios_driver(mobile_cfg)
        else:
            raise ValueError(
                f"Unsupported platform: '{mobile_cfg.platform_name}'. "
                "Use 'Android' or 'iOS'."
            )

    # ── Android ────────────────────────────────────────────────────────────────

    @staticmethod
    def _android_driver(cfg) -> appium_webdriver.Remote:
        options = UiAutomator2Options()
        options.device_name = cfg.device_name
        options.platform_version = cfg.platform_version
        options.app_package = cfg.app_package
        options.app_activity = cfg.app_activity
        options.no_reset = cfg.no_reset
        options.set_capability("autoGrantPermissions", True)
        options.set_capability("newCommandTimeout", 300)

        driver = appium_webdriver.Remote(
            command_executor=cfg.appium_url,
            options=options,
        )
        logger.info("Android driver created: session_id=%s", driver.session_id)
        return driver

    # ── iOS ────────────────────────────────────────────────────────────────────

    @staticmethod
    def _ios_driver(cfg) -> appium_webdriver.Remote:
        options = XCUITestOptions()
        options.device_name = cfg.device_name
        options.platform_version = cfg.platform_version
        options.bundle_id = cfg.app_package
        options.no_reset = cfg.no_reset
        options.set_capability("newCommandTimeout", 300)

        driver = appium_webdriver.Remote(
            command_executor=cfg.appium_url,
            options=options,
        )
        logger.info("iOS driver created: session_id=%s", driver.session_id)
        return driver
