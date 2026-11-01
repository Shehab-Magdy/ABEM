"""API tests for POST /payments/{id}/reverse/ (SRS 11.6): linked negative entry, balance restored, one reversal."""

import pytest

from fixtures.phase5 import API, errors, apartment_balance, money, unwrap


def _reverse(api, payment_id, reason="Entered in error"):
    return api.post(f"{API}/payments/{payment_id}/reverse/", data={"reason": reason})


@pytest.mark.api
@pytest.mark.payments
@pytest.mark.phase5
@pytest.mark.financial
class TestPaymentReversal:
    def test_reversal_is_a_linked_negative_entry(self, admin_api, reversible_payment):
        original = reversible_payment["payment"]
        resp = _reverse(admin_api, original["id"], "Wrong unit")
        assert resp.status == 201, resp.text()
        rev = resp.json()
        assert money(rev["amount_paid"]) == -money(original["amount_paid"])
        assert rev["reversal_of"] == original["id"]
        assert rev["reversal_reason"] == "Wrong unit"
        assert rev["is_reversal"] is True
        assert rev["is_voided"] is False

    def test_original_becomes_voided_and_is_kept(self, admin_api, reversible_payment):
        original = reversible_payment["payment"]
        assert original["is_voided"] is False
        assert _reverse(admin_api, original["id"]).status == 201
        resp = admin_api.get(f"{API}/payments/{original['id']}/")
        assert resp.status == 200
        assert resp.json()["is_voided"] is True
        assert money(resp.json()["amount_paid"]) == money(original["amount_paid"])

    def test_reversal_restores_the_unit_balance(self, admin_api, reversible_payment):
        apt_id = reversible_payment["apartment"]["id"]
        paid = money(reversible_payment["payment"]["amount_paid"])
        assert reversible_payment["balance_after"] == reversible_payment["balance_before"] - paid
        resp = _reverse(admin_api, reversible_payment["payment"]["id"])
        assert resp.status == 201
        assert apartment_balance(admin_api, apt_id) == reversible_payment["balance_before"]
        assert money(resp.json()["balance_after"]) == reversible_payment["balance_before"]

    def test_double_reversal_conflicts_and_balance_is_not_restored_twice(self, admin_api, reversible_payment):
        apt_id = reversible_payment["apartment"]["id"]
        pid = reversible_payment["payment"]["id"]
        assert _reverse(admin_api, pid).status == 201
        again = _reverse(admin_api, pid, "Again")
        assert again.status == 409, again.text()
        assert apartment_balance(admin_api, apt_id) == reversible_payment["balance_before"]

    def test_a_reversal_cannot_itself_be_reversed(self, admin_api, reversible_payment):
        rev = _reverse(admin_api, reversible_payment["payment"]["id"]).json()
        assert _reverse(admin_api, rev["id"]).status == 409

    @pytest.mark.negative
    @pytest.mark.parametrize("body", [{}, {"reason": ""}, {"reason": "   "}])
    def test_reason_is_required(self, admin_api, reversible_payment, body):
        pid = reversible_payment["payment"]["id"]
        resp = admin_api.post(f"{API}/payments/{pid}/reverse/", data=body)
        assert resp.status == 400
        assert "reason" in errors(resp)
        assert admin_api.get(f"{API}/payments/{pid}/").json()["is_voided"] is False

    def test_allocations_are_negated(self, admin_api, reversible_payment):
        rev = _reverse(admin_api, reversible_payment["payment"]["id"]).json()
        original = admin_api.get(f"{API}/payments/{reversible_payment['payment']['id']}/").json()
        sums = lambda p: sum(money(a["allocated_amount"]) for a in p["allocation_details"])  # noqa: E731
        assert sums(rev) == -sums(original)

    def test_reversal_is_listed_and_audited(self, admin_api, reversible_payment):
        pid = reversible_payment["payment"]["id"]
        rev = _reverse(admin_api, pid, "Audit me").json()
        listing = unwrap(
            admin_api.get(
                f"{API}/payments/", params={"apartment_id": reversible_payment["apartment"]["id"], "page_size": 50}
            ).json()
        )
        assert rev["id"] in {p["id"] for p in listing}
        audit = unwrap(admin_api.get(f"{API}/audit/", params={"entity": "payment", "page_size": 100}).json())
        assert any(a["entity_id"] == pid and a["action"] == "payment.reversed" for a in audit)

    def test_payment_has_receipt_number(self, reversible_payment):
        assert reversible_payment["payment"]["receipt_no"]

    def test_receipt_numbers_are_unique(self, admin_api, reversible_payment):
        apt_id = reversible_payment["apartment"]["id"]
        second = admin_api.post(
            f"{API}/payments/", data={"apartment_id": apt_id, "amount_paid": "5", "payment_method": "cash",
                                      "payment_date": reversible_payment["payment"]["payment_date"]}
        )
        assert second.status == 201, second.text()
        assert second.json()["receipt_no"] != reversible_payment["payment"]["receipt_no"]

    def test_treasury_reports_payments_and_reversals(self, admin_api, reversible_payment):
        bid = reversible_payment["building"]["id"]
        before = admin_api.get(f"{API}/buildings/{bid}/treasury/").json()
        for key in ("total_payments", "total_reversals", "total_sales"):
            assert key in before
        assert money(before["total_payments"]) >= money(reversible_payment["payment"]["amount_paid"])
        assert _reverse(admin_api, reversible_payment["payment"]["id"]).status == 201
        after = admin_api.get(f"{API}/buildings/{bid}/treasury/").json()
        assert money(after["total_reversals"]) == money(reversible_payment["payment"]["amount_paid"])
        assert money(after["balance"]) == money(before["balance"]) - money(reversible_payment["payment"]["amount_paid"])


@pytest.mark.api
@pytest.mark.payments
@pytest.mark.phase5
@pytest.mark.rbac
@pytest.mark.tenant_isolation
class TestPaymentReversalAccess:
    def test_unauthenticated_gets_401(self, unauthenticated_api, reversible_payment):
        resp = _reverse(unauthenticated_api, reversible_payment["payment"]["id"])
        assert resp.status == 401

    def test_owner_cannot_reverse(self, member_owner, admin_api, reversible_payment):
        resp = _reverse(member_owner["api"], reversible_payment["payment"]["id"])
        assert resp.status == 403
        assert admin_api.get(f"{API}/payments/{reversible_payment['payment']['id']}/").json()["is_voided"] is False

    def test_other_admin_cannot_reverse_another_buildings_payment(
        self, second_admin_api, admin_api, reversible_payment
    ):
        pid = reversible_payment["payment"]["id"]
        resp = _reverse(second_admin_api, pid)
        assert resp.status in (403, 404), resp.text()
        assert admin_api.get(f"{API}/payments/{pid}/").json()["is_voided"] is False
        assert apartment_balance(admin_api, reversible_payment["apartment"]["id"]) == reversible_payment["balance_after"]

    def test_other_admin_does_not_see_the_payment(self, second_admin_api, reversible_payment):
        pid = reversible_payment["payment"]["id"]
        assert second_admin_api.get(f"{API}/payments/{pid}/").status == 404
