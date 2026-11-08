"""Terms acceptance at sign-up and account deletion."""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core.cache import cache, caches
from rest_framework.test import APIClient

from apps.apartments.models import Apartment
from apps.buildings.models import Building, BuildingCoAdmin, UserBuilding
from apps.payments.models import Payment

FIXED_CODE = "123456"

pytestmark = pytest.mark.django_db

SIGNUP = {
    "email": "new@3mara.test",
    "first_name": "منى",
    "last_name": "السكن",
    "role": "owner",
}


@pytest.fixture(autouse=True)
def _clear_ratelimit_cache():
    """
    See test_auth.py: otp/request rate-limit counters live in the
    DB-backed CACHES["ratelimit"] alias (RATELIMIT_USE_CACHE), shared
    across tests reusing the same fixture email.
    """
    cache.clear()
    caches["ratelimit"].clear()


def test_signup_requires_accepting_the_terms(api_client):
    assert (
        api_client.post(
            "/api/v1/auth/self-register/", SIGNUP, format="json"
        ).status_code
        == 400
    )
    resp = api_client.post(
        "/api/v1/auth/self-register/", {**SIGNUP, "accept_terms": False}, format="json"
    )
    assert resp.status_code == 400


def test_signup_records_when_the_terms_were_accepted(api_client, django_user_model):
    resp = api_client.post(
        "/api/v1/auth/self-register/", {**SIGNUP, "accept_terms": True}, format="json"
    )
    assert resp.status_code == 201
    assert (
        django_user_model.objects.get(email="new@3mara.test").terms_accepted_at
        is not None
    )


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def _otp_code_for(email):
    """
    Request a fresh sign-in code for `email` via the public endpoint, with the
    code generator patched to a fixed value (see test_auth.py's module
    docstring for why: rendering the OTP email template crashes under the
    Django test client on this Python version - a pre-existing, unrelated
    environment issue).
    """
    with patch("apps.authentication.otp.generate_otp_code", return_value=FIXED_CODE):
        APIClient().post("/api/v1/auth/otp/request/", {"email": email}, format="json")
    return FIXED_CODE


def test_deleting_an_account_erases_the_person_but_keeps_the_books(
    admin_user, owner_user
):
    owner_user.phone = "01012345678"
    owner_user.save()
    building = Building.objects.create(
        name="Tower", address="1 Nile St", admin=admin_user
    )
    unit = Apartment.objects.create(
        building=building, unit_number="1", owner=owner_user
    )
    unit.owners.add(owner_user)
    UserBuilding.objects.create(user=owner_user, building=building)
    payment = Payment.objects.create(
        apartment=unit,
        amount_paid=Decimal("50.00"),
        payment_date=date.today(),
        recorded_by=admin_user,
    )

    code = _otp_code_for(owner_user.email)
    resp = _client(owner_user).post(
        "/api/v1/auth/delete-account/", {"code": code}, format="json"
    )
    assert resp.status_code == 200

    owner_user.refresh_from_db()
    assert (
        not owner_user.is_active
        and owner_user.phone == ""
        and owner_user.first_name == ""
    )
    assert (
        owner_user.email.endswith("@deleted.invalid")
        and not owner_user.has_usable_password()
    )
    unit.refresh_from_db()
    assert unit.owner is None and not unit.owners.exists()
    assert not UserBuilding.objects.filter(user=owner_user).exists()
    assert Payment.objects.filter(pk=payment.pk).exists()  # financial record stays


def test_wrong_code_does_not_delete(owner_user):
    _otp_code_for(owner_user.email)
    resp = _client(owner_user).post(
        "/api/v1/auth/delete-account/", {"code": "000000"}, format="json"
    )
    assert resp.status_code == 400
    owner_user.refresh_from_db()
    assert owner_user.is_active


