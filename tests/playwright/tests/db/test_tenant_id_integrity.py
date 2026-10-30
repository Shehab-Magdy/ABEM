"""DB tests for tenant ID integrity."""
import re
import pytest
from utils.db_client import query_all


@pytest.mark.db
class TestTenantIdIntegrity:
    def test_building_id_is_valid_uuid(self, db_conn):
        rows = query_all(db_conn, "SELECT id::text FROM buildings_building LIMIT 10")
        uuid_pattern = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
        for row in rows:
            assert uuid_pattern.match(row["id"]), f"Invalid UUID: {row['id']}"

    def test_apartment_building_id_not_null(self, db_conn):
        rows = query_all(db_conn, "SELECT building_id FROM apartments_apartment WHERE building_id IS NULL LIMIT 1")
        assert len(rows) == 0, "Found apartments with NULL building_id"

    def test_expense_building_id_not_null(self, db_conn):
        rows = query_all(db_conn, "SELECT building_id FROM expenses_expense WHERE building_id IS NULL LIMIT 1")
        assert len(rows) == 0, "Found expenses with NULL building_id"
