"""DB tests for password hashing."""
import pytest
from utils.db_client import query_one


@pytest.mark.db
class TestPasswordHashing:
    def test_password_not_stored_plaintext(self, admin_api, db_conn, create_user):
        user = create_user(role="owner")
        row = query_one(db_conn, "SELECT password FROM authentication_user WHERE id::text = %s", (user["id"],))
        assert row is not None
        assert row["password"] != user["_password"]

    def test_password_hash_has_known_prefix(self, db_conn, create_user):
        user = create_user(role="owner")
        row = query_one(db_conn, "SELECT password FROM authentication_user WHERE id::text = %s", (user["id"],))
        assert row["password"].startswith("pbkdf2_sha256$") or row["password"].startswith("$2b$")

    def test_password_field_never_in_api_response(self, admin_api, create_user):
        user = create_user(role="owner")
        resp = admin_api.get(f"/api/v1/users/{user['id']}/")
        body = resp.json()
        assert "password" not in body
        assert "password_hash" not in body
