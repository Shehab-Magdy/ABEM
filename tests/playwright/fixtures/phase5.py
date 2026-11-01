"""Fixtures shared by the Phase 5 api / ui / e2e tests.

Kept out of the root conftest.py on purpose: the subfolder conftests import what they need from here.
"""

from __future__ import annotations

import logging
from decimal import Decimal

import pytest
from playwright.sync_api import APIRequestContext, Browser, Playwright

from config.settings import settings
from pw_config import (
    DEFAULT_TIMEOUT,
    LOCALE,
    NAVIGATION_TIMEOUT,
    TIMEZONE_ID,
    VIEWPORT_HEIGHT,
    VIEWPORT_WIDTH,
)
from utils.data_factory import build_payment

logger = logging.getLogger(__name__)

API = "/api/v1"


def unwrap(body):
    """Return the list of rows from a paginated or plain list response."""
    return body.get("results", body) if isinstance(body, dict) else body


def goto(page, path: str) -> None:
    """Open an app path on the frontend (the suite's pages have no base_url)."""
    page.goto(f"{settings.BASE_URL}{path}")


def errors(resp) -> dict:
    """Field errors of a 400 response; the API wraps them as {"status","code","errors":{field: [...]}}."""
    body = resp.json()
    return body.get("errors", body) if isinstance(body, dict) else {}


def money(value) -> Decimal:
    return Decimal(str(value))


def apartment_balance(api: APIRequestContext, apartment_id: str) -> Decimal:
    resp = api.get(f"{API}/apartments/{apartment_id}/")
    assert resp.status == 200, resp.text()
    return money(resp.json()["balance"])


def login_tokens(playwright: Playwright, email: str, password: str) -> dict:
    ctx = playwright.request.new_context(base_url=settings.API_BASE_URL)
    try:
        resp = ctx.post(f"{API}/auth/login/", data={"email": email, "password": password})
        assert resp.status == 200, f"Login failed for {email} ({resp.status}): {resp.text()}"
        return resp.json()
    finally:
        ctx.dispose()


def bearer_context(playwright: Playwright, access: str) -> APIRequestContext:
    return playwright.request.new_context(
        base_url=settings.API_BASE_URL,
        extra_http_headers={"Authorization": f"Bearer {access}", "Content-Type": "application/json"},
    )


@pytest.fixture(scope="function")
def billed_unit(admin_api: APIRequestContext, seeded_expense: dict) -> dict:
    """A building with one billed expense; nothing paid yet. Keys: building, apartment, expense."""
    if seeded_expense.get("apartment") is None:
        pytest.skip("Seeded building has no apartment")
    return seeded_expense


@pytest.fixture(scope="function")
def reversible_payment(admin_api: APIRequestContext, billed_unit: dict) -> dict:
    """A recorded payment on a billed unit plus the unit balance before and after it.

    Keys: payment, apartment, expense, building, balance_before, balance_after.
    """
    apt_id = billed_unit["apartment"]["id"]
    before = apartment_balance(admin_api, apt_id)
    resp = admin_api.post(
        f"{API}/payments/",
        data=build_payment(
            apt_id, amount_paid="20", payment_method="cash", expense_ids=[billed_unit["expense"]["id"]]
        ),
    )
    assert resp.status == 201, resp.text()
    return {
        "payment": resp.json(),
        "apartment": billed_unit["apartment"],
        "expense": billed_unit["expense"],
        "building": billed_unit["building"],
        "balance_before": before,
        "balance_after": apartment_balance(admin_api, apt_id),
    }


@pytest.fixture(scope="function")
def member_owner(playwright: Playwright, admin_api: APIRequestContext, billed_unit: dict, create_user) -> dict:
    """An owner who is a member of the billed building and owns its apartment, signed in over the API.

    Keys: user, password, api (APIRequestContext as that owner), building, apartment, expense.
    """
    owner = create_user(role="owner")
    building_id = billed_unit["building"]["id"]
    resp = admin_api.post(f"{API}/buildings/{building_id}/assign-user/", data={"user_id": owner["id"]})
    assert resp.status in (200, 201), resp.text()
    tokens = login_tokens(playwright, owner["email"], owner["_password"])
    ctx = bearer_context(playwright, tokens["access"])
    yield {
        "user": owner,
        "password": owner["_password"],
        "api": ctx,
        "building": billed_unit["building"],
        "apartment": billed_unit["apartment"],
        "expense": billed_unit["expense"],
    }
    ctx.dispose()


@pytest.fixture(scope="function")
def raw_admin_page(playwright_browser: Browser):
    """Admin page signed in through the login form WITHOUT the suite's forced-English init script.

    For language switch / persistence tests. The only seeding is "start in English if nothing is saved yet", so a
    language saved by the app (localStorage or the profile) is honoured across reloads. Signing in fresh avoids
    depending on a possibly expired shared storage state.
    """
    context = playwright_browser.new_context(
        viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
        locale=LOCALE,
        timezone_id=TIMEZONE_ID,
    )
    context.add_init_script(
        "try { if (!localStorage.getItem('abem_language')) localStorage.setItem('abem_language', 'en'); } catch (e) {}"
    )
    context.set_default_timeout(DEFAULT_TIMEOUT)
    context.set_default_navigation_timeout(NAVIGATION_TIMEOUT)
    pg = context.new_page()
    pg.goto(f"{settings.BASE_URL}/login")
    pg.get_by_label("Email address").fill(settings.ADMIN_EMAIL)
    pg.get_by_label("Password", exact=True).fill(settings.ADMIN_PASSWORD)
    pg.get_by_role("button", name="Sign in").click()
    pg.wait_for_url("**/dashboard**", timeout=15_000)
    yield pg
    pg.close()
    context.close()


@pytest.fixture(scope="function")
def member_owner_page(playwright_browser: Browser, member_owner: dict):
    """Browser page signed in through the login form as the member_owner (English UI)."""
    context = playwright_browser.new_context(
        viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
        locale=LOCALE,
        timezone_id=TIMEZONE_ID,
    )
    context.add_init_script("try { localStorage.setItem('abem_language', 'en'); } catch (e) {}")
    context.set_default_timeout(DEFAULT_TIMEOUT)
    context.set_default_navigation_timeout(NAVIGATION_TIMEOUT)
    pg = context.new_page()
    pg.goto(f"{settings.BASE_URL}/login")
    pg.get_by_label("Email address").fill(member_owner["user"]["email"])
    pg.get_by_label("Password", exact=True).fill(member_owner["password"])
    pg.get_by_role("button", name="Sign in").click()
    pg.wait_for_url("**/dashboard**", timeout=15_000)
    yield pg
    pg.close()
    context.close()
