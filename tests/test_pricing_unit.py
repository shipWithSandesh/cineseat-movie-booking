import pytest

from app.main import price_for, seat_class, valid_seat


@pytest.mark.unit
@pytest.mark.parametrize("seat,cls", [("A1", "SILVER"), ("B10", "SILVER"), ("C5", "GOLD"), ("F1", "GOLD"), ("G3", "PREMIUM"), ("H10", "PREMIUM")])
def test_seat_class_boundaries(seat, cls):
    assert seat_class(seat) == cls


@pytest.mark.unit
@pytest.mark.parametrize("seat,ok", [("A1", True), ("H10", True), ("A0", False), ("A11", False), ("Z1", False), ("A", False), ("1A", False)])
def test_seat_validation(seat, ok):
    assert valid_seat(seat) is ok


@pytest.mark.unit
def test_price_includes_ten_percent_convenience_fee():
    assert price_for(["A1", "C1", "G1"]) == {"subtotal": 780, "convenience_fee": 78, "total": 858}
