"""UI tests for payments page."""
import pytest
from pages.payments_page import PaymentsPage
from config.settings import settings


@pytest.mark.ui
@pytest.mark.payments
class TestPaymentsUI:
    def test_payments_page_renders(self, admin_page):
        pp = PaymentsPage(admin_page)
        pp.navigate()
        pp.wait_for_load()

    def test_owner_no_record_button(self, owner_page):
        pp = PaymentsPage(owner_page)
        pp.navigate()
        pp.wait_for_load()
        assert not pp.is_record_button_visible()
