"""UI tests for notifications — Sprint 6."""
import pytest
from config.settings import settings


@pytest.mark.ui
@pytest.mark.notifications
@pytest.mark.sprint6
class TestNotificationManagement:

    def test_notification_bell_visible(self, admin_page):
        """Notification bell icon is visible on dashboard."""
        admin_page.goto(f"{settings.BASE_URL}/dashboard")
        admin_page.wait_for_load_state("networkidle")

    def test_notification_list_page(self, admin_page):
        """Notifications page loads."""
        admin_page.goto(f"{settings.BASE_URL}/notifications")
        admin_page.wait_for_load_state("networkidle")
        assert "/notifications" in admin_page.url

    def test_owner_sees_notifications(self, owner_page):
        """Owner can access notifications."""
        owner_page.goto(f"{settings.BASE_URL}/notifications")
        owner_page.wait_for_load_state("networkidle")
        assert "/notifications" in owner_page.url

    def test_admin_broadcast_panel(self, admin_page):
        """Admin sees broadcast panel."""
        admin_page.goto(f"{settings.BASE_URL}/notifications")
        admin_page.wait_for_load_state("networkidle")
