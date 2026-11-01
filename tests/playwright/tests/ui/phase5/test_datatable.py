"""UI tests for the shared DataTable (plain MUI Table) on Buildings, Users, Expenses and Payments:
search box with a column-naming placeholder, sortable headers, TablePagination."""

import re

import pytest
from playwright.sync_api import expect

from fixtures.phase5 import API, goto
from pages.data_table_page import DataTablePage
from pages.expenses_page import ExpensesPage
from pages.payments_page import PaymentsPage
from utils.data_factory import build_building, build_expense, build_payment, unique_prefix


def _no_datagrid(page):
    assert page.locator("[role='grid'], .MuiDataGrid-root").count() == 0, "DataGrid must be gone"


@pytest.mark.ui
@pytest.mark.datatable
@pytest.mark.phase5
class TestBuildingsTable:
    @pytest.fixture
    def two_buildings(self, create_building):
        tag = unique_prefix()
        return tag, create_building(name=f"{tag} Alpha"), create_building(name=f"{tag} Zulu")

    def test_is_a_plain_table_with_search_and_pager(self, admin_page):
        goto(admin_page, "/buildings")
        table = DataTablePage(admin_page, "buildings-table")
        table.wait_ready()
        _no_datagrid(admin_page)
        expect(table.search_box).to_be_visible()
        expect(table.pager).to_be_visible()
        assert table.rows_per_page_options() == ["10", "25", "50"]

    def test_placeholder_names_the_searched_columns(self, admin_page):
        goto(admin_page, "/buildings")
        table = DataTablePage(admin_page, "buildings-table")
        table.wait_ready()
        assert table.search_placeholder() == "Search by name, address, city…"

    def test_search_filters_rows(self, admin_page, two_buildings):
        tag, alpha, zulu = two_buildings
        goto(admin_page, "/buildings")
        table = DataTablePage(admin_page, "buildings-table")
        table.wait_ready()
        table.search(f"{tag} Zulu")
        expect(table.rows).to_have_count(1)
        expect(table.rows.first).to_contain_text(zulu["name"])
        table.search(f"{tag}")
        expect(table.rows).to_have_count(2)

    @pytest.mark.xfail(
        strict=True,
        reason="App bug: Buildings table shows 'No buildings yet' for a search with no match instead of "
        "'No matching records' (BuildingsPage passes a fixed emptyMessage to DataTable)",
    )
    def test_search_without_match_shows_empty_message(self, admin_page):
        goto(admin_page, "/buildings")
        table = DataTablePage(admin_page, "buildings-table")
        table.wait_ready()
        table.search("zz-no-such-building-" + unique_prefix())
        expect(table.empty_message()).to_have_text("No matching records")

    def test_sort_by_name_toggles_direction(self, admin_page, two_buildings):
        tag, alpha, zulu = two_buildings
        goto(admin_page, "/buildings")
        table = DataTablePage(admin_page, "buildings-table")
        table.wait_ready()
        table.search(tag)
        expect(table.rows).to_have_count(2)
        # default sort is name ascending
        assert table.sort_direction("Name") == "ascending"
        expect(table.rows.first).to_contain_text("Alpha")
        table.sort_by("Name")
        expect(table.rows.first).to_contain_text("Zulu")
        assert table.sort_direction("Name") == "descending"


@pytest.mark.ui
@pytest.mark.datatable
@pytest.mark.phase5
class TestUsersTable:
    def test_placeholder_search_and_sort(self, admin_page, create_user):
        user = create_user(role="owner")
        goto(admin_page, "/users")
        table = DataTablePage(admin_page, "users-table")
        table.wait_ready()
        _no_datagrid(admin_page)
        assert table.search_placeholder() == "Search by email, name…"
        table.search(user["email"])
        expect(table.rows).to_have_count(1)
        expect(table.rows.first).to_contain_text(user["email"])
        table.clear_search()
        expect(table.rows.first).to_be_visible()
        table.sort_by("Email")
        assert table.sort_direction("Email") == "ascending"
        emails = [e.lower() for e in table.column_texts(0)]
        assert emails == sorted(emails)
        table.sort_by("Email")
        assert table.sort_direction("Email") == "descending"
        emails = [e.lower() for e in table.column_texts(0)]
        assert emails == sorted(emails, reverse=True)

    def test_name_column_is_not_sortable(self, admin_page):
        goto(admin_page, "/users")
        table = DataTablePage(admin_page, "users-table")
        table.wait_ready()
        expect(table.header("Name").locator(".MuiTableSortLabel-root")).to_have_count(0)


