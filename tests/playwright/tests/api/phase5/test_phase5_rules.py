"""API tests for the Phase 5 data rules (SRS 11.6): immutable building, paid-expense lock, asset sales,
owner membership, one pending plan payment, account deletion with a balance."""

from datetime import date

import pytest

from fixtures.phase5 import API, money, unwrap
from utils.data_factory import build_building, build_payment


def _assets_url(path=""):
    return f"{API}/payments/assets/{path}"


@pytest.fixture
def other_building(create_building):
    return create_building(num_apartments=1, num_stores=0)


@pytest.fixture
def asset(admin_api, billed_unit):
    resp = admin_api.post(
        _assets_url(),
        data={
            "building_id": billed_unit["building"]["id"],
            "name": "Phase5 generator",
            "asset_type": "equipment",
            "acquisition_date": date.today().isoformat(),
            "acquisition_value": "1000.00",
        },
    )
    assert resp.status == 201, resp.text()
    return resp.json()


@pytest.mark.api
@pytest.mark.phase5
@pytest.mark.negative
class TestBuildingIsImmutable:
    def test_unit_cannot_move_to_another_building(self, admin_api, billed_unit, other_building):
        apt_id = billed_unit["apartment"]["id"]
        resp = admin_api.patch(f"{API}/apartments/{apt_id}/", data={"building_id": other_building["id"]})
        assert resp.status == 400
        assert "building_id" in resp.json()
        assert admin_api.get(f"{API}/apartments/{apt_id}/").json()["building_id"] == billed_unit["building"]["id"]

    def test_expense_cannot_move_to_another_building(self, admin_api, billed_unit, other_building):
        exp_id = billed_unit["expense"]["id"]
        resp = admin_api.patch(f"{API}/expenses/{exp_id}/", data={"building_id": other_building["id"]})
        assert resp.status == 400
        assert "building_id" in resp.json()

    def test_asset_cannot_move_to_another_building(self, admin_api, asset, other_building):
        resp = admin_api.patch(_assets_url(f"{asset['id']}/"), data={"building_id": other_building["id"]})
        assert resp.status == 400
        assert "building_id" in resp.json()

    def test_patching_the_same_building_is_allowed(self, admin_api, billed_unit):
        apt_id = billed_unit["apartment"]["id"]
        resp = admin_api.patch(
            f"{API}/apartments/{apt_id}/", data={"building_id": billed_unit["building"]["id"], "floor": 1}
        )
        assert resp.status == 200, resp.text()


@pytest.mark.api
@pytest.mark.phase5
@pytest.mark.financial
class TestPaidExpenseLock:
    def test_amount_cannot_change_once_paid(self, admin_api, reversible_payment):
        exp = reversible_payment["expense"]
        resp = admin_api.patch(f"{API}/expenses/{exp['id']}/", data={"amount": "999"})
        assert resp.status == 400, resp.text()
        assert money(admin_api.get(f"{API}/expenses/{exp['id']}/").json()["amount"]) == money(exp["amount"])

    def test_split_cannot_change_once_paid(self, admin_api, reversible_payment):
        exp = reversible_payment["expense"]
        other = "equal_apartments" if exp["split_type"] != "equal_apartments" else "equal_all"
        resp = admin_api.patch(f"{API}/expenses/{exp['id']}/", data={"split_type": other})
        assert resp.status == 400, resp.text()

    def test_paid_expense_cannot_be_deleted(self, admin_api, reversible_payment):
        exp_id = reversible_payment["expense"]["id"]
        resp = admin_api.delete(f"{API}/expenses/{exp_id}/")
        assert resp.status == 400, resp.text()
        assert admin_api.get(f"{API}/expenses/{exp_id}/").status == 200

    def test_descriptive_fields_stay_editable(self, admin_api, reversible_payment):
        exp_id = reversible_payment["expense"]["id"]
        resp = admin_api.patch(f"{API}/expenses/{exp_id}/", data={"description": "Edited after payment"})
        assert resp.status == 200, resp.text()
        assert resp.json()["description"] == "Edited after payment"

    def test_reversing_the_payment_unlocks_the_expense(self, admin_api, reversible_payment):
        exp_id = reversible_payment["expense"]["id"]
        assert admin_api.post(
            f"{API}/payments/{reversible_payment['payment']['id']}/reverse/", data={"reason": "Unlock"}
        ).status == 201
        resp = admin_api.patch(f"{API}/expenses/{exp_id}/", data={"amount": "150"})
        assert resp.status == 200, resp.text()

    def test_unpaid_expense_can_still_be_deleted(self, admin_api, billed_unit, create_expense):
        extra = create_expense(billed_unit["building"]["id"], billed_unit["category"]["id"], amount="50")
        assert admin_api.delete(f"{API}/expenses/{extra['id']}/").status in (200, 204)


