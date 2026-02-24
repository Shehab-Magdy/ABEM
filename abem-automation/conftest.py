"""
Root conftest.py — session and function-scoped fixtures shared across all tests.

Fixture tree:
  env_config          (session)  – parsed Config from environments.yaml
  ├── admin_api        (session)  – authenticated APIClient (admin role)
  ├── owner_api        (function) – fresh authenticated APIClient (owner role)
  └── unauthenticated_api (function) – bare APIClient, no token
  web_driver           (function) – Selenium WebDriver (Chrome/Firefox)
  mobile_driver        (session)  – Appium driver (re-used across mobile tests)

Cleanup strategy:
  - owner_api creates a transient owner user and deletes it in teardown
  - web_driver quits after each test
  - mobile_driver is session-scoped (Appium sessions are expensive)
"""

from __future__ import annotations

import pytest
from typing import Generator

from config.settings import get_config, Config
from core.api_client import APIClient
from core.driver_factory import DriverFactory
from core.mobile_driver_factory import MobileDriverFactory
from api.auth_api import AuthAPI
from api.user_api import UserAPI
from utils.logger import get_logger
from utils.test_data import UserFactory

logger = get_logger("conftest")


# ── Hooks ──────────────────────────────────────────────────────────────────────

def pytest_configure(config):
    """Register custom markers so pytest doesn't warn about unknown ones."""
    config.addinivalue_line("markers", "web:      Web UI tests (requires browser)")
    config.addinivalue_line("markers", "api:      REST API tests")
    config.addinivalue_line("markers", "mobile:   Mobile tests (requires Appium)")
    config.addinivalue_line("markers", "smoke:    Smoke tests")
    config.addinivalue_line("markers", "sprint_0: Sprint 0 infrastructure tests")
    config.addinivalue_line("markers", "sprint_1: Sprint 1 auth & user tests")
    config.addinivalue_line("markers", "positive: Happy-path test cases")
    config.addinivalue_line("markers", "negative: Edge-case / error-path test cases")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Attach the test result to the request object so teardown can read it."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


# ── Environment / Config ───────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def env_config() -> Config:
    cfg = get_config()
    logger.info(
        "Test environment: %s | api=%s | web=%s",
        cfg.environment,
        cfg.api_url,
        cfg.base_url,
    )
    return cfg


# ── API Clients ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def admin_api(env_config: Config) -> Generator[APIClient, None, None]:
    """
    Session-scoped authenticated admin client.
    Shared across all tests — do NOT mutate state (password, email) in tests.
    """
    client = APIClient(env_config.api_url)
    client.authenticate(env_config.admin_email, env_config.admin_password)
    yield client
    client.logout()


@pytest.fixture(scope="function")
def owner_api(env_config: Config, admin_api: APIClient) -> Generator[APIClient, None, None]:
    """
    Function-scoped owner client backed by a freshly-created owner user.
    The user is deleted after the test to keep the DB clean.
    """
    user_data = UserFactory.owner()
    admin_user_api = UserAPI(admin_api)
    auth_api = AuthAPI(admin_api)

    # Create via admin
    resp = auth_api.register(**{k: user_data[k] for k in ["email", "password", "first_name", "last_name", "role"]})
    assert resp.status_code == 201, f"Could not create owner for fixture: {resp.text}"
    created_user = resp.json()
    user_id = created_user["id"]

    # Authenticate as the new owner
    client = APIClient(env_config.api_url)
    client.authenticate(user_data["email"], user_data["password"])

    yield client

    # Teardown: logout and delete via admin
    client.logout()
    admin_user_api.delete_user(user_id)


@pytest.fixture(scope="function")
def unauthenticated_api(env_config: Config) -> APIClient:
    """Bare APIClient with no token — for negative auth tests."""
    return APIClient(env_config.api_url)


# ── Transient user helper ──────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def create_temp_user(admin_api: APIClient, env_config: Config):
    """
    Factory fixture: call it inside a test to create a temporary owner.
    All users created through this fixture are deleted after the test.

    Usage:
        def test_something(create_temp_user):
            user = create_temp_user(role="owner")
            # user["id"], user["email"], user["password"] are available
    """
    created_ids: list[str] = []
    admin_user_api = UserAPI(admin_api)
    admin_auth_api = AuthAPI(admin_api)

    def _create(role: str = "owner", **overrides) -> dict:
        data = UserFactory.owner() if role == "owner" else UserFactory.admin()
        data.update(overrides)
        resp = admin_auth_api.register(**{k: data[k] for k in ["email", "password", "first_name", "last_name", "role"]})
        assert resp.status_code == 201, f"temp user creation failed: {resp.text}"
        user = resp.json()
        user["password"] = data["password"]  # attach plaintext for auth
        created_ids.append(user["id"])
        return user

    yield _create

    for uid in created_ids:
        try:
            admin_user_api.delete_user(uid)
        except Exception as e:
            logger.warning("Could not delete temp user %s: %s", uid, e)


# ── Web Driver ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def web_driver(env_config: Config, request):
    """
    Function-scoped Selenium WebDriver.
    Captures a screenshot on test failure before quitting.
    """
    import os

    browser = os.environ.get("BROWSER", env_config.browser)
    headless_env = os.environ.get("HEADLESS", "").lower()
    headless = (headless_env == "true") if headless_env else env_config.headless
    remote_url = os.environ.get("SELENIUM_REMOTE_URL")

    driver = DriverFactory.create_driver(
        browser=browser,
        headless=headless,
        remote_url=remote_url or None,
        implicit_wait=env_config.implicit_wait,
    )

    yield driver

    # Screenshot on failure
    rep = getattr(request.node, "rep_call", None)
    if rep and rep.failed:
        from datetime import datetime
        from pathlib import Path

        Path("screenshots").mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = request.node.name.replace("/", "_").replace(":", "_")
        path = f"screenshots/FAIL_{safe_name}_{ts}.png"
        try:
            driver.save_screenshot(path)
            logger.warning("Failure screenshot → %s", path)
        except Exception as exc:
            logger.error("Screenshot capture failed: %s", exc)

    driver.quit()


# ── Mobile Driver ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def mobile_driver(env_config: Config):
    """
    Session-scoped Appium driver.
    Re-used across all mobile tests to avoid expensive session creation per test.
    Skip automatically if Appium is not configured.
    """
    import os
    import socket

    # Check if Appium server is reachable before creating driver
    appium_url = env_config.mobile.appium_url
    host = appium_url.split("//")[-1].split(":")[0]
    port = int(appium_url.split(":")[-1].split("/")[0])

    try:
        sock = socket.create_connection((host, port), timeout=2)
        sock.close()
    except OSError:
        pytest.skip(f"Appium server not reachable at {appium_url} — skipping mobile tests")

    driver = MobileDriverFactory.create_driver(env_config.mobile)
    yield driver
    driver.quit()
