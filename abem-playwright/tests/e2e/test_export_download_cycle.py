"""E2E Journey 7: Export and receipt full cycle."""
from decimal import Decimal
import pytest
from utils.data_factory import build_building, build_expense, build_payment
from utils.csv_helpers import parse_csv_bytes
from utils.assertions import assert_valid_pdf
from config.settings import settings


@pytest.mark.e2e
@pytest.mark.exports
class TestExportDownloadCycle:

    def test_export_lifecycle(self, admin_api):
        building = admin_api.post(
            "/api/v1/buildings/", data=build_building(num_apartments=2, num_stores=0)
        ).json()
        bid = building["id"]
        try:
            apts = admin_api.get("/api/v1/apartments/", params={"building_id": bid}).json()
            apt_list = apts.get("results", apts) if isinstance(apts, dict) else apts
            cats = admin_api.get("/api/v1/expenses/categories/", params={"building_id": bid}).json()
            cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats

            # Create expense
            admin_api.post("/api/v1/expenses/", data=build_expense(
                bid, cat_list[0]["id"], amount="200"
            ))

            # Record payments for both apartments
            payments = []
            for apt in apt_list[:2]:
                p = admin_api.post("/api/v1/payments/", data=build_payment(
                    apt["id"], amount_paid="50"
                )).json()
                payments.append(p)

            # Download CSV export
            csv_resp = admin_api.get("/api/v1/exports/payments/", params={"format": "csv"})
            assert csv_resp.status == 200
            rows = parse_csv_bytes(csv_resp.body())
            assert len(rows) >= 2

            # Download XLSX export
            xlsx_resp = admin_api.get("/api/v1/exports/expenses/", params={
                "file_format": "xlsx", "building_id": bid,
            })
            assert xlsx_resp.status == 200

            # Download receipt PDF
            receipt_resp = admin_api.get(f"/api/v1/payments/{payments[0]['id']}/receipt/")
            assert receipt_resp.status == 200
            assert_valid_pdf(receipt_resp.body())

        finally:
            admin_api.delete(f"/api/v1/buildings/{bid}/")
