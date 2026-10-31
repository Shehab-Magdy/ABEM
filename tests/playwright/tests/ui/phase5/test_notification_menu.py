"""UI tests for the header notification popover (bell -> panel with tabs, infinite scroll, mark all read)."""

import re

import pytest
from playwright.sync_api import expect

from fixtures.phase5 import API, unwrap
from pages.header_page import HeaderPage
from pages.notifications_page import NotificationsPage
from utils.data_factory import build_broadcast


def _broadcast(admin_api, building_id, n):
    for i in range(n):
        resp = admin_api.post(f"{API}/notifications/broadcast/", data=build_broadcast(building_id))
        assert resp.status in (200, 201), resp.text()


@pytest.mark.ui
@pytest.mark.notifications
@pytest.mark.phase5
class TestNotificationMenu:
    def test_bell_opens_a_popover_instead_of_navigating(self, admin_page):
        header = HeaderPage(admin_page)
        header.goto("/dashboard")
        header.open_menu()
        expect(header.panel).to_be_visible()
        assert admin_page.url.rstrip("/").endswith("/dashboard")
        expect(header.tab("all")).to_be_visible()
        expect(header.tab("unread")).to_be_visible()
        assert header.tab("all").get_attribute("aria-selected") == "true"

    def test_escape_closes_the_popover(self, admin_page):
        header = HeaderPage(admin_page)
        header.goto("/dashboard")
        header.open_menu()
        header.close_menu()
        expect(header.panel).to_be_hidden()

    def test_open_center_link_goes_to_notifications_page(self, admin_page):
        header = HeaderPage(admin_page)
        header.goto("/dashboard")
        header.open_menu()
        header.open_center()
        admin_page.wait_for_url(re.compile(r".*/notifications$"))
        expect(admin_page.get_by_test_id("mark-all-read-btn")).to_be_visible()

    def test_infinite_scroll_loads_ten_per_page(self, admin_api, member_owner, member_owner_page):
        _broadcast(admin_api, member_owner["building"]["id"], 12)
        header = HeaderPage(member_owner_page)
        header.goto("/dashboard")
        header.open_menu()
        expect(header.items.first).to_be_visible()
        expect(header.items).to_have_count(10)
        header.scroll_list_to_end()
        expect(header.items).to_have_count(12)
        expect(header.panel.get_by_test_id("notification-menu-sentinel")).to_have_count(0)

    def test_unread_tab_lists_only_unread_and_all_tab_marks_them(self, admin_api, member_owner, member_owner_page):
        _broadcast(admin_api, member_owner["building"]["id"], 3)
        header = HeaderPage(member_owner_page)
        header.goto("/dashboard")
        header.open_menu()
        expect(header.items.first).to_be_visible()
        header.select_tab("unread")
        expect(header.items.first).to_be_visible()
        assert header.items.count() == header.unread_dots.count()
        assert header.tab("unread").get_attribute("aria-selected") == "true"

    def test_mark_all_read_clears_badge_and_empties_unread_tab(self, admin_api, member_owner, member_owner_page):
        _broadcast(admin_api, member_owner["building"]["id"], 3)
        header = HeaderPage(member_owner_page)
        header.goto("/dashboard")
        expect(member_owner_page.get_by_test_id("notification-badge")).to_be_visible()
        assert header.badge_count() >= 3
        header.open_menu()
        header.mark_all_read_in_menu()
        expect(header.unread_dots).to_have_count(0)
        expect(member_owner_page.get_by_test_id("notification-badge")).to_have_count(0)
        header.select_tab("unread")
        expect(header.empty_state()).to_be_visible()
        # the server agrees
        assert member_owner["api"].get(f"{API}/notifications/unread-count/").json()["count"] == 0
        # read ones are still in the All tab
        header.select_tab("all")
        expect(header.items.first).to_be_visible()

    def test_mark_all_read_survives_reload(self, admin_api, member_owner, member_owner_page):
        _broadcast(admin_api, member_owner["building"]["id"], 2)
        header = HeaderPage(member_owner_page)
        header.goto("/dashboard")
        header.open_menu()
        header.mark_all_read_in_menu()
        expect(header.unread_dots).to_have_count(0)
        member_owner_page.reload()
        header.language_button.wait_for(state="visible")
        expect(member_owner_page.get_by_test_id("notification-badge")).to_have_count(0)

    def test_notification_center_page_mark_all_read(self, admin_api, member_owner, member_owner_page):
        _broadcast(admin_api, member_owner["building"]["id"], 2)
        center = NotificationsPage(member_owner_page)
        center.navigate()
        center.wait_for_load()
        expect(center.mark_all_read_button()).to_be_enabled()
        center.mark_all_read()
        expect(center.mark_all_read_button()).to_be_disabled()
        assert member_owner["api"].get(f"{API}/notifications/unread-count/").json()["count"] == 0

    @pytest.mark.tenant_isolation
    def test_menu_only_shows_the_signed_in_users_notifications(self, admin_api, member_owner, member_owner_page):
        _broadcast(admin_api, member_owner["building"]["id"], 1)
        mine = {n["title"] for n in unwrap(member_owner["api"].get(f"{API}/notifications/").json())}
        header = HeaderPage(member_owner_page)
        header.goto("/dashboard")
        header.open_menu()
        expect(header.items.first).to_be_visible()
        shown = header.items.all_inner_texts()
        assert shown and all(any(title in text for title in mine) for text in shown)
