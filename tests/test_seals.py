from app.services.seal_service import price_display


def test_price_display():
    assert price_display(100) == "$1.00"
