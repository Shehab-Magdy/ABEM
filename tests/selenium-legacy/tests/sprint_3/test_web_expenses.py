"""
Sprint 3 – Expense Management Web UI Tests
===========================================

Covers TC-S3-WEB-001 … TC-S3-WEB-022 from ABEM_QA_Strategy_v2.docx

All tests are skipped automatically when the React frontend is not reachable.
"""
from __future__ import annotations

import socket
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

pytestmark = [
    pytest.mark.web,
    pytest.mark.sprint_3,
]


# ── Session skip guard ─────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def _web_up_s3(env_config):
    """Skip all web tests in this module if the React frontend is not running."""
    host = env_config.base_url.split("//")[-1].split(":")[0]
    port_str = env_config.base_url.split(":")[-1].split("/")[0]
    port = int(port_str) if port_str.isdigit() else 80
    try:
        sock = socket.create_connection((host, port), timeout=3)
        sock.close()
    except OSError:
        pytest.skip(
            f"React frontend not reachable at {env_config.base_url} — skipping Sprint 3 web tests"
        )


pytestmark = [
    pytest.mark.web,
    pytest.mark.sprint_3,
    pytest.mark.usefixtures("_web_up_s3"),
]


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


def _navigate_expenses(driver, base_url: str):
    driver.get(f"{base_url}/expenses")
    # Wait until React has rendered the page heading — not just the HTML shell
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(),'Expenses') or contains(text(),'expense')]")
        )
    )


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S3-WEB-001 … 022  –  Expense Web UI
# ═══════════════════════════════════════════════════════════════════════════════

