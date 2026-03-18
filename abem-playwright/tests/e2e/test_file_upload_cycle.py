"""E2E Journey 6: Bill image upload full cycle."""
from pathlib import Path
import pytest
from playwright.sync_api import Playwright
from utils.data_factory import build_building, build_expense
from config.settings import settings


@pytest.mark.e2e
@pytest.mark.file_upload
class TestFileUploadCycle:

    def test_upload_lifecycle(
        self, playwright: Playwright, admin_api, admin_token: str,
        test_jpeg_file: Path, test_exe_file: Path, test_large_file: Path,
    ):
        building = admin_api.post(
            "/api/v1/buildings/", data=build_building(num_apartments=1, num_stores=0)
        ).json()
        bid = building["id"]

        # Separate context for multipart uploads (no Content-Type header)
        upload_ctx = playwright.request.new_context(
            base_url=settings.API_BASE_URL,
            extra_http_headers={"Authorization": f"Bearer {admin_token}"},
        )
        try:
            cats = admin_api.get("/api/v1/expenses/categories/", params={"building_id": bid}).json()
            cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
            expense = admin_api.post("/api/v1/expenses/", data=build_expense(
                bid, cat_list[0]["id"], amount="100"
            )).json()
            eid = expense["id"]

            # Upload valid JPEG
            resp = upload_ctx.post(
                f"/api/v1/expenses/{eid}/upload/",
                multipart={"file": {"name": "bill.jpg", "mimeType": "image/jpeg",
                                    "buffer": test_jpeg_file.read_bytes()}},
            )
            assert resp.status in (200, 201), f"JPEG upload: {resp.status} {resp.text()}"

            # Upload .exe → 400
            resp = upload_ctx.post(
                f"/api/v1/expenses/{eid}/upload/",
                multipart={"file": {"name": "bad.exe", "mimeType": "application/x-msdownload",
                                    "buffer": test_exe_file.read_bytes()}},
            )
            assert resp.status == 400

            # Upload oversized → 413
            resp = upload_ctx.post(
                f"/api/v1/expenses/{eid}/upload/",
                multipart={"file": {"name": "big.bin", "mimeType": "image/jpeg",
                                    "buffer": test_large_file.read_bytes()}},
            )
            assert resp.status == 413

        finally:
            upload_ctx.dispose()
            admin_api.delete(f"/api/v1/buildings/{bid}/")
