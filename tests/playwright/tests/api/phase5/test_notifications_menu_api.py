"""API tests for the endpoints behind the header notification menu: unread filter, page_size, unread-count,
mark-all-read. Every call is scoped to the caller."""

import pytest

from fixtures.phase5 import API, unwrap
from utils.data_factory import build_broadcast


def _broadcast(admin_api, building_id, n=1):
    for _ in range(n):
        resp = admin_api.post(f"{API}/notifications/broadcast/", data=build_broadcast(building_id))
        assert resp.status in (200, 201), resp.text()


@pytest.mark.api
@pytest.mark.notifications
@pytest.mark.phase5
class TestNotificationMenuEndpoints:
    def test_unread_count_matches_unread_list(self, admin_api, member_owner):
        _broadcast(admin_api, member_owner["building"]["id"], 3)
        count = member_owner["api"].get(f"{API}/notifications/unread-count/").json()["count"]
        listing = member_owner["api"].get(f"{API}/notifications/", params={"unread": "true", "page_size": 100}).json()
        assert count >= 3
        assert listing["count"] == count
        assert all(n["is_read"] is False for n in unwrap(listing))

    def test_unread_filter_excludes_read(self, admin_api, member_owner):
        _broadcast(admin_api, member_owner["building"]["id"], 2)
        first = unwrap(member_owner["api"].get(f"{API}/notifications/", params={"unread": "true"}).json())[0]
        assert member_owner["api"].post(f"{API}/notifications/{first['id']}/read/").status == 200
        ids = {n["id"] for n in unwrap(
            member_owner["api"].get(f"{API}/notifications/", params={"unread": "true", "page_size": 100}).json()
        )}
        assert first["id"] not in ids
        all_ids = {n["id"] for n in unwrap(
            member_owner["api"].get(f"{API}/notifications/", params={"page_size": 100}).json()
        )}
        assert first["id"] in all_ids

    def test_page_size_ten_paginates_without_repeats(self, admin_api, member_owner):
        _broadcast(admin_api, member_owner["building"]["id"], 12)
        page1 = member_owner["api"].get(f"{API}/notifications/", params={"unread": "true", "page_size": 10}).json()
        assert len(page1["results"]) == 10
        assert page1["next"], "12+ unread notifications must have a second page"
        page2 = member_owner["api"].get(
            f"{API}/notifications/", params={"unread": "true", "page_size": 10, "page": 2}
        ).json()
        assert len(page2["results"]) >= 2
        ids1 = [n["id"] for n in page1["results"]]
        ids2 = [n["id"] for n in page2["results"]]
        assert not set(ids1) & set(ids2)
        stamps = [n["created_at"] for n in page1["results"]]
        assert stamps == sorted(stamps, reverse=True), "newest first"

    def test_mark_all_read_clears_the_callers_unread(self, admin_api, member_owner):
        _broadcast(admin_api, member_owner["building"]["id"], 3)
        resp = member_owner["api"].post(f"{API}/notifications/mark-all-read/")
        assert resp.status == 200
        assert resp.json()["updated"] >= 3
        assert member_owner["api"].get(f"{API}/notifications/unread-count/").json()["count"] == 0
        listing = member_owner["api"].get(f"{API}/notifications/", params={"unread": "true"}).json()
        assert listing["count"] == 0
        # read notifications are kept
        assert member_owner["api"].get(f"{API}/notifications/").json()["count"] >= 3

    def test_mark_all_read_is_idempotent(self, member_owner):
        member_owner["api"].post(f"{API}/notifications/mark-all-read/")
        again = member_owner["api"].post(f"{API}/notifications/mark-all-read/")
        assert again.status == 200
        assert again.json()["updated"] == 0

    def test_requires_authentication(self, unauthenticated_api):
        assert unauthenticated_api.get(f"{API}/notifications/unread-count/").status == 401
        assert unauthenticated_api.post(f"{API}/notifications/mark-all-read/").status == 401


@pytest.mark.api
@pytest.mark.notifications
@pytest.mark.phase5
@pytest.mark.tenant_isolation
class TestNotificationScoping:
    def test_mark_all_read_only_touches_the_caller(self, admin_api, member_owner, create_user, playwright):
        """A second member of the same building keeps their unread notifications."""
        from fixtures.phase5 import bearer_context, login_tokens

        other = create_user(role="owner")
        bid = member_owner["building"]["id"]
        assert admin_api.post(f"{API}/buildings/{bid}/assign-user/", data={"user_id": other["id"]}).status in (200, 201)
        other_api = bearer_context(playwright, login_tokens(playwright, other["email"], other["_password"])["access"])
        try:
            _broadcast(admin_api, bid, 2)
            before = other_api.get(f"{API}/notifications/unread-count/").json()["count"]
            assert before >= 2
            member_owner["api"].post(f"{API}/notifications/mark-all-read/")
            assert other_api.get(f"{API}/notifications/unread-count/").json()["count"] == before
        finally:
            other_api.dispose()

    def test_user_cannot_read_anothers_notification(self, admin_api, member_owner):
        _broadcast(admin_api, member_owner["building"]["id"], 1)
        mine = unwrap(member_owner["api"].get(f"{API}/notifications/").json())[0]
        assert admin_api.get(f"{API}/notifications/{mine['id']}/").status == 404
        assert admin_api.post(f"{API}/notifications/{mine['id']}/read/").status == 404

    def test_admin_list_never_contains_owner_rows(self, admin_api, member_owner):
        _broadcast(admin_api, member_owner["building"]["id"], 1)
        mine = {n["id"] for n in unwrap(member_owner["api"].get(f"{API}/notifications/").json())}
        theirs = {n["id"] for n in unwrap(admin_api.get(f"{API}/notifications/", params={"page_size": 200}).json())}
        assert not mine & theirs
