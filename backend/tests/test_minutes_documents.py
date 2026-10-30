"""Meeting minutes and the building's documents: the secretary and admins write, members read."""
from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.buildings.models import Building, UserBuilding

pytestmark = pytest.mark.django_db


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture(autouse=True)
def _tmp_media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    settings.DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"


@pytest.fixture
def building(admin_user):
    return Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user)


@pytest.fixture
def people(building, django_user_model):
    secretary = django_user_model.objects.create_user(email="sec@abem.test", password="SPass1!xxx", role="owner")
    resident = django_user_model.objects.create_user(email="res@abem.test", password="RPass1!xxx", role="owner")
    UserBuilding.objects.create(user=secretary, building=building, board_role="secretary")
    UserBuilding.objects.create(user=resident, building=building)
    return secretary, resident


MEETING = {"title": "General assembly", "held_on": "2026-10-20", "attendees": "12 owners", "agenda": "Elevator", "notes": "Discussed offers", "decisions": "Replace the elevator"}


def _meeting(user, building, **extra):
    return _client(user).post("/api/v1/governance/meetings/", {"building_id": str(building.pk), **MEETING, **extra}, format="json")


def test_secretary_and_admin_record_minutes_and_members_read_them(admin_user, building, people):
    secretary, resident = people
    assert _meeting(secretary, building).status_code == 201
    assert _meeting(admin_user, building, title="Follow-up").status_code == 201
    titles = [m["title"] for m in _client(resident).get("/api/v1/governance/meetings/").data["results"]]
    assert sorted(titles) == ["Follow-up", "General assembly"]


def test_ordinary_residents_cannot_write_minutes(building, people):
    _, resident = people
    assert _meeting(resident, building).status_code == 403


def test_a_secretary_of_another_building_cannot_write_here(building, people, django_user_model):
    other_admin = django_user_model.objects.create_user(email="oa@abem.test", password="OPass1!xxx", role="admin")
    other = Building.objects.create(name="Other", address="9 Elm", admin=other_admin)
    outsider = django_user_model.objects.create_user(email="o@abem.test", password="OPass1!xxx", role="owner")
    UserBuilding.objects.create(user=outsider, building=other, board_role="secretary")
    assert _meeting(outsider, building).status_code == 403
    assert _client(outsider).get("/api/v1/governance/meetings/").data["results"] == []   # and sees none of this building's


def test_secretary_edits_and_residents_cannot(admin_user, building, people):
    secretary, resident = people
    meeting_id = _meeting(secretary, building).data["id"]
    assert _client(secretary).patch(f"/api/v1/governance/meetings/{meeting_id}/", {"decisions": "Postponed"}, format="json").status_code == 200
    assert _client(resident).patch(f"/api/v1/governance/meetings/{meeting_id}/", {"decisions": "Hacked"}, format="json").status_code == 403
    assert _client(resident).delete(f"/api/v1/governance/meetings/{meeting_id}/").status_code == 403


def test_minutes_download_as_pdf_in_both_languages(admin_user, building, people):
    meeting_id = _meeting(admin_user, building).data["id"]
    for lang in ("ar", "en"):
        admin_user.preferred_language = lang
        admin_user.save()
        resp = _client(admin_user).get(f"/api/v1/governance/meetings/{meeting_id}/pdf/")
        assert resp.status_code == 200 and resp.content.startswith(b"%PDF")


def _upload(user, building, name="contract.pdf", content_type="application/pdf", body=b"%PDF-1.4 test"):
    return _client(user).post(
        "/api/v1/governance/documents/",
        {"building_id": str(building.pk), "title": "Elevator contract", "kind": "contract", "file": SimpleUploadedFile(name, body, content_type=content_type)},
        format="multipart",
    )


def test_secretary_uploads_a_document_and_members_can_open_it(admin_user, building, people):
    secretary, resident = people
    resp = _upload(secretary, building)
    assert resp.status_code == 201 and resp.data["mime_type"] == "application/pdf" and resp.data["url"]
    listed = _client(resident).get("/api/v1/governance/documents/").data["results"]
    assert [d["title"] for d in listed] == ["Elevator contract"]


def test_only_pdf_and_images_and_only_by_the_secretary_or_admins(building, people):
    secretary, resident = people
    assert _upload(secretary, building, "x.exe", "application/x-msdownload").status_code == 400
    assert _upload(resident, building).status_code == 403


def test_oversized_files_are_refused(building, people, settings):
    settings.MAX_UPLOAD_SIZE_MB = 1
    assert _upload(people[0], building, body=b"0" * (1024 * 1024 + 1)).status_code == 400


def test_documents_can_be_removed_by_the_secretary_only(building, people):
    secretary, resident = people
    doc_id = _upload(secretary, building).data["id"]
    assert _client(resident).delete(f"/api/v1/governance/documents/{doc_id}/").status_code == 403
    assert _client(secretary).delete(f"/api/v1/governance/documents/{doc_id}/").status_code == 204
