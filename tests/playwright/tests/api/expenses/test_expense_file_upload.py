"""API tests for expense file upload."""

from pathlib import Path

import pytest
from playwright.sync_api import APIRequestContext, Playwright

from config.settings import settings


@pytest.mark.api
@pytest.mark.file_upload
class TestExpenseFileUpload:
    """Upload endpoint requires multipart/form-data, not application/json.

    We create a separate API context without Content-Type header for uploads.
    """

    def _upload_ctx(self, playwright: Playwright, token: str) -> APIRequestContext:
        """Create API context without Content-Type (let Playwright set multipart)."""
        return playwright.request.new_context(
            base_url=settings.API_BASE_URL,
            extra_http_headers={"Authorization": f"Bearer {token}"},
        )

    def test_upload_jpeg(
        self, playwright: Playwright, admin_token: str,
        seeded_expense, test_jpeg_file: Path,
    ):
        eid = seeded_expense["expense"]["id"]
        ctx = self._upload_ctx(playwright, admin_token)
        try:
            resp = ctx.post(
                f"/api/v1/expenses/{eid}/upload/",
                multipart={"file": {
                    "name": "bill.jpg",
                    "mimeType": "image/jpeg",
                    "buffer": test_jpeg_file.read_bytes(),
                }},
            )
            assert resp.status in (200, 201), f"Upload JPEG failed: {resp.status} {resp.text()}"
        finally:
            ctx.dispose()

    def test_upload_pdf(
        self, playwright: Playwright, admin_token: str,
        seeded_expense, test_pdf_file: Path,
    ):
        eid = seeded_expense["expense"]["id"]
        ctx = self._upload_ctx(playwright, admin_token)
        try:
            resp = ctx.post(
                f"/api/v1/expenses/{eid}/upload/",
                multipart={"file": {
                    "name": "bill.pdf",
                    "mimeType": "application/pdf",
                    "buffer": test_pdf_file.read_bytes(),
                }},
            )
            assert resp.status in (200, 201)
        finally:
            ctx.dispose()

    def test_upload_exe_rejected(
        self, playwright: Playwright, admin_token: str,
        seeded_expense, test_exe_file: Path,
    ):
        eid = seeded_expense["expense"]["id"]
        ctx = self._upload_ctx(playwright, admin_token)
        try:
            resp = ctx.post(
                f"/api/v1/expenses/{eid}/upload/",
                multipart={"file": {
                    "name": "malicious.exe",
                    "mimeType": "application/x-msdownload",
                    "buffer": test_exe_file.read_bytes(),
                }},
            )
            assert resp.status == 400
        finally:
            ctx.dispose()

    def test_upload_oversized_file(
        self, playwright: Playwright, admin_token: str,
        seeded_expense, test_large_file: Path,
    ):
        eid = seeded_expense["expense"]["id"]
        ctx = self._upload_ctx(playwright, admin_token)
        try:
            resp = ctx.post(
                f"/api/v1/expenses/{eid}/upload/",
                multipart={"file": {
                    "name": "large.bin",
                    "mimeType": "image/jpeg",
                    "buffer": test_large_file.read_bytes(),
                }},
            )
            assert resp.status == 413
        finally:
            ctx.dispose()

    def test_upload_empty_body(
        self, playwright: Playwright, admin_token: str, seeded_expense,
    ):
        eid = seeded_expense["expense"]["id"]
        ctx = self._upload_ctx(playwright, admin_token)
        try:
            resp = ctx.post(f"/api/v1/expenses/{eid}/upload/", data={})
            assert resp.status in (400, 415), f"Expected 400/415, got {resp.status}"
        finally:
            ctx.dispose()

    def test_unauthenticated_upload(
        self, playwright: Playwright, seeded_expense, test_jpeg_file: Path,
    ):
        eid = seeded_expense["expense"]["id"]
        ctx = playwright.request.new_context(base_url=settings.API_BASE_URL)
        try:
            resp = ctx.post(
                f"/api/v1/expenses/{eid}/upload/",
                multipart={"file": {
                    "name": "bill.jpg",
                    "mimeType": "image/jpeg",
                    "buffer": test_jpeg_file.read_bytes(),
                }},
            )
            assert resp.status == 401
        finally:
            ctx.dispose()

    def test_owner_cannot_upload(
        self, playwright: Playwright, owner_token: str,
        seeded_expense, test_jpeg_file: Path,
    ):
        eid = seeded_expense["expense"]["id"]
        ctx = self._upload_ctx(playwright, owner_token)
        try:
            resp = ctx.post(
                f"/api/v1/expenses/{eid}/upload/",
                multipart={"file": {
                    "name": "bill.jpg",
                    "mimeType": "image/jpeg",
                    "buffer": test_jpeg_file.read_bytes(),
                }},
            )
            assert resp.status == 403
        finally:
            ctx.dispose()
