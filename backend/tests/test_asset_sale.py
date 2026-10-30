"""R-23: selling an asset validates its input and cannot happen twice."""

from decimal import Decimal

import pytest
from apps.buildings.models import Building
from apps.payments.models import AssetSale, BuildingAsset

pytestmark = pytest.mark.django_db


@pytest.fixture
def asset(admin_user):
    building = Building.objects.create(name="Tower", address="1 Nile St", admin=admin_user)
    return BuildingAsset.objects.create(building=building, name="Generator", created_by=admin_user)


def _sell(client, asset, **body):
    return client.post(f"/api/v1/payments/assets/{asset.pk}/sell/", body, format="json")


@pytest.mark.parametrize("price", ["0", "0.00", "-5", "abc", "", "1e400", "NaN", "99999999999999"])
def test_bad_price_is_400_and_nothing_saved(admin_client, asset, price):
    resp = _sell(admin_client, asset, sale_date="2026-10-01", sale_price=price)
    assert resp.status_code == 400
    asset.refresh_from_db()
    assert not asset.is_sold and not AssetSale.objects.exists()


@pytest.mark.parametrize("sale_date", ["not-a-date", "2026-13-45", "01/10/2026", ""])
def test_bad_date_is_400(admin_client, asset, sale_date):
    resp = _sell(admin_client, asset, sale_date=sale_date, sale_price="100.00")
    assert resp.status_code == 400
    assert not AssetSale.objects.exists()


def test_valid_sale_is_recorded_once(admin_client, asset):
    resp = _sell(admin_client, asset, sale_date="2026-10-01", sale_price="250.50", buyer_name="Ali")
    assert resp.status_code == 201
    assert AssetSale.objects.get().sale_price == Decimal("250.50")
    asset.refresh_from_db()
    assert asset.is_sold
    assert _sell(admin_client, asset, sale_date="2026-10-02", sale_price="10").status_code == 400
    assert AssetSale.objects.count() == 1
