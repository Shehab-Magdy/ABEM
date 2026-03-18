"""Performance timing tests using Playwright metrics."""
import pytest
from config.settings import settings


@pytest.mark.ui
@pytest.mark.performance
class TestPageLoadTiming:
    def test_login_page_load_under_2s(self, page):
        page.goto(f"{settings.BASE_URL}/login")
        timing = page.evaluate("JSON.parse(JSON.stringify(window.performance.timing))")
        dom_loaded = timing["domContentLoadedEventEnd"] - timing["navigationStart"]
        assert dom_loaded < 2000, f"Login DOM loaded in {dom_loaded}ms (threshold: 2000ms)"

    def test_dashboard_load_under_3s(self, admin_page):
        start = admin_page.evaluate("performance.now()")
        admin_page.goto(f"{settings.BASE_URL}/dashboard")
        admin_page.wait_for_load_state("networkidle")
        end = admin_page.evaluate("performance.now()")
        elapsed = end - start
        assert elapsed < 3000, f"Dashboard loaded in {elapsed:.0f}ms (threshold: 3000ms)"

    def test_buildings_load_under_1500ms(self, admin_page):
        start = admin_page.evaluate("performance.now()")
        admin_page.goto(f"{settings.BASE_URL}/buildings")
        admin_page.wait_for_load_state("networkidle")
        end = admin_page.evaluate("performance.now()")
        elapsed = end - start
        assert elapsed < 1500, f"Buildings loaded in {elapsed:.0f}ms (threshold: 1500ms)"

    def test_expenses_load_under_1500ms(self, admin_page):
        start = admin_page.evaluate("performance.now()")
        admin_page.goto(f"{settings.BASE_URL}/expenses")
        admin_page.wait_for_load_state("networkidle")
        end = admin_page.evaluate("performance.now()")
        elapsed = end - start
        assert elapsed < 1500, f"Expenses loaded in {elapsed:.0f}ms (threshold: 1500ms)"