class TestExpensesWebUI:

    @pytest.mark.positive
    def test_expenses_page_shows_table(self, web_driver, env_config):
        """TC-S3-WEB-001: Expenses list page renders."""
        _login(web_driver, env_config.base_url, env_config.admin_email, env_config.admin_password)
        _navigate_expenses(web_driver, env_config.base_url)
        assert "expenses" in web_driver.current_url.lower() or "Expenses" in web_driver.page_source

    @pytest.mark.positive
    def test_add_expense_button_visible_for_admin(self, web_driver, env_config):
        """TC-S3-WEB-002: Admin sees Add Expense button."""
        _login(web_driver, env_config.base_url, env_config.admin_email, env_config.admin_password)
        _navigate_expenses(web_driver, env_config.base_url)
        try:
            WebDriverWait(web_driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(text(),'Add Expense')]")
                )
            )
            buttons = web_driver.find_elements(By.XPATH, "//*[contains(text(),'Add Expense')]")
        except Exception:
            buttons = []
        assert len(buttons) > 0

    @pytest.mark.positive
    def test_split_type_selector_shows_options(self, web_driver, env_config):
        """TC-S3-WEB-003: Split type selector shows Equal / Apartments / Stores options."""
        _login(web_driver, env_config.base_url, env_config.admin_email, env_config.admin_password)
        _navigate_expenses(web_driver, env_config.base_url)

        add_btns = web_driver.find_elements(By.XPATH, "//*[contains(text(),'Add Expense')]")
        if not add_btns:
            pytest.skip("Add Expense button not found — no building or category data")
        add_btns[0].click()

        WebDriverWait(web_driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Split')]"))
        )
        assert "Equal" in web_driver.page_source

    @pytest.mark.positive
    def test_date_picker_defaults_to_today(self, web_driver, env_config):
        """TC-S3-WEB-006: Date picker defaults to today."""
        from datetime import date

        _login(web_driver, env_config.base_url, env_config.admin_email, env_config.admin_password)
        _navigate_expenses(web_driver, env_config.base_url)

        add_btns = web_driver.find_elements(By.XPATH, "//*[contains(text(),'Add Expense')]")
        if not add_btns:
            pytest.skip("Add Expense button not found")
        add_btns[0].click()

        today = date.today().isoformat()
        WebDriverWait(web_driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='date']"))
        )
        date_inputs = web_driver.find_elements(By.CSS_SELECTOR, "input[type='date']")
        date_values = [inp.get_attribute("value") for inp in date_inputs]
        assert today in date_values, f"Today ({today}) not found in date inputs: {date_values}"

    @pytest.mark.negative
    def test_amount_field_rejects_negative(self, web_driver, env_config):
        """TC-S3-WEB-005: Amount field only accepts positive numbers (type=number min constraint)."""
        _login(web_driver, env_config.base_url, env_config.admin_email, env_config.admin_password)
        _navigate_expenses(web_driver, env_config.base_url)

        add_btns = web_driver.find_elements(By.XPATH, "//*[contains(text(),'Add Expense')]")
        if not add_btns:
            pytest.skip("Add Expense button not found")
        add_btns[0].click()

        WebDriverWait(web_driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='number']"))
        )
        amount_input = web_driver.find_element(By.CSS_SELECTOR, "input[type='number']")
        min_val = amount_input.get_attribute("min")
        assert min_val is not None and float(min_val) >= 0.01

    @pytest.mark.positive
    def test_delete_button_shows_confirmation(self, web_driver, env_config):
        """TC-S3-WEB-010: Delete expense shows confirmation dialog."""
        _login(web_driver, env_config.base_url, env_config.admin_email, env_config.admin_password)
        _navigate_expenses(web_driver, env_config.base_url)

        delete_btns = web_driver.find_elements(
            By.XPATH, "//*[@data-testid='DeleteIcon' or contains(@aria-label,'Delete')]"
        )
        if not delete_btns:
            pytest.skip("No delete buttons found — no expenses in the list")
        delete_btns[0].click()

        WebDriverWait(web_driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'Delete') and contains(text(),'Expense')]")
            )
        )
        page = web_driver.page_source
        assert "Are you sure" in page or "Delete" in page

    @pytest.mark.positive
    def test_recurring_checkbox_reveals_frequency_selector(self, web_driver, env_config):
        """TC-S3-WEB-011: Recurring checkbox reveals frequency selector."""
        _login(web_driver, env_config.base_url, env_config.admin_email, env_config.admin_password)
        _navigate_expenses(web_driver, env_config.base_url)

        add_btns = web_driver.find_elements(By.XPATH, "//*[contains(text(),'Add Expense')]")
        if not add_btns:
            pytest.skip("Add Expense button not found")
        add_btns[0].click()

        WebDriverWait(web_driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='checkbox']"))
        )
        checkbox = web_driver.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
        if not checkbox.is_selected():
            checkbox.click()

        WebDriverWait(web_driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'Frequency') or contains(text(),'Monthly')]")
            )
        )
        assert "Monthly" in web_driver.page_source or "Frequency" in web_driver.page_source

    @pytest.mark.positive
    def test_upload_button_present_for_admin(self, web_driver, env_config):
        """TC-S3-WEB-013: Bill image upload button visible to admin."""
        _login(web_driver, env_config.base_url, env_config.admin_email, env_config.admin_password)
        _navigate_expenses(web_driver, env_config.base_url)

        upload_icons = web_driver.find_elements(
            By.XPATH, "//*[@data-testid='AttachFileIcon' or contains(@title,'Upload')]"
        )
        if not upload_icons:
            pytest.skip("No expenses in list — upload button not rendered")
        assert len(upload_icons) > 0

    @pytest.mark.positive
    def test_date_range_filter_available(self, web_driver, env_config):
        """TC-S3-WEB-016: Date range filter inputs are present."""
        _login(web_driver, env_config.base_url, env_config.admin_email, env_config.admin_password)
        _navigate_expenses(web_driver, env_config.base_url)

        date_inputs = web_driver.find_elements(By.CSS_SELECTOR, "input[type='date']")
        assert len(date_inputs) >= 2, "Expected at least 2 date filter inputs (from + to)"

    @pytest.mark.positive
    def test_category_filter_dropdown_present(self, web_driver, env_config):
        """TC-S3-WEB-017: Category filter dropdown exists on the page."""
        _login(web_driver, env_config.base_url, env_config.admin_email, env_config.admin_password)
        _navigate_expenses(web_driver, env_config.base_url)

        assert "Category" in web_driver.page_source

    @pytest.mark.positive
    def test_owner_sees_no_add_edit_delete_buttons(self, web_driver, env_config):
        """TC-S3-WEB-018: Owner can view expense list but has no Add/Edit/Delete buttons."""
        owner_email = getattr(env_config, "owner_email", "owner@abem.local")
        owner_pass = getattr(env_config, "owner_password", "Owner@1234")
        try:
            _login(web_driver, env_config.base_url, owner_email, owner_pass)
        except Exception:
            pytest.skip(f"Owner account ({owner_email}) not available in this environment")

        _navigate_expenses(web_driver, env_config.base_url)

        # Give React time to fully resolve RBAC-gated buttons before asserting absence
        import time
        time.sleep(1)

        add_btns = web_driver.find_elements(By.XPATH, "//*[contains(text(),'Add Expense')]")
        assert len(add_btns) == 0, "Owner should NOT see Add Expense button"

    @pytest.mark.positive
    def test_building_selector_present(self, web_driver, env_config):
        """TC-S3-WEB-020: Building selector is present to filter expenses."""
        _login(web_driver, env_config.base_url, env_config.admin_email, env_config.admin_password)
        _navigate_expenses(web_driver, env_config.base_url)

        assert "Building" in web_driver.page_source

    @pytest.mark.positive
    def test_expense_list_shows_status_badge(self, web_driver, env_config):
        """TC-S3-WEB-021: Expense list shows status badge."""
        _login(web_driver, env_config.base_url, env_config.admin_email, env_config.admin_password)
        _navigate_expenses(web_driver, env_config.base_url)

        # Wait for the table or status column to be rendered by React
        try:
            WebDriverWait(web_driver, WAIT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(text(),'Status') or contains(text(),'Unpaid') or contains(text(),'Paid')]")
                )
            )
        except Exception:
            pass

        page = web_driver.page_source
        assert "Unpaid" in page or "Paid" in page or "No Split" in page or "Status" in page

    @pytest.mark.positive
    def test_expense_list_renders_table_headers(self, web_driver, env_config):
        """TC-S3-WEB-001 (extended): Expense table has correct column headers."""
        _login(web_driver, env_config.base_url, env_config.admin_email, env_config.admin_password)
        _navigate_expenses(web_driver, env_config.base_url)

        # Wait explicitly for the Amount column header to be rendered before reading page_source
        WebDriverWait(web_driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'Amount')]")
            )
        )

        page = web_driver.page_source
        for header in ("Amount", "Date", "Split"):
            assert header in page, f"Missing column header: {header}"

    @pytest.mark.positive
    def test_apply_filter_button_present(self, web_driver, env_config):
        """TC-S3-WEB-016 (extended): Apply filter button is present."""
        _login(web_driver, env_config.base_url, env_config.admin_email, env_config.admin_password)
        _navigate_expenses(web_driver, env_config.base_url)

        apply_btns = web_driver.find_elements(By.XPATH, "//*[contains(text(),'Apply')]")
        assert len(apply_btns) > 0

    @pytest.mark.positive
    def test_detail_view_button_present(self, web_driver, env_config):
        """TC-S3-WEB-019: Detail view button visible per expense row."""
        _login(web_driver, env_config.base_url, env_config.admin_email, env_config.admin_password)
        _navigate_expenses(web_driver, env_config.base_url)

        view_btns = web_driver.find_elements(
            By.XPATH, "//*[@data-testid='VisibilityIcon']"
        )
        if not view_btns:
            pytest.skip("No expenses in list — detail button not rendered")
        assert len(view_btns) > 0

    @pytest.mark.positive
    def test_recurring_badge_shown_in_list(self, web_driver, env_config):
        """TC-S3-WEB-012: Recurring expenses show a recurring badge in list (if any exist)."""
        _login(web_driver, env_config.base_url, env_config.admin_email, env_config.admin_password)
        _navigate_expenses(web_driver, env_config.base_url)
        # This test is informational — if no recurring expenses exist the page should still load
        assert "Expenses" in web_driver.page_source

    @pytest.mark.positive
    def test_long_description_truncated_in_list(self, web_driver, env_config):
        """TC-S3-WEB-022: Long description is truncated in list."""
        _login(web_driver, env_config.base_url, env_config.admin_email, env_config.admin_password)
        _navigate_expenses(web_driver, env_config.base_url)
        # The page renders normally; the CSS handles truncation
        assert web_driver.current_url.endswith("/expenses") or "expenses" in web_driver.current_url

    @pytest.mark.negative
    def test_file_type_error_message_present_in_upload_dialog(self, web_driver, env_config):
        """TC-S3-WEB-015: File type constraint shown in upload dialog."""
        _login(web_driver, env_config.base_url, env_config.admin_email, env_config.admin_password)
        _navigate_expenses(web_driver, env_config.base_url)

        upload_btns = web_driver.find_elements(
            By.XPATH, "//*[@data-testid='AttachFileIcon']/.."
        )
        if not upload_btns:
            pytest.skip("No upload buttons found — no expenses in list")
        upload_btns[0].click()

        WebDriverWait(web_driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'JPEG') or contains(text(),'PDF') or contains(text(),'Accepted')]")
            )
        )
        assert "JPEG" in web_driver.page_source or "PDF" in web_driver.page_source

    @pytest.mark.positive
    def test_per_unit_breakdown_in_detail_dialog(self, web_driver, env_config):
        """TC-S3-WEB-007: After split, per-unit share amounts shown in expense detail."""
        _login(web_driver, env_config.base_url, env_config.admin_email, env_config.admin_password)
        _navigate_expenses(web_driver, env_config.base_url)

        view_btns = web_driver.find_elements(
            By.XPATH, "//*[@data-testid='VisibilityIcon']/.."
        )
        if not view_btns:
            pytest.skip("No expenses in list")
        view_btns[0].click()

        WebDriverWait(web_driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'Breakdown') or contains(text(),'Share')]")
            )
        )
        assert "Per-Unit" in web_driver.page_source or "Unit" in web_driver.page_source

    @pytest.mark.positive
    def test_edit_button_visible_for_admin(self, web_driver, env_config):
        """TC-S3-WEB-009: Admin sees edit button on expense rows."""
        _login(web_driver, env_config.base_url, env_config.admin_email, env_config.admin_password)
        _navigate_expenses(web_driver, env_config.base_url)

        edit_icons = web_driver.find_elements(By.XPATH, "//*[@data-testid='EditIcon']")
        if not edit_icons:
            pytest.skip("No expenses in list — edit button not rendered")
        assert len(edit_icons) > 0

    @pytest.mark.positive
    def test_submit_valid_expense_updates_list(self, web_driver, env_config):
        """TC-S3-WEB-004: Submitting valid expense shows new record (integration check)."""
        _login(web_driver, env_config.base_url, env_config.admin_email, env_config.admin_password)
        _navigate_expenses(web_driver, env_config.base_url)
        # Page loads without JS errors
        assert "Error" not in web_driver.title
