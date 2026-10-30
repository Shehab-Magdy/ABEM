"""Support tickets: anyone signed in can report a problem and sees only their own."""
import io

import pytest
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient

from apps.support.models import SupportTicket

pytestmark = pytest.mark.django_db
URL = "/api/v1/support/tickets/"


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def _png():
    buf = io.BytesIO()
    Image.new("RGB", (4, 4), "white").save(buf, "PNG")
    return SimpleUploadedFile("shot.png", buf.getvalue(), content_type="image/png")


def test_report_with_screenshot_is_saved_and_emailed(owner_user, settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    payload = {"message": "The lift page is blank", "screenshot": _png()}
    resp = _client(owner_user).post(URL, payload, format="multipart")
    assert resp.status_code == 201
    ticket = SupportTicket.objects.get()
    assert ticket.user == owner_user and ticket.screenshot
    assert len(mail.outbox) == 1 and owner_user.email in mail.outbox[0].subject


def test_report_without_screenshot_and_short_message(owner_user):
    assert _client(owner_user).post(URL, {"message": "Cannot pay my share"}, format="json").status_code == 201
    assert _client(owner_user).post(URL, {"message": "no"}, format="json").status_code == 400


def test_rejects_files_that_are_not_images(owner_user, tmp_path, settings):
    settings.MEDIA_ROOT = str(tmp_path)
    bad = SimpleUploadedFile("x.png", b"not an image", content_type="image/png")
    payload = {"message": "Broken thing here", "screenshot": bad}
    assert _client(owner_user).post(URL, payload, format="multipart").status_code == 400


def test_users_only_see_their_own_tickets(owner_user, admin_user):
    SupportTicket.objects.create(user=owner_user, message="mine")
    SupportTicket.objects.create(user=admin_user, message="theirs")
    results = _client(owner_user).get(URL).data
    results = results["results"] if isinstance(results, dict) else results
    assert [t["message"] for t in results] == ["mine"]


def test_must_be_signed_in():
    assert APIClient().post(URL, {"message": "hello there"}, format="json").status_code == 401
