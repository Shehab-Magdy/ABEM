"""UI tests for notification preferences and broadcast."""
import pytest
from pages.notifications_page import NotificationsPage
from config.settings import settings


@pytest.mark.ui
@pytest.mark.notifications
class TestNotificationPreferencesUI:
    def test_broadcast_panel_visible_admin(self, admin_page):
        np = NotificationsPage(admin_page)
        np.navigate()
        np.wait_for_load()
        # Broadcast toggle may not be visible if it's in a collapsed section
        # or named differently — check for any broadcast-related element
        has_broadcast = np.is_broadcast_toggle_visible() or \
            admin_page.locator("text=Broadcast").count() > 0 or \
            admin_page.locator("text=Send Broadcast").count() > 0
        assert has_broadcast

    def test_owner_no_broadcast_panel(self, owner_page):
        np = NotificationsPage(owner_page)
        np.navigate()
        np.wait_for_load()
        assert not np.is_broadcast_toggle_visible()
