"""
Sprint 8 — Audit & Exports Mobile Tests (8 cases)
TC-S8-MOB-001 → TC-S8-MOB-008

All tests are skip-guarded: if Appium is not reachable, the entire module is skipped.

Test class layout:
  TestAuditMobile   (3)  – audit page not accessible in mobile app, exports via mobile
  TestExportMobile  (3)  – CSV/XLSX/receipt download from mobile
  TestOfflineMobile (2)  – export unavailable offline; receipt unavailable offline
"""
from __future__ import annotations

import pytest

pytestmark = [
    pytest.mark.mobile,
    pytest.mark.sprint_8,
]


@pytest.fixture(scope="module", autouse=True)
def _mobile_available(mobile_driver):
    if mobile_driver is None:
        pytest.skip("Appium driver not available — skipping Sprint 8 mobile tests")


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S8-MOB-001 … 003 — Audit Mobile
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuditMobile:

    @pytest.mark.positive
    def test_audit_log_not_exposed_in_mobile_owner_view(self, mobile_driver):
        """TC-S8-MOB-001: Audit Log section is not accessible to owner role in mobile app."""
        pytest.skip("not implemented — requires owner login flow and nav inspection")

    @pytest.mark.positive
    def test_admin_can_trigger_export_from_mobile(self, mobile_driver):
        """TC-S8-MOB-002: Admin user can trigger a data export from the mobile app settings."""
        pytest.skip("not implemented — requires admin login and export action trigger")

    @pytest.mark.positive
    def test_export_download_toast_appears_on_mobile(self, mobile_driver):
        """TC-S8-MOB-003: A download/success toast appears after triggering an export on mobile."""
        pytest.skip("not implemented — requires export trigger and toast detection")


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S8-MOB-004 … 006 — Export Mobile
# ═══════════════════════════════════════════════════════════════════════════════

class TestExportMobile:

    @pytest.mark.positive
    def test_payments_csv_download_works_on_mobile(self, mobile_driver):
        """TC-S8-MOB-004: GET /exports/payments/?format=csv download completes on mobile device."""
        pytest.skip("not implemented — requires WebView/API call intercept on mobile")

    @pytest.mark.positive
    def test_payments_xlsx_download_works_on_mobile(self, mobile_driver):
        """TC-S8-MOB-005: GET /exports/payments/?format=xlsx download completes on mobile device."""
        pytest.skip("not implemented — requires XLSX MIME type handling on mobile")

    @pytest.mark.positive
    def test_payment_receipt_pdf_opens_on_mobile(self, mobile_driver):
        """TC-S8-MOB-006: PDF receipt opens correctly in mobile PDF viewer."""
        pytest.skip("not implemented — requires PDF intent/viewer launch detection via Appium")


# ═══════════════════════════════════════════════════════════════════════════════
# TC-S8-MOB-007 … 008 — Offline Behaviour
# ═══════════════════════════════════════════════════════════════════════════════

class TestOfflineMobile:

    @pytest.mark.positive
    def test_export_shows_error_when_offline(self, mobile_driver):
        """TC-S8-MOB-007: Attempting an export while offline shows an appropriate error message."""
        pytest.skip("not implemented — requires airplane mode toggle and error detection")

    @pytest.mark.positive
    def test_receipt_shows_error_when_offline(self, mobile_driver):
        """TC-S8-MOB-008: Requesting a PDF receipt while offline shows an appropriate error message."""
        pytest.skip("not implemented — requires offline mode + receipt action trigger")