def test_primary_admin_must_hand_over_first(admin_user, django_user_model):
    building = Building.objects.create(
        name="Tower", address="1 Nile St", admin=admin_user
    )
    code = _otp_code_for(admin_user.email)
    resp = _client(admin_user).post(
        "/api/v1/auth/delete-account/", {"code": code}, format="json"
    )
    assert resp.status_code == 409
    admin_user.refresh_from_db()
    assert admin_user.is_active

    # a co-admin may leave without blocking anyone
    co_admin = django_user_model.objects.create_user(email="co@abem.test", role="admin")
    BuildingCoAdmin.objects.create(user=co_admin, building=building)
    co_code = _otp_code_for(co_admin.email)
    assert (
        _client(co_admin)
        .post("/api/v1/auth/delete-account/", {"code": co_code}, format="json")
        .status_code
        == 200
    )
    assert not BuildingCoAdmin.objects.filter(user=co_admin).exists()


def test_a_deleted_account_cannot_sign_in(owner_user, api_client):
    code = _otp_code_for(owner_user.email)
    _client(owner_user).post(
        "/api/v1/auth/delete-account/", {"code": code}, format="json"
    )
    resp = api_client.post(
        "/api/v1/auth/otp/verify/",
        {"email": "owner@abem.test", "code": "000000"},
        format="json",
    )
    assert resp.status_code in (400, 403)


def test_api_errors_come_back_in_arabic_when_asked(owner_user):
    client = _client(owner_user)
    resp = client.post(
        "/api/v1/auth/delete-account/",
        {"code": "000000"},
        format="json",
        HTTP_ACCEPT_LANGUAGE="ar",
    )
    assert resp.status_code == 400
    assert (
        resp.data["detail"]
        == "لم يتم العثور على رمز نشط لهذا البريد الإلكتروني. اطلب رمزاً جديداً."
    )


# ── R-31 ─────────────────────────────────────────────────────────────────────


def _resident(owner_user, admin_user, balance="0.00"):
    building = Building.objects.create(
        name="Tower", address="1 Nile St", admin=admin_user
    )
    unit = Apartment.objects.create(
        building=building, unit_number="1", owner=owner_user, balance=Decimal(balance)
    )
    unit.owners.add(owner_user)
    UserBuilding.objects.create(user=owner_user, building=building)
    return building, unit


def _delete(user, **extra):
    code = _otp_code_for(user.email)
    return _client(user).post(
        "/api/v1/auth/delete-account/", {"code": code, **extra}, format="json"
    )


def test_pending_claims_are_rejected_on_deletion(admin_user, owner_user):
    from apps.payments.models import PaymentClaim

    _, unit = _resident(owner_user, admin_user)
    claim = PaymentClaim.objects.create(
        apartment=unit, amount=Decimal("10.00"), created_by=owner_user
    )
    assert _delete(owner_user).status_code == 200
    claim.refresh_from_db()
    assert claim.status == "rejected" and claim.reviewed_at is not None


def test_outstanding_balance_requires_confirmation(admin_user, owner_user):
    _, unit = _resident(owner_user, admin_user, balance="250.00")
    resp = _delete(owner_user)
    assert resp.status_code == 409
    assert Decimal(str(resp.data["balance"])) == Decimal("250.00")
    owner_user.refresh_from_db()
    assert owner_user.is_active
    assert _delete(owner_user, confirm_balance=True).status_code == 200
    owner_user.refresh_from_db()
    assert not owner_user.is_active


def test_leaving_board_member_notifies_the_admin(admin_user, owner_user):
    from apps.notifications.models import Notification

    building, _ = _resident(owner_user, admin_user)
    UserBuilding.objects.filter(user=owner_user, building=building).update(
        board_role="treasurer"
    )
    assert _delete(owner_user).status_code == 200
    assert Notification.objects.filter(
        user=admin_user, metadata__building_id=str(building.pk)
    ).exists()


def test_last_platform_owner_cannot_delete_themselves(django_user_model):
    root = django_user_model.objects.create_superuser(
        email="root@abem.test", password="OwnerPass1!"
    )
    resp = _delete(root)
    assert resp.status_code == 409
    root.refresh_from_db()
    assert root.is_active

    django_user_model.objects.create_superuser(
        email="root2@abem.test", password="OwnerPass1!"
    )
    assert _delete(root).status_code == 200
