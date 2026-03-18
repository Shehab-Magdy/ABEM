"""Root conftest.py — central fixture hub for the ABEM Playwright framework.

Registers all fixtures from the fixtures/ package and provides
browser, page, API context, and data-seeding fixtures.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
from playwright.sync_api import (
    APIRequestContext,
    Browser,
    BrowserContext,
    Page,
    Playwright,
)

from config.settings import settings
from pw_config import (
    ADMIN_STORAGE_STATE,
    DEFAULT_TIMEOUT,
    EXPECT_TIMEOUT,
    HEADLESS,
    LOCALE,
    NAVIGATION_TIMEOUT,
    OWNER_STORAGE_STATE,
    SCREENSHOT_ON_FAILURE,
    SLOW_MO,
    TIMEZONE_ID,
    VIEWPORT_HEIGHT,
    VIEWPORT_WIDTH,
)

# ── Re-export all fixture modules so pytest discovers them ────
from fixtures.auth import *  # noqa: F401, F403
from fixtures.buildings import *  # noqa: F401, F403
from fixtures.categories import *  # noqa: F401, F403
from fixtures.db import *  # noqa: F401, F403
from fixtures.expenses import *  # noqa: F401, F403
from fixtures.file_uploads import *  # noqa: F401, F403
from fixtures.payments import *  # noqa: F401, F403
from fixtures.users import *  # noqa: F401, F403

logger = logging.getLogger(__name__)


# ── pytest hooks ──────────────────────────────────────────────


def pytest_configure(config):
    """Ensure reports directory exists."""
    os.makedirs("reports", exist_ok=True)
    os.makedirs("tmp", exist_ok=True)


# ── Browser fixtures ──────────────────────────────────────────


@pytest.fixture(scope="session")
def playwright_browser(playwright: Playwright) -> Browser:
    """Session-scoped Chromium browser instance."""
    browser = playwright.chromium.launch(
        headless=HEADLESS,
        slow_mo=SLOW_MO,
    )
    logger.info("Launched Chromium (headless=%s, slow_mo=%s)", HEADLESS, SLOW_MO)
    yield browser
    browser.close()


@pytest.fixture(scope="function")
def browser_context(playwright_browser: Browser) -> BrowserContext:
    """Function-scoped browser context — fresh cookies/storage per test."""
    context = playwright_browser.new_context(
        viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
        locale=LOCALE,
        timezone_id=TIMEZONE_ID,
    )
    context.set_default_timeout(DEFAULT_TIMEOUT)
    context.set_default_navigation_timeout(NAVIGATION_TIMEOUT)
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(browser_context: BrowserContext) -> Page:
    """Function-scoped page from browser_context."""
    pg = browser_context.new_page()
    yield pg
    pg.close()


# ── API context fixtures ─────────────────────────────────────


@pytest.fixture(scope="function")
def api_context(playwright: Playwright) -> APIRequestContext:
    """Function-scoped APIRequestContext pointed at API_BASE_URL."""
    ctx = playwright.request.new_context(
        base_url=settings.API_BASE_URL,
        extra_http_headers={"Content-Type": "application/json"},
    )
    yield ctx
    ctx.dispose()


# ── Authenticated page fixtures ──────────────────────────────

_admin_state_ready = False
_owner_state_ready = False


def _ensure_admin_storage_state(playwright: Playwright, browser: Browser) -> str:
    """Perform admin login via browser and save storage state."""
    global _admin_state_ready
    if _admin_state_ready and Path(ADMIN_STORAGE_STATE).exists():
        return ADMIN_STORAGE_STATE

    context = browser.new_context(
        viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
        locale=LOCALE,
        timezone_id=TIMEZONE_ID,
    )
    pg = context.new_page()
    pg.goto(f"{settings.BASE_URL}/login")
    pg.get_by_label("Email address").fill(settings.ADMIN_EMAIL)
    pg.get_by_label("Password").fill(settings.ADMIN_PASSWORD)
    pg.get_by_role("button", name="Sign in").click()
    pg.wait_for_url("**/dashboard**", timeout=15_000)
    context.storage_state(path=ADMIN_STORAGE_STATE)
    pg.close()
    context.close()
    _admin_state_ready = True
    logger.info("Admin storage state saved to %s", ADMIN_STORAGE_STATE)
    return ADMIN_STORAGE_STATE


def _ensure_owner_storage_state(playwright: Playwright, browser: Browser) -> str:
    """Perform owner login via browser and save storage state."""
    global _owner_state_ready
    if _owner_state_ready and Path(OWNER_STORAGE_STATE).exists():
        return OWNER_STORAGE_STATE

    context = browser.new_context(
        viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
        locale=LOCALE,
        timezone_id=TIMEZONE_ID,
    )
    pg = context.new_page()
    pg.goto(f"{settings.BASE_URL}/login")
    pg.get_by_label("Email address").fill(settings.OWNER_EMAIL)
    pg.get_by_label("Password").fill(settings.OWNER_PASSWORD)
    pg.get_by_role("button", name="Sign in").click()
    pg.wait_for_url("**/dashboard**", timeout=15_000)
    context.storage_state(path=OWNER_STORAGE_STATE)
    pg.close()
    context.close()
    _owner_state_ready = True
    logger.info("Owner storage state saved to %s", OWNER_STORAGE_STATE)
    return OWNER_STORAGE_STATE


@pytest.fixture(scope="function")
def admin_page(playwright: Playwright, playwright_browser: Browser) -> Page:
    """Function-scoped page already logged in as admin."""
    state_path = _ensure_admin_storage_state(playwright, playwright_browser)
    context = playwright_browser.new_context(
        storage_state=state_path,
        viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
        locale=LOCALE,
        timezone_id=TIMEZONE_ID,
    )
    context.set_default_timeout(DEFAULT_TIMEOUT)
    context.set_default_navigation_timeout(NAVIGATION_TIMEOUT)
    pg = context.new_page()
    yield pg
    pg.close()
    context.close()


@pytest.fixture(scope="function")
def owner_page(playwright: Playwright, playwright_browser: Browser) -> Page:
    """Function-scoped page already logged in as owner."""
    state_path = _ensure_owner_storage_state(playwright, playwright_browser)
    context = playwright_browser.new_context(
        storage_state=state_path,
        viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
        locale=LOCALE,
        timezone_id=TIMEZONE_ID,
    )
    context.set_default_timeout(DEFAULT_TIMEOUT)
    context.set_default_navigation_timeout(NAVIGATION_TIMEOUT)
    pg = context.new_page()
    yield pg
    pg.close()
    context.close()


# ── Unique ID fixture ────────────────────────────────────────


@pytest.fixture(scope="function")
def unique_id():
    """Return a callable that generates unique test data prefixes."""
    def _generate() -> str:
        return f"test_{uuid4().hex[:8]}"
    return _generate
