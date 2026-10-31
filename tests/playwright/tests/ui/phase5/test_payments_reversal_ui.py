"""UI tests for reversing a payment from the Payments page: dialog, required reason, Voided / Reversal chips,
receipt numbers, and the owner view (no reverse button)."""

import re

import pytest
from playwright.sync_api import expect

from config.settings import settings
from fixtures.phase5 import API, apartment_balance
from pages.payments_page import PaymentsPage


def _open(page, ctx):
    pp = PaymentsPage(page)
    pp.navigate()
    pp.choose_building(ctx["building"]["name"])
    pp.choose_unit(str(ctx["apartment"]["unit_number"]))
    pp.table().wait_ready()
    return pp


@pytest.mark.ui
@pytest.mark.payments
@pytest.mark.phase5
@pytest.mark.financial
class TestReversePaymentUI:
    def test_receipt_number_is_shown(self, admin_page, reversible_payment):
        pp = _open(admin_page, reversible_payment)
        expect(pp.table().rows).to_have_count(1)
        assert pp.receipt_numbers() == [f"#{reversible_payment['payment']['receipt_no']}"]

    def test_reverse_button_opens_dialog_with_required_reason(self, admin_page, reversible_payment):
        pp = _open(admin_page, reversible_payment)
        pp.click_reverse(0)
        dialog = pp.reverse_dialog()
        expect(dialog).to_be_visible()
        expect(dialog.get_by_text("Reverse this payment")).to_be_visible()
        expect(dialog.get_by_role("button", name="Reverse", exact=True)).to_be_disabled()
        pp.fill_reverse_reason("   ")
        expect(dialog.get_by_role("button", name="Reverse", exact=True)).to_be_disabled()
        pp.fill_reverse_reason("Paid twice")
        expect(dialog.get_by_role("button", name="Reverse", exact=True)).to_be_enabled()

    def test_cancel_leaves_the_payment_untouched(self, admin_page, admin_api, reversible_payment):
        pp = _open(admin_page, reversible_payment)
        pp.click_reverse(0)
        pp.fill_reverse_reason("Never mind")
        pp.reverse_dialog().get_by_role("button", name="Cancel").click()
        expect(pp.reverse_dialog()).to_have_count(0)
        expect(pp.voided_chips()).to_have_count(0)
        assert apartment_balance(admin_api, reversible_payment["apartment"]["id"]) == reversible_payment["balance_after"]

    def test_reversing_marks_voided_adds_reversal_row_and_restores_balance(
        self, admin_page, admin_api, reversible_payment
    ):
        pp = _open(admin_page, reversible_payment)
        pp.click_reverse(0)
        pp.fill_reverse_reason("Recorded on the wrong unit")
        pp.confirm_reverse()
        expect(admin_page.get_by_text("Payment reversed.")).to_be_visible()
        table = pp.table()
        expect(table.rows).to_have_count(2)
        expect(pp.voided_chips()).to_have_count(1)
        expect(pp.reversal_chips()).to_have_count(1)
        # neither the voided original nor the reversal row can be reversed again
        expect(pp.reverse_buttons()).to_have_count(0)
        assert apartment_balance(admin_api, reversible_payment["apartment"]["id"]) == reversible_payment["balance_before"]

    def test_reversal_reason_is_visible_as_chip_title(self, admin_page, reversible_payment):
        pp = _open(admin_page, reversible_payment)
        pp.click_reverse(0)
        pp.fill_reverse_reason("Because tests")
        pp.confirm_reverse()
        expect(pp.reversal_chips()).to_have_attribute("title", "Because tests")

    def test_print_receipt_button_still_present_for_voided_payment(self, admin_page, reversible_payment):
        pp = _open(admin_page, reversible_payment)
        pp.click_reverse(0)
        pp.fill_reverse_reason("Void")
        pp.confirm_reverse()
        expect(pp.voided_chips()).to_have_count(1)
        expect(admin_page.get_by_test_id("print-receipt")).to_have_count(2)

    @pytest.mark.rbac
    def test_owner_sees_no_reverse_button(self, member_owner, member_owner_page, admin_api, reversible_payment):
        """The resident of the unit sees the payment but cannot reverse it."""
        # The owner belongs to a fresh unit-less state; make them the unit's owner so the payment is theirs
        assert admin_api.patch(
            f"{API}/apartments/{reversible_payment['apartment']['id']}/",
            data={"owner_id": member_owner["user"]["id"]},
        ).status == 200
        member_owner_page.goto(f"{settings.BASE_URL}/payments")
        member_owner_page.get_by_test_id("payments-data-table").wait_for(state="visible")
        expect(member_owner_page.get_by_test_id("reverse-payment")).to_have_count(0)