@pytest.mark.api
@pytest.mark.phase5
@pytest.mark.negative
class TestAssetSaleValidation:
    def _sell(self, api, asset, **overrides):
        body = {"sale_date": date.today().isoformat(), "sale_price": "500.00", "buyer_name": "Buyer"}
        body.update(overrides)
        return api.post(_assets_url(f"{asset['id']}/sell/"), data=body)

    @pytest.mark.parametrize("price", ["0", "-5"])
    def test_price_must_be_positive(self, admin_api, asset, price):
        resp = self._sell(admin_api, asset, sale_price=price)
        assert resp.status == 400
        assert "sale_price" in resp.json()

    @pytest.mark.parametrize("bad_date", ["2026-13-45", "not-a-date", ""])
    def test_date_must_be_valid(self, admin_api, asset, bad_date):
        resp = self._sell(admin_api, asset, sale_date=bad_date)
        assert resp.status == 400
        assert "sale_date" in resp.json()

    def test_failed_sale_leaves_the_asset_unsold(self, admin_api, asset):
        self._sell(admin_api, asset, sale_price="0")
        fetched = admin_api.get(_assets_url(f"{asset['id']}/")).json()
        assert fetched["is_sold"] is False

    def test_valid_sale_marks_asset_sold_and_cannot_repeat(self, admin_api, asset):
        assert self._sell(admin_api, asset).status == 201
        assert admin_api.get(_assets_url(f"{asset['id']}/")).json()["is_sold"] is True
        assert self._sell(admin_api, asset).status == 400

    def test_sale_shows_in_treasury_total_sales(self, admin_api, asset, billed_unit):
        assert self._sell(admin_api, asset, sale_price="750.00").status == 201
        treasury = admin_api.get(f"{API}/buildings/{billed_unit['building']['id']}/treasury/").json()
        assert money(treasury["total_sales"]) == money("750.00")

    def test_other_admin_cannot_sell_the_asset(self, second_admin_api, asset):
        resp = self._sell(second_admin_api, asset)
        assert resp.status in (403, 404)


@pytest.mark.api
@pytest.mark.phase5
@pytest.mark.rbac
class TestOwnerAssignment:
    def test_owner_must_already_be_in_the_building(self, admin_api, billed_unit, create_user):
        outsider = create_user(role="owner")
        apt_id = billed_unit["apartment"]["id"]
        resp = admin_api.patch(f"{API}/apartments/{apt_id}/", data={"owner_id": outsider["id"]})
        assert resp.status == 400
        assert "owner_id" in resp.json()

    def test_a_building_member_can_be_assigned(self, admin_api, member_owner):
        apt_id = member_owner["apartment"]["id"]
        resp = admin_api.patch(f"{API}/apartments/{apt_id}/", data={"owner_id": member_owner["user"]["id"]})
        assert resp.status == 200, resp.text()
        assert resp.json()["owner_id"] == member_owner["user"]["id"]


@pytest.mark.api
@pytest.mark.phase5
class TestOnePendingPlanPayment:
    def test_second_pending_plan_payment_is_rejected(self, admin_api, create_building):
        building = create_building(num_apartments=1, num_stores=0)
        tiers = unwrap(admin_api.get(f"{API}/plans/tiers/").json())
        paid = next((t for t in tiers if money(t["price_monthly"]) > 0), None)
        if paid is None:
            pytest.skip("No paid plan tier configured")
        body = {"building_id": building["id"], "plan_code": paid["code"], "period": "monthly", "reference": "REF-1"}
        first = admin_api.post(f"{API}/plans/payments/", data=body)
        assert first.status == 201, first.text()
        second = admin_api.post(f"{API}/plans/payments/", data={**body, "reference": "REF-2"})
        assert second.status == 400, second.text()

    def test_other_admin_cannot_pay_for_the_building(self, second_admin_api, create_building, admin_api):
        building = create_building(num_apartments=1, num_stores=0)
        tiers = unwrap(admin_api.get(f"{API}/plans/tiers/").json())
        paid = next((t for t in tiers if money(t["price_monthly"]) > 0), None)
        if paid is None:
            pytest.skip("No paid plan tier configured")
        resp = second_admin_api.post(
            f"{API}/plans/payments/",
            data={"building_id": building["id"], "plan_code": paid["code"], "period": "monthly", "reference": "X"},
        )
        assert resp.status in (400, 403, 404)


@pytest.mark.api
@pytest.mark.phase5
class TestAccountDeletionWithBalance:
    def test_deletion_conflicts_while_a_balance_is_owed_until_confirmed(self, admin_api, member_owner):
        apt_id = member_owner["apartment"]["id"]
        assert admin_api.patch(f"{API}/apartments/{apt_id}/", data={"owner_id": member_owner["user"]["id"]}).status == 200
        # a bill after the assignment guarantees the owner owes something
        admin_api.post(
            f"{API}/expenses/",
            data={
                "building_id": member_owner["building"]["id"],
                "category_id": member_owner["expense"]["category_id"],
                "title": "Phase5 owed", "amount": "100", "expense_date": date.today().isoformat(),
                "split_type": "equal_all", "is_recurring": False,
            },
        )
        resp = member_owner["api"].post(f"{API}/auth/delete-account/", data={"password": member_owner["password"]})
        assert resp.status == 409, resp.text()
        body = resp.json()
        assert money(body["balance"]) > 0
        assert body.get("requires_confirmation") is True
        confirmed = member_owner["api"].post(
            f"{API}/auth/delete-account/", data={"password": member_owner["password"], "confirm_balance": True}
        )
        assert confirmed.status in (200, 204), confirmed.text()
