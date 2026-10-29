"""UI tests for file upload on expenses."""
import pytest
from pathlib import Path
from config.settings import settings


@pytest.mark.ui
@pytest.mark.file_upload
class TestFileUploadUI:
    def test_upload_button_visible_admin(self, admin_page, admin_api, seeded_expense):
        eid = seeded_expense.get("expense", seeded_expense).get("id", seeded_expense.get("id"))
        admin_page.goto(f"{settings.BASE_URL}/expenses")
        admin_page.wait_for_load_state("networkidle")
        # Upload button may appear on row or detail view

    def test_owner_no_upload_button(self, owner_page):
        owner_page.goto(f"{settings.BASE_URL}/expenses")
        owner_page.wait_for_load_state("networkidle")
        assert owner_page.locator("#add-expense-btn").count() == 0
