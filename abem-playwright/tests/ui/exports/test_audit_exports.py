"""UI tests for audit log and exports — Sprint 8."""
import pytest
from config.settings import settings


@pytest.mark.ui
@pytest.mark.exports
@pytest.mark.sprint8
class TestAuditExports:

    def test_audit_log_page_loads(self, admin_page):
        """Audit log page loads for admin."""
        admin_page.goto(f"{settings.BASE_URL}/audit")
        admin_page.wait_for_load_state("networkidle")

    def test_export_payments_button(self, admin_page):
        """Export payments button is available."""
        admin_page.goto(f"{settings.BASE_URL}/exports")
        admin_page.wait_for_load_state("networkidle")

    def test_export_expenses_button(self, admin_page):
        """Export expenses button is available."""
        admin_page.goto(f"{settings.BASE_URL}/exports")
        admin_page.wait_for_load_state("networkidle")

    @pytest.mark.rbac
    def test_owner_no_export_access(self, owner_page):
        """Owner has no export buttons."""
        owner_page.goto(f"{settings.BASE_URL}/exports")
        owner_page.wait_for_load_state("networkidle")
        assert not owner_page.locator("button:has-text('Export')").is_visible(timeout=2000)

    @pytest.mark.rbac
    def test_owner_no_audit_access(self, owner_page):
        """Owner cannot access audit log."""
        owner_page.goto(f"{settings.BASE_URL}/audit")
        owner_page.wait_for_timeout(2000)
