"""Forgot / reset password by emailed link."""
import re

import pytest
from django.core import mail

pytestmark = pytest.mark.django_db

NEW_PASSWORD = "NewPass1!x"


def _link_params():
    body = mail.outbox[-1].body
    return re.search(r"uid=([^&\s]+)&token=([^\s]+)", body).groups()


def test_known_email_gets_a_reset_link(api_client, owner_user):
    resp = api_client.post("/api/v1/auth/forgot-password/", {"email": owner_user.email}, format="json")
    assert resp.status_code == 200
    assert len(mail.outbox) == 1 and "reset-password?uid=" in mail.outbox[0].body


def test_unknown_email_looks_the_same_and_sends_nothing(api_client):
    resp = api_client.post("/api/v1/auth/forgot-password/", {"email": "nobody@abem.test"}, format="json")
    assert resp.status_code == 200
    assert mail.outbox == []


def test_reset_link_sets_the_new_password_once(api_client, owner_user):
    api_client.post("/api/v1/auth/forgot-password/", {"email": owner_user.email}, format="json")
    uid, token = _link_params()
    body = {"uid": uid, "token": token, "password": NEW_PASSWORD, "confirm_password": NEW_PASSWORD}

    assert api_client.post("/api/v1/auth/reset-password/", body, format="json").status_code == 200
    owner_user.refresh_from_db()
    assert owner_user.check_password(NEW_PASSWORD)
    # the token is single-use: the password changed, so it no longer validates
    assert api_client.post("/api/v1/auth/reset-password/", body, format="json").status_code == 400


def test_bad_token_and_weak_password_are_rejected(api_client, owner_user):
    api_client.post("/api/v1/auth/forgot-password/", {"email": owner_user.email}, format="json")
    uid, token = _link_params()
    bad = api_client.post(
        "/api/v1/auth/reset-password/",
        {"uid": uid, "token": "wrong", "password": NEW_PASSWORD, "confirm_password": NEW_PASSWORD},
        format="json",
    )
    weak = api_client.post(
        "/api/v1/auth/reset-password/",
        {"uid": uid, "token": token, "password": "short", "confirm_password": "short"},
        format="json",
    )
    assert bad.status_code == 400 and weak.status_code == 400
