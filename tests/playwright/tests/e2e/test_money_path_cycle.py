"""E2E Journey: expense -> payment -> receipt -> reversal -> balance restored (SRS 11.6)."""

from decimal import Decimal

import pytest
from playwright.sync_api import expect

from fixtures.phase5 import API, apartment_balance, money, unwrap
from pages.payments_page import PaymentsPage
from utils.assertions import assert_valid_pdf
from utils.data_factory import build_building, build_expense, build_payment


@pytest.mark.e2e
@pytest.mark.money_path
@pytest.mark.phase5
@pytest.mark.financial
class TestMoneyPathCycle:
    def test_expense_payment_receipt_reversal_restores_balance(self, admin_api, admin_page):
        building = admin_api.post(f"{API}/buildings/", data=build_building(num_apartments=1, num_stores=0)).json()
        bid = building["id"]
        try:
            apt = unwrap(admin_api.get(f"{API}/apartments/", params={"building_id": bid}).json())[0]
            cat = unwrap(admin_api.get(f"{API}/expenses/categories/", params={"building_id": bid}).json())[0]

            # 1. an expense bills the unit
            expense = admin_api.post(f"{API}/expenses/", data=build_expense(bid, cat["id"], amount="100")).json()
            billed = apartment_balance(admin_api, apt["id"])
            assert billed > 0, "the unit owes after the expense"

            # 2. a payment reduces the balance and gets a receipt number
            payment = admin_api.post(
                f"{API}/payments/",
                data=build_payment(apt["id"], amount_paid="40", payment_method="cash", expense_ids=[expense["id"]]),
            ).json()
            assert payment["receipt_no"]
            assert apartment_balance(admin_api, apt["id"]) == billed - Decimal("40")

            # 3. the receipt is a PDF
            receipt = admin_api.get(f"{API}/payments/{payment['id']}/receipt/")
            assert receipt.status == 200
            assert_valid_pdf(receipt.body())

            # 4. the expense is locked while it has payments
            assert admin_api.delete(f"{API}/expenses/{expense['id']}/").status == 400

            # 5. reverse it from the Payments page
            pp = PaymentsPage(admin_page)
            pp.navigate()
            pp.choose_building(building["name"])
            pp.choose_unit(str(apt["unit_number"]))
            table = pp.table()
            table.wait_ready()
            expect(table.rows).to_have_count(1)
            assert pp.receipt_numbers() == [f"#{payment['receipt_no']}"]
            pp.click_reverse(0)
            pp.fill_reverse_reason("E2E money path")
            pp.confirm_reverse()
            expect(pp.voided_chips()).to_have_count(1)
            expect(pp.reversal_chips()).to_have_count(1)

            # 6. the balance is back to what it was before the payment, the history is kept
            assert apartment_balance(admin_api, apt["id"]) == billed
            history = unwrap(admin_api.get(f"{API}/payments/", params={"apartment_id": apt["id"]}).json())
            assert sorted(money(p["amount_paid"]) for p in history) == [Decimal("-40"), Decimal("40")]
            treasury = admin_api.get(f"{API}/buildings/{bid}/treasury/").json()
            assert money(treasury["total_reversals"]) == Decimal("40")

            # 7. a second reversal of the same payment is refused
            again = admin_api.post(f"{API}/payments/{payment['id']}/reverse/", data={"reason": "twice"})
            assert again.status == 409

            # 8. with no money left on it the expense can be deleted again
            assert admin_api.delete(f"{API}/expenses/{expense['id']}/").status in (200, 204)
        finally:
            admin_api.delete(f"{API}/buildings/{bid}/")

    def test_other_admin_cannot_touch_the_money_path(self, admin_api, second_admin_api, reversible_payment):
        pid = reversible_payment["payment"]["id"]
        assert second_admin_api.post(f"{API}/payments/{pid}/reverse/", data={"reason": "x"}).status in (403, 404)
        assert second_admin_api.get(f"{API}/payments/{pid}/receipt/").status in (403, 404)
        assert second_admin_api.get(f"{API}/exports/building/{reversible_payment['building']['id']}/").status == 404