@pytest.mark.ui
@pytest.mark.datatable
@pytest.mark.phase5
class TestExpensesTable:
    @pytest.fixture
    def expense_building(self, seeded_building, admin_api, create_expense):
        building = seeded_building["building"]
        cats = admin_api.get(f"{API}/expenses/categories/", params={"building_id": building["id"]}).json()
        cat = (cats.get("results", cats) if isinstance(cats, dict) else cats)[0]
        tag = unique_prefix()
        # 11 rows so the second page exists (default page size 10)
        rows = [
            create_expense(building["id"], cat["id"], title=f"{tag} Expense {i:02d}", amount=str(100 + i))
            for i in range(11)
        ]
        return {"building": building, "tag": tag, "rows": rows}

    def _open(self, page, building):
        ep = ExpensesPage(page)
        ep.navigate()
        ep.select_building(building["name"])
        table = DataTablePage(page, "expenses-data-table")
        table.wait_ready()
        return table

    def test_pagination_ten_per_page(self, admin_page, expense_building):
        table = self._open(admin_page, expense_building["building"])
        _no_datagrid(admin_page)
        expect(table.rows).to_have_count(10)
        assert "1–10 of 11" in table.displayed_rows_text()
        assert table.is_next_enabled()
        table.next_page()
        expect(table.rows).to_have_count(1)
        assert "11–11 of 11" in table.displayed_rows_text()
        assert not table.is_next_enabled()
        table.previous_page()
        expect(table.rows).to_have_count(10)

    def test_rows_per_page_25_shows_everything(self, admin_page, expense_building):
        table = self._open(admin_page, expense_building["building"])
        table.set_rows_per_page(25)
        expect(table.rows).to_have_count(11)

    def test_search_by_title_and_placeholder(self, admin_page, expense_building):
        table = self._open(admin_page, expense_building["building"])
        placeholder = table.search_placeholder()
        assert placeholder.startswith("Search by ") and placeholder.endswith("…")
        assert "title" in placeholder.lower()
        table.search(f"{expense_building['tag']} Expense 07")
        expect(table.rows).to_have_count(1)
        expect(table.rows.first).to_contain_text("Expense 07")
        assert "1–1 of 1" in table.displayed_rows_text()

    def test_search_resets_to_first_page(self, admin_page, expense_building):
        table = self._open(admin_page, expense_building["building"])
        table.next_page()
        expect(table.rows).to_have_count(1)
        table.search(expense_building["tag"])
        expect(table.rows).to_have_count(10)
        assert "1–10 of 11" in table.displayed_rows_text()

    def test_sort_by_amount(self, admin_page, expense_building):
        table = self._open(admin_page, expense_building["building"])
        table.sort_by("Amount")
        direction = table.sort_direction("Amount")
        assert direction in ("ascending", "descending")
        table.sort_by("Amount")
        assert table.sort_direction("Amount") != direction


@pytest.mark.ui
@pytest.mark.datatable
@pytest.mark.phase5
class TestPaymentsTable:
    @pytest.fixture
    def two_payments(self, admin_api, billed_unit):
        apt = billed_unit["apartment"]
        tag = unique_prefix()
        made = []
        for amount, note in (("30", f"{tag} first"), ("45", f"{tag} second")):
            resp = admin_api.post(
                f"{API}/payments/",
                data=build_payment(apt["id"], amount_paid=amount, payment_method="cash", notes=note,
                                   expense_ids=[billed_unit["expense"]["id"]]),
            )
            assert resp.status == 201, resp.text()
            made.append(resp.json())
        return {**billed_unit, "tag": tag, "payments": made}

    def _open(self, page, ctx):
        pp = PaymentsPage(page)
        pp.navigate()
        pp.choose_building(ctx["building"]["name"])
        pp.choose_unit(str(ctx["apartment"]["unit_number"]))
        table = pp.table()
        table.wait_ready()
        return pp, table

    def test_table_search_sort_and_pager(self, admin_page, two_payments):
        _, table = self._open(admin_page, two_payments)
        _no_datagrid(admin_page)
        expect(table.rows).to_have_count(2)
        expect(table.pager).to_be_visible()
        placeholder = table.search_placeholder()
        assert placeholder.startswith("Search by ") and "receipt" in placeholder.lower()
        table.search(f"{two_payments['tag']} second")
        expect(table.rows).to_have_count(1)
        table.clear_search()
        expect(table.rows).to_have_count(2)
        table.sort_by("Amount")
        first = table.column_texts(2)
        table.sort_by("Amount")
        assert table.column_texts(2) == list(reversed(first))
