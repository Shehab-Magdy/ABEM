"""API tests for expense file upload."""

from pathlib import Path

import pytest
from playwright.sync_api import APIRequestContext


@pytest.mark.api
@pytest.mark.file_upload
class TestExpenseFileUpload:

    def test_upload_jpeg(
        self,
        admin_api: APIRequestContext,
        seeded_expense,
        test_jpeg_file: Path,
    ):
        eid = seeded_expense["expense"]["id"]
        resp = admin_api.post(
            f"/api/v1/expenses/{eid}/upload/",
            multipart={"file": {"name": "bill.jpg", "mimeType": "image/jpeg",
                                "buffer": test_jpeg_file.read_bytes()}},
        )
        assert resp.status in (200, 201)

    def test_upload_pdf(
        self,
        admin_api: APIRequestContext,
        seeded_expense,
        test_pdf_file: Path,
    ):
        eid = seeded_expense["expense"]["id"]
        resp = admin_api.post(
            f"/api/v1/expenses/{eid}/upload/",
            multipart={"file": {"name": "bill.pdf", "mimeType": "application/pdf",
                                "buffer": test_pdf_file.read_bytes()}},
        )
        assert resp.status in (200, 201)

    def test_upload_exe_rejected(
        self,
        admin_api: APIRequestContext,
        seeded_expense,
        test_exe_file: Path,
    ):
        eid = seeded_expense["expense"]["id"]
        resp = admin_api.post(
            f"/api/v1/expenses/{eid}/upload/",
            multipart={"file": {"name": "malicious.exe",
                                "mimeType": "application/x-msdownload",
                                "buffer": test_exe_file.read_bytes()}},
        )
        assert resp.status == 400

    def test_upload_oversized_file(
        self,
        admin_api: APIRequestContext,
        seeded_expense,
        test_large_file: Path,
    ):
        eid = seeded_expense["expense"]["id"]
        resp = admin_api.post(
            f"/api/v1/expenses/{eid}/upload/",
            multipart={"file": {"name": "large.bin", "mimeType": "image/jpeg",
                                "buffer": test_large_file.read_bytes()}},
        )
        assert resp.status == 413

    def test_upload_empty_body(
        self, admin_api: APIRequestContext, seeded_expense
    ):
        eid = seeded_expense["expense"]["id"]
        resp = admin_api.post(f"/api/v1/expenses/{eid}/upload/", data={})
        assert resp.status == 400

    def test_unauthenticated_upload(
        self,
        unauthenticated_api: APIRequestContext,
        seeded_expense,
        test_jpeg_file: Path,
    ):
        eid = seeded_expense["expense"]["id"]
        resp = unauthenticated_api.post(
            f"/api/v1/expenses/{eid}/upload/",
            multipart={"file": {"name": "bill.jpg", "mimeType": "image/jpeg",
                                "buffer": test_jpeg_file.read_bytes()}},
        )
        assert resp.status == 401

    def test_owner_cannot_upload(
        self,
        owner_api: APIRequestContext,
        seeded_expense,
        test_jpeg_file: Path,
    ):
        eid = seeded_expense["expense"]["id"]
        resp = owner_api.post(
            f"/api/v1/expenses/{eid}/upload/",
            multipart={"file": {"name": "bill.jpg", "mimeType": "image/jpeg",
                                "buffer": test_jpeg_file.read_bytes()}},
        )
        assert resp.status == 403
