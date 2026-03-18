"""UI tests for export downloads."""
import pytest
from pages.exports_page import ExportsPage
from config.settings import settings


@pytest.mark.ui
@pytest.mark.exports
class TestExportDownloadUI:
    def test_owner_no_export_buttons(self, owner_page):
        ep = ExportsPage(owner_page)
        ep.navigate()
        ep.wait_for_load()
        assert not ep.is_csv_button_visible()
