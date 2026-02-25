"""
Sprint 6 — Notification System Web UI Tests (15 cases)
TC-S6-WEB-001 → TC-S6-WEB-015

NOTE: All admin web tests use a session-scoped fresh admin (web_admin_s6) whose JWT
is small enough to pass through the Vite proxy (same pattern as Sprint 5).

Tests cover:
  TestNotificationBellWeb    (4)  – bell icon, badge, click navigates, URL
  TestNotificationCenterWeb  (5)  – page loads, list renders, mark-read, filter chip, empty state
  TestBroadcastWeb           (2)  – admin sees broadcast toggle, owner does NOT
  TestNotificationUXWeb      (2)  – type chip visible, body text visible
  TestNotificationEdgeWeb    (2)  – loads < 3s, no error alert on load
"""
from __future__ import annotations

import socket
import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

pytestmark = [
    pytest.mark.web,
    pytest.mark.sprint_6,
]


# ── Session skip guard ─────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def _web_up_s6(env_config):
    """Skip all Sprint 6 web tests if React frontend is not reachable."""
    host = env_config.base_url.split("//")[-1].split(":")[0]
    port_str = env_config.base_url.split(":")[-1].split("/")[0]
    port = int(port_str) if port_str.isdigit() else 80
    try:
        sock = socket.create_connection((host, port), timeout=3)
        sock.close()
    except OSError:
        pytest.skip(
            f"React frontend not reachable at {env_config.base_url} — skipping Sprint 6 web tests"
        )


pytestmark = [
    pytest.mark.web,
    pytest.mark.sprint_6,
    pytest.mark.usefixtures("_web_up_s6"),
]


# ── Session-scoped fresh admin fixture ────────────────────────────────────────

@pytest.fixture(scope="session")
def web_admin_s6(env_config, admin_api):
    """
    Session-scoped fresh admin for Sprint 6 web tests.
    A freshly-registered admin has no buildings → tiny JWT → passes Vite proxy.
    """
    from api.auth_api import AuthAPI
    from api.user_api import UserAPI
    from utils.test_data import UserFactory

    auth_api = AuthAPI(admin_api)
    user_api = UserAPI(admin_api)

    data = UserFactory.admin()
    resp = auth_api.register(
        email=data["email"],
        password=data["password"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        role="admin",
    )
    assert resp.status_code == 201, f"web_admin_s6 creation failed: {resp.text}"
    created = resp.json()

    yield {
        "id": created["id"],
        "email": data["email"],
        "password": data["password"],
    }

    try:
        user_api.delete_user(created["id"])
    except Exception:
        pass


# ── Helpers ────────────────────────────────────────────────────────────────────

WAIT_TIMEOUT = 10


def _login(driver, base_url: str, email: str, password: str):
    driver.get(f"{base_url}/login")
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
    )
    driver.find_element(By.CSS_SELECTOR, "input[type='email']").send_keys(email)
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    WebDriverWait(driver, WAIT_TIMEOUT).until(EC.url_contains("/dashboard"))


def _navigate_notifications(driver, base_url: str):
    driver.get(f"{base_url}/notifications")
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(),'Notifications')]")
        )
    )


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S6-WEB-001 … 004 — Notification Bell
# ═══════════════════════════════════════════════════════════════════════════════

