"""E2E Journey 6: Bill image upload full cycle."""
from pathlib import Path
import pytest
from utils.data_factory import build_building, build_expense
from config.settings import settings


@pytest.mark.e2e
@pytest.mark.file_upload
class TestFileUploadCycle:

    def test_upload_lifecycle(self, admin_api, test_jpeg_file: Path, test_exe_file: Path, test_large_file: Path):
        building = admin_api.post(
            "/api/v1/buildings/", data=build_building(num_apartments=1, num_stores=0)
        ).json()
        bid = building["id"]
        try:
            cats = admin_api.get("/api/v1/expenses/categories/", params={"building_id": bid}).json()
            cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats
            expense = admin_api.post("/api/v1/expenses/", data=build_expense(
                bid, cat_list[0]["id"], amount="100"
            )).json()
            eid = expense["id"]

            # Upload valid JPEG
            resp = admin_api.post(
                f"/api/v1/expenses/{eid}/upload/",
                multipart={"file": {"name": "bill.jpg", "mimeType": "image/jpeg",
                                    "buffer": test_jpeg_file.read_bytes()}},
            )
            assert resp.status in (200, 201)

            # Upload .exe → 400
            resp = admin_api.post(
                f"/api/v1/expenses/{eid}/upload/",
                multipart={"file": {"name": "bad.exe", "mimeType": "application/x-msdownload",
                                    "buffer": test_exe_file.read_bytes()}},
            )
            assert resp.status == 400

            # Upload oversized → 413
            resp = admin_api.post(
                f"/api/v1/expenses/{eid}/upload/",
                multipart={"file": {"name": "big.bin", "mimeType": "image/jpeg",
                                    "buffer": test_large_file.read_bytes()}},
            )
            assert resp.status == 413

        finally:
            admin_api.delete(f"/api/v1/buildings/{bid}/")
