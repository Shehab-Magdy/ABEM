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
from appium.options import AppiumOptions

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
        options = AppiumOptions()
        options.platform_name = "Android"
        options.set_capability("deviceName", cfg.device_name)
        options.set_capability("platformVersion", cfg.platform_version)
        options.set_capability("appPackage", cfg.app_package)
        options.set_capability("appActivity", cfg.app_activity)
        options.set_capability("automationName", cfg.automation_name)
        options.set_capability("noReset", cfg.no_reset)
        options.set_capability("autoGrantPermissions", True)
        # Flutter-specific driver for native element access
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
        options = AppiumOptions()
        options.platform_name = "iOS"
        options.set_capability("deviceName", cfg.device_name)
        options.set_capability("platformVersion", cfg.platform_version)
        options.set_capability("bundleId", cfg.app_package)  # iOS uses bundleId
        options.set_capability("automationName", "XCUITest")
        options.set_capability("noReset", cfg.no_reset)
        options.set_capability("newCommandTimeout", 300)

        driver = appium_webdriver.Remote(
            command_executor=cfg.appium_url,
            options=options,
        )
        logger.info("iOS driver created: session_id=%s", driver.session_id)
        return driver