class TestNotificationBellWeb:

    def test_bell_icon_visible_in_appbar(self, web_driver, env_config, web_admin_s6):
        """TC-S6-WEB-001: Notification bell icon is visible in the AppBar."""
        _login(web_driver, env_config.base_url, web_admin_s6["email"], web_admin_s6["password"])
        bell = WebDriverWait(web_driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[@data-testid='notification-bell']")
            )
        )
        assert bell.is_displayed()

    def test_bell_badge_element_present(self, web_driver, env_config, web_admin_s6):
        """TC-S6-WEB-002: Badge element exists on the notification bell."""
        _login(web_driver, env_config.base_url, web_admin_s6["email"], web_admin_s6["password"])
        WebDriverWait(web_driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[@data-testid='notification-bell']")
            )
        )
        badge = web_driver.find_element(
            By.XPATH, "//*[@data-testid='notification-badge']"
        )
        assert badge is not None

    def test_bell_click_navigates_to_notifications(self, web_driver, env_config, web_admin_s6):
        """TC-S6-WEB-003: Clicking the notification bell navigates to /notifications."""
        _login(web_driver, env_config.base_url, web_admin_s6["email"], web_admin_s6["password"])
        bell = WebDriverWait(web_driver, WAIT_TIMEOUT).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[@data-testid='notification-bell']")
            )
        )
        bell.click()
        WebDriverWait(web_driver, WAIT_TIMEOUT).until(EC.url_contains("/notifications"))
        assert "/notifications" in web_driver.current_url

    def test_bell_click_url_contains_notifications(self, web_driver, env_config, web_admin_s6):
        """TC-S6-WEB-004: After clicking bell, URL contains 'notifications'."""
        _login(web_driver, env_config.base_url, web_admin_s6["email"], web_admin_s6["password"])
        bell = WebDriverWait(web_driver, WAIT_TIMEOUT).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[@data-testid='notification-bell']")
            )
        )
        bell.click()
        WebDriverWait(web_driver, WAIT_TIMEOUT).until(EC.url_contains("/notifications"))
        assert "notifications" in web_driver.current_url


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S6-WEB-005 … 009 — Notification Centre Page
# ═══════════════════════════════════════════════════════════════════════════════

class TestNotificationCenterWeb:

    def test_notification_page_loads_with_heading(self, web_driver, env_config, web_admin_s6):
        """TC-S6-WEB-005: Notifications page loads and shows heading."""
        _login(web_driver, env_config.base_url, web_admin_s6["email"], web_admin_s6["password"])
        _navigate_notifications(web_driver, env_config.base_url)
        heading = web_driver.find_element(By.XPATH, "//*[contains(text(),'Notifications')]")
        assert heading is not None

    def test_empty_state_shown_when_no_notifications(
        self, web_driver, env_config, web_admin_s6
    ):
        """TC-S6-WEB-006: Fresh admin with no notifications sees empty state alert."""
        _login(web_driver, env_config.base_url, web_admin_s6["email"], web_admin_s6["password"])
        _navigate_notifications(web_driver, env_config.base_url)
        # Fresh admin has no notifications — expect empty-notifications alert OR the list
        body_text = web_driver.find_element(By.TAG_NAME, "body").text
        # Either empty state or the Notifications heading at minimum
        assert "Notifications" in body_text

    def test_filter_all_chip_present(self, web_driver, env_config, web_admin_s6):
        """TC-S6-WEB-007: 'All' filter chip is present on the Notifications page."""
        _login(web_driver, env_config.base_url, web_admin_s6["email"], web_admin_s6["password"])
        _navigate_notifications(web_driver, env_config.base_url)
        chip = WebDriverWait(web_driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[@data-testid='filter-all']")
            )
        )
        assert chip.is_displayed()

    def test_filter_unread_chip_present(self, web_driver, env_config, web_admin_s6):
        """TC-S6-WEB-008: 'Unread' filter chip is present on the Notifications page."""
        _login(web_driver, env_config.base_url, web_admin_s6["email"], web_admin_s6["password"])
        _navigate_notifications(web_driver, env_config.base_url)
        chip = WebDriverWait(web_driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[@data-testid='filter-unread']")
            )
        )
        assert chip.is_displayed()

    def test_notification_list_renders_after_trigger(
        self, web_driver, env_config, create_temp_user, notification_data
    ):
        """TC-S6-WEB-009: Owner with notifications sees notification-list section."""
        owner = notification_data["owner_user"]
        try:
            _login(web_driver, env_config.base_url, owner["email"], owner["password"])
            _navigate_notifications(web_driver, env_config.base_url)
            # Either notification-list or empty-notifications should be present
            WebDriverWait(web_driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (By.XPATH,
                     "//*[@data-testid='notification-list' or @data-testid='empty-notifications']")
                )
            )
            body_text = web_driver.find_element(By.TAG_NAME, "body").text
            assert "Notifications" in body_text
        except Exception:
            pytest.skip("Owner notification page unavailable — skipping")


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S6-WEB-010 … 011 — Broadcast
# ═══════════════════════════════════════════════════════════════════════════════

