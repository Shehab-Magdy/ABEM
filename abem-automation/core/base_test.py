"""
Base test class providing shared setup/teardown hooks for all test types.

Every test class should extend BaseTest (or one of its sub-classes).
pytest fixtures defined in conftest.py are preferred for injection, but this
class gives a convenient place for instance-level state and helper methods.
"""

from __future__ import annotations

import pytest
from utils.logger import get_logger


class BaseTest:
    """
    Lightweight base for all ABEM test classes.

    Provides:
    - Per-test logger with the test class name
    - Failure hooks for screenshots / logs
    """

    logger = None  # set per-instance in setup

    def setup_method(self, method):
        self.logger = get_logger(
            f"{self.__class__.__name__}.{method.__name__}"
        )
        self.logger.info("▶ START %s", method.__name__)

    def teardown_method(self, method):
        self.logger.info("■ END   %s", method.__name__)


class BaseWebTest(BaseTest):
    """
    Base class for Selenium web tests.

    Extend and accept `web_driver` as a fixture argument in your test class:

        class TestLogin(BaseWebTest):
            def test_something(self, web_driver, env_config):
                self.driver = web_driver
                ...
    """

    driver = None  # set by test method or conftest autouse fixture

    def teardown_method(self, method):
        if self.driver and hasattr(self, "_request") and self._request.node.rep_call.failed:
            self._take_failure_screenshot(method.__name__)
        super().teardown_method(method)

    def _take_failure_screenshot(self, test_name: str) -> None:
        from datetime import datetime
        from pathlib import Path

        Path("screenshots").mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"screenshots/{test_name}_{ts}.png"
        try:
            self.driver.save_screenshot(path)
            self.logger.warning("Screenshot saved → %s", path)
        except Exception as exc:
            self.logger.error("Could not save screenshot: %s", exc)


class BaseAPITest(BaseTest):
    """
    Base class for API (requests-based) tests.

    Test classes receive the authenticated `admin_api` or `owner_api` clients
    via fixtures in conftest.py. This base only provides the logger.
    """


class BaseMobileTest(BaseTest):
    """
    Base class for Appium mobile tests.

    Accept `mobile_driver` as a fixture argument in each test method.
    """

    driver = None  # set by test method

    def teardown_method(self, method):
        if self.driver:
            try:
                # Capture a screenshot on every mobile teardown for audit
                from datetime import datetime
                from pathlib import Path

                Path("screenshots").mkdir(exist_ok=True)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                path = f"screenshots/mobile_{method.__name__}_{ts}.png"
                self.driver.save_screenshot(path)
            except Exception:
                pass
        super().teardown_method(method)
