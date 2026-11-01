"""E2E fixtures (kept out of the root conftest): Phase 5 helpers and per-test fresh logins."""
from fixtures.fresh_sessions import admin_page, owner_page  # noqa: F401
from fixtures.phase5 import *  # noqa: F401, F403
