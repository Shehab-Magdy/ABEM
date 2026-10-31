"""UI tests for the header language button: flips dir, persists to the profile, survives reload. Includes the
Arabic / RTL checks. The suite's English init script is NOT used here (raw_admin_page) so persistence is real,
and the profile language is always put back to English afterwards."""

import re

import pytest
from playwright.sync_api import expect

from fixtures.phase5 import API
from pages.buildings_page import BuildingsPage
from pages.data_table_page import DataTablePage
from pages.header_page import HeaderPage
from pages.payments_page import PaymentsPage


@pytest.fixture
def restore_english(admin_api):
    """Whatever a test does, the shared admin account ends up on English."""
    yield
    resp = admin_api.patch(f"{API}/auth/profile/", data={"preferred_language": "en"})
    assert resp.status == 200, resp.text()


def _profile_language(admin_api) -> str:
    return admin_api.get(f"{API}/auth/profile/").json()["preferred_language"]


@pytest.mark.ui
@pytest.mark.i18n
@pytest.mark.phase5
class TestLanguageSwitch:
    def test_button_shows_the_other_language(self, raw_admin_page, restore_english):
        header = HeaderPage(raw_admin_page)
        header.goto("/dashboard")
        assert header.language_button_text() == "ع"
        header.expect_direction("ltr")

    def test_switch_to_arabic_flips_direction_and_label(self, raw_admin_page, restore_english):
        header = HeaderPage(raw_admin_page)
        header.goto("/dashboard")
        header.click_language_switch()
        header.expect_direction("rtl")
        expect(header.language_button).to_have_text("EN")
        expect(raw_admin_page.locator("html")).to_have_attribute("lang", "ar")

    def test_switch_back_to_english(self, raw_admin_page, restore_english):
        header = HeaderPage(raw_admin_page)
        header.goto("/dashboard")
        header.click_language_switch()
        header.expect_direction("rtl")
        header.click_language_switch()
        header.expect_direction("ltr")
        expect(header.language_button).to_have_text("ع")

    def test_choice_is_saved_to_the_profile(self, raw_admin_page, admin_api, restore_english):
        header = HeaderPage(raw_admin_page)
        header.goto("/dashboard")
        with raw_admin_page.expect_response(
            lambda r: "/auth/profile/" in r.url and r.request.method == "PATCH"
        ) as info:
            header.click_language_switch()
        assert info.value.ok
        assert _profile_language(admin_api) == "ar"

    def test_arabic_persists_after_reload(self, raw_admin_page, restore_english):
        header = HeaderPage(raw_admin_page)
        header.goto("/dashboard")
        header.click_language_switch()
        header.expect_direction("rtl")
        raw_admin_page.wait_for_timeout(500)  # let the profile PATCH finish before leaving
        raw_admin_page.reload()
        header.language_button.wait_for(state="visible")
        header.expect_direction("rtl")
        expect(header.language_button).to_have_text("EN")

    def test_profile_language_wins_on_a_fresh_device(self, raw_admin_page, playwright_browser, admin_api, restore_english):
        """Saved on the profile, so a browser with empty storage signs in and comes up Arabic."""
        header = HeaderPage(raw_admin_page)
        header.goto("/dashboard")
        header.click_language_switch()
        header.expect_direction("rtl")
        raw_admin_page.wait_for_timeout(500)
        state = raw_admin_page.context.storage_state()
        # Same session, but without the locally remembered language: it must come from the profile.
        state["origins"] = [
            {**o, "localStorage": [i for i in o["localStorage"] if i["name"] != "abem_language"]}
            for o in state["origins"]
        ]
        ctx = playwright_browser.new_context(storage_state=state)
        try:
            pg = ctx.new_page()
            fresh = HeaderPage(pg)
            fresh.goto("/dashboard")
            fresh.expect_direction("rtl")
        finally:
            ctx.close()


@pytest.mark.ui
@pytest.mark.i18n
@pytest.mark.phase5
@pytest.mark.datatable
class TestArabicRtl:
    def test_arabic_buildings_table_search_names_columns_in_arabic(self, raw_admin_page, restore_english):
        header = HeaderPage(raw_admin_page)
        header.goto("/buildings")
        header.click_language_switch()
        header.expect_direction("rtl")
        BuildingsPage(raw_admin_page).wait_for_load()
        table = DataTablePage(raw_admin_page, "buildings-table")
        table.wait_ready()
        placeholder = table.search_placeholder()
        assert placeholder.startswith("ابحث بـ"), placeholder
        assert placeholder.endswith("…")
        assert "الاسم" in placeholder and "المدينة" in placeholder
        assert not re.search(r"[A-Za-z]{3,}", placeholder), "no English words left in the Arabic placeholder"

    def test_arabic_payments_page_is_rtl_with_arabic_receipt_column(
        self, raw_admin_page, reversible_payment, restore_english
    ):
        header = HeaderPage(raw_admin_page)
        header.goto("/payments")
        header.click_language_switch()
        header.expect_direction("rtl")
        # Pick the building/unit in Arabic
        group_b = raw_admin_page.locator(".MuiFormControl-root").filter(has_text="المبنى").first
        group_b.get_by_role("combobox").click()
        raw_admin_page.get_by_role("option", name=reversible_payment["building"]["name"]).click()
        group_a = raw_admin_page.locator(".MuiFormControl-root").filter(has_text=re.compile("الشقة|الوحدة")).first
        group_a.get_by_role("combobox").click()
        raw_admin_page.get_by_role("option").filter(
            has_text=re.compile(re.escape(str(reversible_payment["apartment"]["unit_number"])))
        ).first.click()
        table = PaymentsPage(raw_admin_page).table()
        table.wait_ready()
        expect(table.rows.first).to_be_visible()
        assert "رقم الإيصال" in table.header_labels()
        expect(raw_admin_page.get_by_test_id("reverse-payment").first).to_have_text("إلغاء الدفعة")
