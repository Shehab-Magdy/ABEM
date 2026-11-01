"""Playwright browser configuration for ABEM test framework."""

import os

from dotenv import load_dotenv

load_dotenv()

# ── Browser settings ──────────────────────────────────────────
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
SLOW_MO = int(os.getenv("SLOW_MO", "0"))
BROWSER_TYPE = os.getenv("BROWSER_TYPE", "chromium")

# ── Viewport ──────────────────────────────────────────────────
VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 720

# ── Locale & timezone ─────────────────────────────────────────
LOCALE = "en-US"
TIMEZONE_ID = "Africa/Cairo"

# ── Timeouts (ms) ─────────────────────────────────────────────
# Playwright's own timeouts must be shorter than the 30s per-test pytest timeout, otherwise a missing element makes
# pytest-timeout kill the whole session instead of failing one test.
DEFAULT_TIMEOUT = int(os.getenv("PW_DEFAULT_TIMEOUT", "12000"))
NAVIGATION_TIMEOUT = int(os.getenv("PW_NAVIGATION_TIMEOUT", "20000"))
EXPECT_TIMEOUT = 10_000

# ── Artifacts ─────────────────────────────────────────────────
SCREENSHOT_ON_FAILURE = True
VIDEO_ON_FAILURE = os.getenv("VIDEO_ON_FAILURE", "false").lower() == "true"
TRACE_ON_FAILURE = os.getenv("TRACE_ON_FAILURE", "false").lower() == "true"

# ── Storage state paths ──────────────────────────────────────
ADMIN_STORAGE_STATE = "tmp/admin_storage_state.json"
OWNER_STORAGE_STATE = "tmp/owner_storage_state.json"
