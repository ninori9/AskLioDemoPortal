import math
import types

from app.services import procurement_service
from app.models.user import User
from app.schemas.procurement import (
    ProcurementRequestCreate,
    OrderLineIn,
)

def _lite_passthrough(req):
    """Bypass full mapper; return the ORM object so we can assert fields directly."""
    return req

def test_total_price_with_summary_fields(db, fake_classifier, mute_weaviate, monkeypatch):
    monkeypatch.setattr(procurement_service, "to_lite_out", _lite_passthrough)

    body = ProcurementRequestCreate(
        title="Test Offer A",
        vendorName="Vendor GmbH",
        vatID="DE123456789",
        orderLines=[
            OrderLineIn(description="Item A", unitPriceCents=10000, quantity=1,   unit="pcs"),
            OrderLineIn(description="Item B", unitPriceCents=2500,  quantity=3.0, unit="pcs"),  # float qty
        ],
        shippingCents=1500,
        taxCents=1900,
        totalDiscountCents=200,
    )
    user = User(id="u1")

    out = procurement_service.create_request(db, body, user)

    # Lines: 10000 + (2500 * 3.0 = 7500) = 17500
    # Summary: +1500 +1900 -200 = +3200
    # Total: 20700
    assert out.totalCosts == 20700
    assert out.shippingCents == 1500
    assert out.taxCents == 1900
    assert out.discountCents == 200
    # sanity: float qty computed as cents int
    assert isinstance(out.totalCosts, int)

def test_total_price_handles_partial_nones(db, fake_classifier, mute_weaviate, monkeypatch):
    """Ensure None summary fields are safely treated as 0 in calculations."""
    monkeypatch.setattr(procurement_service, "to_lite_out", _lite_passthrough)

    body = ProcurementRequestCreate(
        title="Test Offer B",
        vendorName="Vendor GmbH",
        vatID="DE987654321",
        orderLines=[
            OrderLineIn(description="Service X", unitPriceCents=3333, quantity=2, unit="h"),
        ],
        shippingCents=None,   # simulate missing shipping
        taxCents=1900,        # only tax provided
        totalDiscountCents=None,
    )
    user = User(id="u2")

    out = procurement_service.create_request(db, body, user)

    # 3333 * 2 = 6666 + 1900 tax = 8566 total
    assert out.totalCosts == 8566

    # Expected: missing fields stored as 0, provided field retained
    assert out.shippingCents in (None, 0)
    assert out.taxCents == 1900
    assert out.discountCents in (None, 0)

def test_large_values_and_rounding(db, fake_classifier, mute_weaviate, monkeypatch):
    monkeypatch.setattr(procurement_service, "to_lite_out", _lite_passthrough)

    # Float quantity that would produce a .5 in cents total — should round to nearest int
    body = ProcurementRequestCreate(
        title="Rounding Edge",
        vendorName="Vendor",
        vatID="DE112233445",
        orderLines=[
            OrderLineIn(description="Edge", unitPriceCents=999, quantity=1.5, unit="pcs"),
        ],
        shippingCents=1,
        taxCents=0,
        totalDiscountCents=0,
    )
    user = User(id="u3")

    out = procurement_service.create_request(db, body, user)

    # 999 * 1.5 = 1498.5 → expect int rounding consistent with service logic
    expected_lines = round(999 * 1.5)
    assert out.totalCosts == expected_lines + 1  # + shipping 1