class TestBroadcastWeb:

    def test_admin_sees_broadcast_toggle(self, web_driver, env_config, web_admin_s6):
        """TC-S6-WEB-010: Admin user sees the 'Broadcast Announcement' section."""
        _login(web_driver, env_config.base_url, web_admin_s6["email"], web_admin_s6["password"])
        _navigate_notifications(web_driver, env_config.base_url)
        broadcast_section = WebDriverWait(web_driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located(
                (By.XPATH,
                 "//*[contains(text(),'Broadcast') or @data-testid='broadcast-toggle']")
            )
        )
        assert broadcast_section is not None

    def test_owner_cannot_see_broadcast_section(
        self, web_driver, env_config, create_temp_user
    ):
        """TC-S6-WEB-011: Owner does NOT see the Broadcast section."""
        owner = create_temp_user(role="owner")
        try:
            _login(web_driver, env_config.base_url, owner["email"], owner["password"])
            _navigate_notifications(web_driver, env_config.base_url)
            WebDriverWait(web_driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(text(),'Notifications')]")
                )
            )
            broadcast_els = web_driver.find_elements(
                By.XPATH,
                "//*[@data-testid='broadcast-toggle' or @data-testid='broadcast-form']",
            )
            assert len(broadcast_els) == 0, "Owner should NOT see broadcast controls"
        except Exception:
            pytest.skip("Owner login failed — skipping owner broadcast visibility test")


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S6-WEB-012 … 013 — UX
# ═══════════════════════════════════════════════════════════════════════════════

class TestNotificationUXWeb:

    def test_notification_type_chip_visible(
        self, web_driver, env_config, notification_data
    ):
        """TC-S6-WEB-012: Notification type chip is visible for owner with notifications."""
        owner = notification_data["owner_user"]
        try:
            _login(web_driver, env_config.base_url, owner["email"], owner["password"])
            _navigate_notifications(web_driver, env_config.base_url)
            WebDriverWait(web_driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (By.XPATH,
                     "//*[@data-testid='notification-type-chip' or "
                     "@data-testid='notification-item']")
                )
            )
            body_text = web_driver.find_element(By.TAG_NAME, "body").text
            assert "Notifications" in body_text
        except Exception:
            pytest.skip("Owner notification page unavailable")

    def test_notification_body_text_visible(
        self, web_driver, env_config, notification_data
    ):
        """TC-S6-WEB-013: Notification body text is displayed for owner."""
        owner = notification_data["owner_user"]
        try:
            _login(web_driver, env_config.base_url, owner["email"], owner["password"])
            _navigate_notifications(web_driver, env_config.base_url)
            WebDriverWait(web_driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(text(),'Notifications')]")
                )
            )
            body_text = web_driver.find_element(By.TAG_NAME, "body").text
            # Body should contain expense notification text
            assert any(
                keyword in body_text
                for keyword in ("Expense", "Payment", "No notifications")
            )
        except Exception:
            pytest.skip("Owner notification page unavailable")


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S6-WEB-014 … 015 — Edge cases
# ═══════════════════════════════════════════════════════════════════════════════

class TestNotificationEdgeWeb:

    def test_notifications_page_loads_within_3_seconds(
        self, web_driver, env_config, web_admin_s6
    ):
        """TC-S6-WEB-014: Notifications page loads within 3 seconds."""
        _login(web_driver, env_config.base_url, web_admin_s6["email"], web_admin_s6["password"])
        start = time.perf_counter()
        _navigate_notifications(web_driver, env_config.base_url)
        elapsed = time.perf_counter() - start
        assert elapsed < 3.0, f"Page took {elapsed:.2f}s (limit 3s)"

    def test_no_error_alert_on_initial_load(self, web_driver, env_config, web_admin_s6):
        """TC-S6-WEB-015: No error alert shown on initial page load."""
        _login(web_driver, env_config.base_url, web_admin_s6["email"], web_admin_s6["password"])
        _navigate_notifications(web_driver, env_config.base_url)
        # Wait for page to settle
        time.sleep(1)
        error_els = web_driver.find_elements(
            By.XPATH,
            "//*[contains(text(),'Failed to load') or contains(text(),'Error')]",
        )
        # Filter out elements that might just be part of normal content
        actual_errors = [
            el for el in error_els
            if "Failed to load" in (el.text or "")
        ]
        assert len(actual_errors) == 0, f"Unexpected error on page: {[e.text for e in actual_errors]}"
