"""UI tests for notifications center."""
import pytest
from pages.notifications_page import NotificationsPage
from config.settings import settings


@pytest.mark.ui
@pytest.mark.notifications
class TestNotificationsUI:
    def test_notification_bell_visible(self, admin_page):
        admin_page.goto(f"{settings.BASE_URL}/dashboard")
        admin_page.wait_for_load_state("networkidle")
        bell = admin_page.get_by_test_id("notification-bell")
        assert bell.count() > 0

    def test_notification_list_renders(self, admin_page):
        np = NotificationsPage(admin_page)
        np.navigate()
        np.wait_for_load()

    def test_filter_unread(self, admin_page):
        np = NotificationsPage(admin_page)
        np.navigate()
        np.wait_for_load()
        np.click_filter_unread()
        admin_page.wait_for_timeout(1000)
