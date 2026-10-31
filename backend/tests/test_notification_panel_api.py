"""Header notification panel API: unread filter, page-size-10 pagination, unread count, mark-all-read."""

import pytest
from apps.notifications.models import (Notification, NotificationChannel,
                                       NotificationType)
from rest_framework.test import APIClient

URL = "/api/v1/notifications/"


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def _make(user, n, is_read=False):
    return [
        Notification.objects.create(
            user=user,
            notification_type=NotificationType.MESSAGE,
            channel=NotificationChannel.IN_APP,
            title=f"n{i}",
            body="body",
            is_read=is_read,
        )
        for i in range(n)
    ]


@pytest.mark.django_db
def test_page_size_10_paginates_without_duplicates(owner_user):
    _make(owner_user, 25)
    client = _client(owner_user)
    first = client.get(URL, {"page_size": 10}).json()
    assert first["count"] == 25 and len(first["results"]) == 10 and first["next"]
    seen = {r["id"] for r in first["results"]}
    for page in (2, 3):
        data = client.get(URL, {"page_size": 10, "page": page}).json()
        ids = {r["id"] for r in data["results"]}
        assert not ids & seen
        seen |= ids
    assert len(seen) == 25
    assert data["next"] is None and len(data["results"]) == 5


@pytest.mark.django_db
def test_unread_filter_accepts_unread_and_is_read(owner_user):
    _make(owner_user, 3)
    _make(owner_user, 2, is_read=True)
    client = _client(owner_user)
    assert client.get(URL, {"unread": "true"}).json()["count"] == 3
    assert client.get(URL, {"is_read": "false"}).json()["count"] == 3
    assert client.get(URL, {"is_read": "true"}).json()["count"] == 2
    assert client.get(URL).json()["count"] == 5


@pytest.mark.django_db
def test_unread_count_is_scoped_to_caller(owner_user, admin_user):
    _make(owner_user, 4)
    _make(owner_user, 2, is_read=True)
    _make(admin_user, 7)
    assert _client(owner_user).get(URL + "unread-count/").json() == {"count": 4}
    assert _client(admin_user).get(URL + "unread-count/").json() == {"count": 7}


@pytest.mark.django_db
def test_unread_count_requires_auth():
    assert APIClient().get(URL + "unread-count/").status_code == 401


@pytest.mark.django_db
def test_mark_all_read_only_touches_own_notifications(owner_user, admin_user):
    _make(owner_user, 3)
    _make(admin_user, 2)
    resp = _client(owner_user).post(URL + "mark-all-read/")
    assert resp.status_code == 200
    assert resp.json()["updated"] == 3
    assert Notification.objects.filter(user=owner_user, is_read=False).count() == 0
    assert Notification.objects.filter(user=admin_user, is_read=False).count() == 2
    assert _client(owner_user).post(URL + "mark-all-read/").json()["updated"] == 0


@pytest.mark.django_db
def test_mark_all_read_requires_auth():
    assert APIClient().post(URL + "mark-all-read/").status_code == 401


@pytest.mark.django_db
def test_cannot_see_or_mark_other_users_notification(owner_user, admin_user):
    other = _make(admin_user, 1)[0]
    client = _client(owner_user)
    assert client.get(f"{URL}{other.id}/").status_code == 404
    assert client.post(f"{URL}{other.id}/read/").status_code == 404
    other.refresh_from_db()
    assert other.is_read is False
