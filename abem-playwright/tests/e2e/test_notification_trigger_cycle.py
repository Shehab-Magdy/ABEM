"""E2E Journey 4: Notification trigger cycle."""
import pytest
from pages.notifications_page import NotificationsPage
from utils.data_factory import build_building, build_expense, build_payment
from utils.db_client import get_notifications_for_user
from config.settings import settings


@pytest.mark.e2e
class TestNotificationTriggerCycle:

    def test_notification_lifecycle(self, admin_api, owner_api, owner_page, db_conn):
        # Create building + expense
        building = admin_api.post(
            "/api/v1/buildings/", data=build_building(num_apartments=1, num_stores=0)
        ).json()
        bid = building["id"]
        try:
            apts = admin_api.get("/api/v1/apartments/", params={"building_id": bid}).json()
            apt_list = apts.get("results", apts) if isinstance(apts, dict) else apts
            cats = admin_api.get("/api/v1/expenses/categories/", params={"building_id": bid}).json()
            cat_list = cats.get("results", cats) if isinstance(cats, dict) else cats

            admin_api.post("/api/v1/expenses/", data=build_expense(
                bid, cat_list[0]["id"], amount="100"
            ))

            # Record payment
            admin_api.post("/api/v1/payments/", data=build_payment(
                apt_list[0]["id"], amount_paid="50"
            ))

            # Owner checks notifications via UI
            np = NotificationsPage(owner_page)
            np.navigate()
            np.wait_for_load()

        finally:
            admin_api.delete(f"/api/v1/buildings/{bid}/")
