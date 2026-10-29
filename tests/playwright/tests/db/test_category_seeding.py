"""DB tests for category seeding."""
import pytest
from utils.data_factory import build_building
from utils.db_client import query_all


@pytest.mark.db
class TestCategorySeeding:
    def test_building_has_15_default_categories(self, admin_api, db_conn):
        building = admin_api.post("/api/v1/buildings/", data=build_building()).json()
        try:
            rows = query_all(
                db_conn,
                "SELECT * FROM expenses_expensecategory WHERE building_id::text = %s",
                (building["id"],),
            )
            assert len(rows) == 15, f"Expected 15 categories, got {len(rows)}"
        finally:
            admin_api.delete(f"/api/v1/buildings/{building['id']}/")

    def test_each_category_has_required_fields(self, admin_api, db_conn):
        building = admin_api.post("/api/v1/buildings/", data=build_building()).json()
        try:
            rows = query_all(
                db_conn,
                "SELECT name, icon, color FROM expenses_expensecategory WHERE building_id::text = %s",
                (building["id"],),
            )
            for row in rows:
                assert row["name"] is not None and row["name"] != ""
                assert row["icon"] is not None
                assert row["color"] is not None
        finally:
            admin_api.delete(f"/api/v1/buildings/{building['id']}/")
