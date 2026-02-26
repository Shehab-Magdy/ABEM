"""
Root conftest.py — session and function-scoped fixtures shared across all tests.

Fixture tree:
  env_config              (session)  – parsed Config from environments.yaml
  ├── admin_api            (session)  – authenticated APIClient (admin role)
  ├── owner_api            (function) – fresh authenticated APIClient (owner role)
  ├── owner_with_id        (function) – (APIClient, user_id) for Sprint 2 RBAC tests
  └── unauthenticated_api  (function) – bare APIClient, no token
  create_temp_user         (function) – factory: create/delete temporary users
  create_temp_building     (function) – factory: create/delete temporary buildings
  temp_building            (function) – single temporary building
  create_temp_apartment    (function) – factory: create/delete temporary apartments
  temp_apartment           (function) – single temporary apartment in a temp building
  web_driver               (function) – Selenium WebDriver (Chrome/Firefox)
  mobile_driver            (session)  – Appium driver (re-used across mobile tests)

Cleanup strategy:
  - owner_api creates a transient owner user and deletes it in teardown
  - create_temp_building / create_temp_apartment delete all created objects on teardown
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
from api.building_api import BuildingAPI
from api.apartment_api import ApartmentAPI
from api.expense_api import ExpenseAPI
from api.category_api import CategoryAPI
from api.payment_api import PaymentAPI
from api.dashboard_api import DashboardAPI
from api.notification_api import NotificationAPI
from api.audit_api import AuditAPI
from api.exports_api import ExportsAPI
from api.user_api import UserAPI
from utils.logger import get_logger
from utils.test_data import (
    ApartmentFactory,
    BuildingFactory,
    CategoryFactory,
    ExpenseFactory,
    PaymentFactory,
    UserFactory,
)

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
    config.addinivalue_line("markers", "sprint_2: Sprint 2 buildings & apartment management tests")
    config.addinivalue_line("markers", "sprint_3: Sprint 3 expense management tests")
    config.addinivalue_line("markers", "sprint_4: Sprint 4 payment management tests")
    config.addinivalue_line("markers", "sprint_5: Sprint 5 dashboard tests")
    config.addinivalue_line("markers", "sprint_6: Sprint 6 notification system tests")
    config.addinivalue_line("markers", "sprint_7: Sprint 7 Flutter finalization tests")
    config.addinivalue_line("markers", "sprint_8: Sprint 8 audit logs & data exports tests")
    config.addinivalue_line("markers", "sprint_9: Sprint 9 performance & security hardening tests")
    config.addinivalue_line("markers", "sprint_10: Sprint 10 deployment & production smoke tests")
    config.addinivalue_line("markers", "regression: Full regression suite (Sprints 0-10)")
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


# ── Sprint 2: Owner with ID ────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def owner_with_id(env_config: Config, admin_api: APIClient):
    """
    Function-scoped fixture yielding (APIClient, user_id) for an owner user.
    Useful when a test needs to assign an owner to a building and also call
    the API as that owner.

    Teardown: logs out the owner and deletes the user.
    """
    user_data = UserFactory.owner()
    admin_user_api = UserAPI(admin_api)
    admin_auth_api = AuthAPI(admin_api)

    resp = admin_auth_api.register(
        **{k: user_data[k] for k in ["email", "password", "first_name", "last_name", "role"]}
    )
    assert resp.status_code == 201, f"Could not create owner for fixture: {resp.text}"
    created_user = resp.json()
    user_id = created_user["id"]

    client = APIClient(env_config.api_url)
    client.authenticate(user_data["email"], user_data["password"])

    yield client, user_id

    client.logout()
    admin_user_api.delete_user(user_id)


# ── Sprint 2: Building fixtures ────────────────────────────────────────────────

@pytest.fixture(scope="function")
def create_temp_building(admin_api: APIClient):
    """
    Factory fixture: call it to create temporary buildings via admin.
    All buildings created through this fixture are soft-deleted after the test.

    Usage:
        def test_something(create_temp_building):
            building = create_temp_building()
            building = create_temp_building(name="Custom", num_floors=5)
    """
    created_ids: list[str] = []
    building_api = BuildingAPI(admin_api)

    def _create(**overrides) -> dict:
        data = BuildingFactory.valid()
        data.update(overrides)
        resp = building_api.create(**data)
        assert resp.status_code == 201, f"Building creation failed: {resp.text}"
        building = resp.json()
        created_ids.append(building["id"])
        return building

    yield _create

    for bid in created_ids:
        try:
            building_api.delete(bid)
        except Exception as e:
            logger.warning("Could not delete temp building %s: %s", bid, e)


@pytest.fixture(scope="function")
def temp_building(create_temp_building) -> dict:
    """Single temporary building — convenience wrapper around create_temp_building."""
    return create_temp_building()


# ── Sprint 2: Apartment fixtures ───────────────────────────────────────────────

@pytest.fixture(scope="function")
def create_temp_apartment(admin_api: APIClient):
    """
    Factory fixture: call it to create temporary apartments via admin.
    All apartments created through this fixture are hard-deleted after the test.

    Usage:
        def test_something(create_temp_building, create_temp_apartment):
            bld = create_temp_building()
            apt = create_temp_apartment(building_id=bld["id"])
    """
    created_ids: list[str] = []
    apartment_api = ApartmentAPI(admin_api)

    def _create(building_id: str, num_floors: int = 10, **overrides) -> dict:
        data = ApartmentFactory.valid(building_id=building_id, num_floors=num_floors)
        data.update(overrides)
        resp = apartment_api.create(**data)
        assert resp.status_code == 201, f"Apartment creation failed: {resp.text}"
        apartment = resp.json()
        created_ids.append(apartment["id"])
        return apartment

    yield _create

    for aid in created_ids:
        try:
            apartment_api.delete(aid)
        except Exception as e:
            logger.warning("Could not delete temp apartment %s: %s", aid, e)


@pytest.fixture(scope="function")
def temp_apartment(create_temp_building, create_temp_apartment) -> dict:
    """Single temporary apartment inside a fresh building."""
    building = create_temp_building(num_floors=10)
    return create_temp_apartment(
        building_id=building["id"],
        num_floors=building["num_floors"],
    )


# ── Sprint 3: Category fixtures ────────────────────────────────────────────────

@pytest.fixture(scope="function")
def create_temp_category(admin_api: APIClient):
    """
    Factory fixture: call it to create temporary expense categories via admin.
    All categories created through this fixture are soft-deleted after the test.

    Usage:
        def test_something(create_temp_building, create_temp_category):
            bld = create_temp_building()
            cat = create_temp_category(building_id=bld["id"])
    """
    created_ids: list[str] = []
    category_api = CategoryAPI(admin_api)

    def _create(building_id: str, **overrides) -> dict:
        data = CategoryFactory.valid(building_id=building_id)
        data.update(overrides)
        resp = category_api.create(**data)
        assert resp.status_code == 201, f"Category creation failed: {resp.text}"
        category = resp.json()
        created_ids.append(category["id"])
        return category

    yield _create

    for cid in created_ids:
        try:
            category_api.delete(cid)
        except Exception as e:
            logger.warning("Could not delete temp category %s: %s", cid, e)


@pytest.fixture(scope="function")
def temp_category(create_temp_building, create_temp_category) -> dict:
    """Single temporary category inside a fresh building."""
    building = create_temp_building()
    return create_temp_category(building_id=building["id"])


# ── Sprint 3: Expense fixtures ─────────────────────────────────────────────────

@pytest.fixture(scope="function")
def create_temp_expense(admin_api: APIClient):
    """
    Factory fixture: call it to create temporary expenses via admin.
    All expenses created through this fixture are soft-deleted after the test.

    Usage:
        def test_something(create_temp_building, create_temp_category, create_temp_expense):
            bld = create_temp_building()
            cat = create_temp_category(building_id=bld["id"])
            exp = create_temp_expense(building_id=bld["id"], category_id=cat["id"])
    """
    created_ids: list[str] = []
    expense_api = ExpenseAPI(admin_api)

    def _create(building_id: str, category_id: str, **overrides) -> dict:
        data = ExpenseFactory.valid(building_id=building_id, category_id=category_id)
        data.update(overrides)
        resp = expense_api.create(**data)
        assert resp.status_code == 201, f"Expense creation failed: {resp.text}"
        expense = resp.json()
        created_ids.append(expense["id"])
        return expense

    yield _create

    for eid in created_ids:
        try:
            expense_api.delete(eid)
        except Exception as e:
            logger.warning("Could not delete temp expense %s: %s", eid, e)


@pytest.fixture(scope="function")
def temp_expense(create_temp_building, create_temp_category, create_temp_expense) -> dict:
    """Single temporary expense in a fresh building with a fresh category."""
    building = create_temp_building(num_floors=5)
    category = create_temp_category(building_id=building["id"])
    return create_temp_expense(building_id=building["id"], category_id=category["id"])


# ── Sprint 4: Payment fixtures ─────────────────────────────────────────────────

@pytest.fixture(scope="function")
def payment_api(admin_api: APIClient) -> PaymentAPI:
    """Function-scoped PaymentAPI backed by the admin client."""
    return PaymentAPI(admin_api)


@pytest.fixture(scope="function")
def create_temp_payment(admin_api: APIClient):
    """
    Factory fixture: call it to create temporary payment records via admin.
    Payments are immutable, so teardown only logs — it does not delete them.

    Usage:
        def test_something(create_temp_building, create_temp_apartment,
                           create_temp_category, create_temp_expense,
                           create_temp_payment):
            bld = create_temp_building(num_floors=3)
            apt = create_temp_apartment(building_id=bld["id"])
            cat = create_temp_category(building_id=bld["id"])
            exp = create_temp_expense(building_id=bld["id"], category_id=cat["id"])
            pmt = create_temp_payment(apartment_id=apt["id"], expense_id=exp["id"])
    """
    created_ids: list[str] = []
    pmt_api = PaymentAPI(admin_api)

    def _create(apartment_id: str, expense_id: str | None = None,
                amount: float = 100.00, **overrides) -> dict:
        data = PaymentFactory.valid(apartment_id=apartment_id,
                                    expense_id=expense_id,
                                    amount=amount)
        data.update(overrides)
        resp = pmt_api.create(**data)
        assert resp.status_code == 201, f"Payment creation failed: {resp.text}"
        payment = resp.json()
        created_ids.append(payment["id"])
        return payment

    yield _create

    # Payments are immutable — no delete endpoint; just log for awareness
    if created_ids:
        logger.debug("Sprint 4 temp payments (immutable, not deleted): %s", created_ids)


@pytest.fixture(scope="function")
def temp_payment(
    create_temp_building, create_temp_apartment, create_temp_category,
    create_temp_expense, create_temp_payment
) -> dict:
    """
    Single temporary payment for a fresh building, apartment, category, and expense.
    The expense split assigns a share to the apartment, enabling a valid payment.
    """
    building = create_temp_building(num_floors=3)
    apartment = create_temp_apartment(building_id=building["id"])
    category = create_temp_category(building_id=building["id"])
    expense = create_temp_expense(
        building_id=building["id"],
        category_id=category["id"],
        amount="100.00",
        split_type="equal_all",
    )
    # After split engine, apartment owes share_amount (rounds up to nearest 5)
    # Use a partial payment so balance isn't zeroed for subsequent assertions
    return create_temp_payment(
        apartment_id=apartment["id"],
        expense_id=expense["id"],
        amount=50.00,
    )


# ── Sprint 5: Dashboard fixtures ───────────────────────────────────────────────

@pytest.fixture(scope="function")
def admin_dashboard_api(admin_api: APIClient) -> DashboardAPI:
    """Function-scoped DashboardAPI backed by the admin client."""
    return DashboardAPI(admin_api)


@pytest.fixture(scope="function")
def owner_dashboard_api(owner_api: APIClient) -> DashboardAPI:
    """Function-scoped DashboardAPI backed by a fresh owner client."""
    return DashboardAPI(owner_api)


@pytest.fixture(scope="function")
def dashboard_data(
    admin_api: APIClient,
    env_config,
    create_temp_building,
    create_temp_apartment,
    create_temp_category,
    create_temp_expense,
    create_temp_payment,
    create_temp_user,
):
    """
    Full dashboard data chain: building + category + owner + apartment + expense + payment.
    Returns a dict with all created entities plus an owner_client for dashboard/owner/ calls.
    Payments are immutable — not deleted on teardown.
    """
    from core.api_client import APIClient as _APIClient

    building = create_temp_building(num_floors=10)
    category = create_temp_category(building_id=building["id"])
    owner_user = create_temp_user(role="owner")
    apartment = create_temp_apartment(
        building_id=building["id"],
        num_floors=10,
        owner_id=owner_user["id"],
    )
    expense = create_temp_expense(
        building_id=building["id"],
        category_id=category["id"],
        amount="200.00",
        split_type="equal_all",
    )
    payment = create_temp_payment(
        apartment_id=apartment["id"],
        expense_id=expense["id"],
        amount=100.00,
    )

    # Authenticate as the owner for owner-dashboard calls
    owner_client = _APIClient(env_config.api_url)
    owner_client.authenticate(owner_user["email"], owner_user["password"])

    yield {
        "building": building,
        "category": category,
        "owner_user": owner_user,
        "apartment": apartment,
        "expense": expense,
        "payment": payment,
        "owner_client": owner_client,
    }

    owner_client.logout()


# ── Sprint 6: Notification fixtures ────────────────────────────────────────────

@pytest.fixture(scope="function")
def notification_api(admin_api: APIClient) -> NotificationAPI:
    """Function-scoped NotificationAPI backed by the admin client."""
    return NotificationAPI(admin_api)


@pytest.fixture(scope="function")
def owner_notification_api(owner_api: APIClient) -> NotificationAPI:
    """Function-scoped NotificationAPI backed by a fresh owner client."""
    return NotificationAPI(owner_api)


@pytest.fixture(scope="function")
def notification_data(
    admin_api: APIClient,
    env_config,
    create_temp_building,
    create_temp_apartment,
    create_temp_category,
    create_temp_expense,
    create_temp_user,
):
    """
    Full notification test chain: building + category + owner + apartment + expense.
    Creating the expense via the admin API triggers an EXPENSE_ADDED notification
    for the apartment owner (Sprint 6 trigger in ExpenseViewSet.perform_create).

    Returns a dict with all entities plus an owner_client for owner-notification calls.
    """
    from core.api_client import APIClient as _APIClient

    building = create_temp_building(num_floors=5)
    category = create_temp_category(building_id=building["id"])
    owner_user = create_temp_user(role="owner")
    apartment = create_temp_apartment(
        building_id=building["id"],
        num_floors=5,
        owner_id=owner_user["id"],
    )
    # Creating the expense triggers EXPENSE_ADDED notification for the owner
    expense = create_temp_expense(
        building_id=building["id"],
        category_id=category["id"],
        amount="150.00",
        split_type="equal_all",
    )

    # Authenticate as the owner so tests can check their own notifications
    owner_client = _APIClient(env_config.api_url)
    owner_client.authenticate(owner_user["email"], owner_user["password"])

    yield {
        "building": building,
        "category": category,
        "owner_user": owner_user,
        "apartment": apartment,
        "expense": expense,
        "owner_client": owner_client,
        "owner_notification_api": NotificationAPI(owner_client),
    }

    owner_client.logout()


# ── Sprint 8: Audit & Export fixtures ──────────────────────────────────────────

@pytest.fixture(scope="session")
def audit_api(admin_api: APIClient) -> AuditAPI:
    """Session-scoped AuditAPI backed by the admin client."""
    return AuditAPI(admin_api)


@pytest.fixture(scope="session")
def exports_api(admin_api: APIClient) -> ExportsAPI:
    """Session-scoped ExportsAPI backed by the admin client."""
    return ExportsAPI(admin_api)


@pytest.fixture(scope="function")
def audit_data(
    admin_api: APIClient,
    env_config,
    create_temp_building,
    create_temp_apartment,
    create_temp_category,
    create_temp_expense,
    create_temp_payment,
    create_temp_user,
):
    """
    Full audit test chain: building + category + owner + apartment + expense + payment.
    Creating these entities triggers audit log entries for each action.

    Returns a dict with all entities plus an owner_client.
    Payments are immutable — not deleted on teardown.
    """
    from core.api_client import APIClient as _APIClient

    building = create_temp_building(num_floors=5)
    category = create_temp_category(building_id=building["id"])
    owner_user = create_temp_user(role="owner")
    apartment = create_temp_apartment(
        building_id=building["id"],
        num_floors=5,
        owner_id=owner_user["id"],
    )
    expense = create_temp_expense(
        building_id=building["id"],
        category_id=category["id"],
        amount="200.00",
        split_type="equal_all",
    )
    payment = create_temp_payment(
        apartment_id=apartment["id"],
        expense_id=expense["id"],
        amount=100.00,
    )

    owner_client = _APIClient(env_config.api_url)
    owner_client.authenticate(owner_user["email"], owner_user["password"])

    yield {
        "admin_api": admin_api,
        "owner_api": owner_client,
        "building": building,
        "category": category,
        "owner_user": owner_user,
        "apartment": apartment,
        "expense": expense,
        "payment": payment,
    }

    owner_client.logout()


# ── Sprint 9 fixtures ───────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def perf_data(admin_api, env_config):
    """
    Session-scoped dataset for Sprint-9 performance benchmarks.

    Creates a full chain once and reuses across all perf tests:
      building → category → owner → apartment → expense (10 000 EGP) → payment

    Session-scoped so setup/teardown happens only once.
    Calls APIs directly (cannot inject function-scoped create_temp_* fixtures).
    """
    from api.building_api import BuildingAPI
    from api.apartment_api import ApartmentAPI
    from api.category_api import CategoryAPI
    from api.expense_api import ExpenseAPI
    from api.payment_api import PaymentAPI
    from api.user_api import UserAPI
    from api.auth_api import AuthAPI
    from utils.test_data import (
        BuildingFactory,
        ApartmentFactory,
        CategoryFactory,
        ExpenseFactory,
        UserFactory,
    )

    b_api   = BuildingAPI(admin_api)
    apt_api = ApartmentAPI(admin_api)
    cat_api = CategoryAPI(admin_api)
    exp_api = ExpenseAPI(admin_api)
    pay_api = PaymentAPI(admin_api)
    u_api   = UserAPI(admin_api)
    auth_a  = AuthAPI(admin_api)

    # 1. Building
    bld_r  = b_api.create(**BuildingFactory.valid(num_floors=5))
    bld_id = bld_r.json()["id"]

    # 2. Category
    cat_r  = cat_api.create(**CategoryFactory.valid(building_id=bld_id))
    cat_id = cat_r.json()["id"]

    # 3. Owner user
    owner_data = UserFactory.owner()
    owner_r    = auth_a.register(**owner_data)
    owner_id   = owner_r.json()["id"]
    b_api.assign_user(bld_id, owner_id)

    # 4. Apartment (owned)
    apt_data             = ApartmentFactory.valid(building_id=bld_id, num_floors=5)
    apt_data["owner_id"] = owner_id
    apt_r  = apt_api.create(**apt_data)
    apt_id = apt_r.json()["id"]

    # 5. Expense — 10 000 EGP gives the apartment enough balance for payment tests
    exp_r  = exp_api.create(
        **ExpenseFactory.valid(building_id=bld_id, category_id=cat_id, amount=10000.00)
    )
    exp_id = exp_r.json()["id"]

    # 6. One seed payment (needed for receipt / pagination tests)
    pay_r  = pay_api.create(
        apartment_id=apt_id,
        amount_paid="10.00",
        payment_date="2026-01-01",
        payment_method="cash",
    )
    pay_id = pay_r.json()["id"]

    yield {
        "building_id":  bld_id,
        "category_id":  cat_id,
        "owner_id":     owner_id,
        "apartment_id": apt_id,
        "expense_id":   exp_id,
        "payment_id":   pay_id,
    }

    # Teardown: payments are immutable; delete owner + building (cascade handles rest)
    try:
        u_api.delete_user(owner_id)
    except Exception:
        pass
    try:
        b_api.delete(bld_id)
    except Exception:
        pass


@pytest.fixture(scope="function")
def sec_data(
    admin_api,
    env_config,
    create_temp_building,
    create_temp_user,
    create_temp_apartment,
    create_temp_payment,
):
    """
    Two isolated owners with separate apartments for Sprint-9 IDOR/security tests.

    Owner A and Owner B are in the same building but own different apartments.
    This setup verifies that cross-owner resource access is denied (404/403).
    """
    from core.api_client import APIClient as _APIClient

    building = create_temp_building(num_floors=5)
    owner_a  = create_temp_user(role="owner")
    owner_b  = create_temp_user(role="owner")

    apt_a = create_temp_apartment(
        building_id=building["id"], num_floors=5, owner_id=owner_a["id"]
    )
    apt_b = create_temp_apartment(
        building_id=building["id"], num_floors=5, owner_id=owner_b["id"]
    )

    pay_a = create_temp_payment(apartment_id=apt_a["id"], amount=10.00)
    pay_b = create_temp_payment(apartment_id=apt_b["id"], amount=10.00)

    a_client = _APIClient(env_config.api_url)
    a_client.authenticate(owner_a["email"], owner_a["password"])
    b_client = _APIClient(env_config.api_url)
    b_client.authenticate(owner_b["email"], owner_b["password"])

    yield {
        "owner_a_token":        a_client.access_token,
        "owner_b_token":        b_client.access_token,
        "owner_a_apartment_id": apt_a["id"],
        "owner_b_apartment_id": apt_b["id"],
        "owner_a_payment_id":   pay_a["id"],
        "owner_b_payment_id":   pay_b["id"],
    }

    a_client.logout()
    b_client.logout()
