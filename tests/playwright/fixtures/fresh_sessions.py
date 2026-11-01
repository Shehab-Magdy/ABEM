"""Per-test signed-in pages that log in through the form instead of replaying one shared storage state.

Why: the app rotates refresh tokens. The suite used to save one logged-in storage state per run and replay it in every
test; once the access token expired, the first test to refresh used the saved refresh token up, every later test was
bounced to /login, and long runs failed more and more. A fresh login per test has no such cross-test state.

Loaded by tests/ui/conftest.py and tests/e2e/conftest.py, which overrides the root conftest's admin_page / owner_page
for those folders (the root conftest.py itself is untouched).
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Browser, Page

from config.settings import settings
from pw_config import (
    DEFAULT_TIMEOUT,
    LOCALE,
    NAVIGATION_TIMEOUT,
    TIMEZONE_ID,
    VIEWPORT_HEIGHT,
    VIEWPORT_WIDTH,
)

ENGLISH_UI = "try { localStorage.setItem('abem_language', 'en'); } catch (e) {}"


def _signed_in(browser: Browser, email: str, password: str):
    context = browser.new_context(
        viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT}, locale=LOCALE, timezone_id=TIMEZONE_ID
    )
    context.add_init_script(ENGLISH_UI)
    context.set_default_timeout(DEFAULT_TIMEOUT)
    context.set_default_navigation_timeout(NAVIGATION_TIMEOUT)
    page = context.new_page()
    page.goto(f"{settings.BASE_URL}/login")
    page.get_by_label("Email address").fill(email)
    page.get_by_label("Password", exact=True).fill(password)
    page.get_by_role("button", name="Sign in").click()
    page.wait_for_url("**/dashboard**", timeout=15_000)
    return context, page


@pytest.fixture(scope="function")
def admin_page(playwright_browser: Browser) -> Page:
    context, page = _signed_in(playwright_browser, settings.ADMIN_EMAIL, settings.ADMIN_PASSWORD)
    yield page
    context.close()


@pytest.fixture(scope="function")
def owner_page(playwright_browser: Browser) -> Page:
    context, page = _signed_in(playwright_browser, settings.OWNER_EMAIL, settings.OWNER_PASSWORD)
    yield page
    context.close()
