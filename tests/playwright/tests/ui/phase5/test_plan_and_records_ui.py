"""UI tests: the plan page's yearly discount, and the whole-building export button on Records."""

import io
import re
import zipfile

import pytest
from playwright.sync_api import expect

from config.settings import settings
from pages.plan_page import PlanPage
from pages.records_page import RecordsPage


@pytest.mark.ui
@pytest.mark.phase5
class TestPlanYearlyDiscount:
    def test_monthly_view_advertises_the_yearly_saving(self, admin_page):
        plan = PlanPage(admin_page)
        plan.navigate_and_wait()
        expect(plan.monthly_hints().first).to_be_visible()
        assert plan.line_through_elements() == []

    def test_yearly_view_shows_struck_through_price_and_save_chip(self, admin_page):
        plan = PlanPage(admin_page)
        plan.navigate_and_wait()
        plan.choose_period("Yearly")
        expect(plan.saving_chips().first).to_be_visible()
        assert 0 < plan.displayed_percent() < 100
        struck = plan.line_through_elements()
        assert struck, "the 12-month list price must be struck through"
        assert all(re.search(r"\d", s) for s in struck)

    def test_yearly_saving_percent_matches_the_hint(self, admin_page):
        plan = PlanPage(admin_page)
        plan.navigate_and_wait()
        hint = plan.monthly_hints().first.inner_text()
        monthly_pct = int(re.search(r"(\d+)%", hint).group(1))
        plan.choose_period("Yearly")
        assert plan.displayed_percent() == monthly_pct

    def test_owner_cannot_open_the_plan_page(self, owner_page):
        owner_page.goto(f"{settings.BASE_URL}/plan")
        owner_page.wait_for_load_state("networkidle")
        assert owner_page.get_by_role("button", name="Yearly", exact=True).count() == 0


@pytest.mark.ui
@pytest.mark.exports
@pytest.mark.phase5
class TestBuildingExportButton:
    def test_admin_downloads_an_xlsx(self, admin_page, create_building):
        building = create_building(num_apartments=2, num_stores=0)
        records = RecordsPage(admin_page)
        records.navigate_and_wait()
        records.choose_building(building["name"])
        expect(records.export_button()).to_be_visible()
        expect(records.export_button()).to_have_text(re.compile("Download full building export"))
        download = records.download_building_export()
        assert download.suggested_filename.endswith(".xlsx")
        assert building["id"] in download.suggested_filename
        path = download.path()
        with open(path, "rb") as fh:
            body = fh.read()
        assert body[:2] == b"PK"
        with zipfile.ZipFile(io.BytesIO(body)) as z:
            assert "xl/workbook.xml" in z.namelist()

    def test_owner_has_no_export_button(self, owner_page):
        records = RecordsPage(owner_page)
        records.navigate_and_wait()
        expect(records.export_button()).to_have_count(0)
