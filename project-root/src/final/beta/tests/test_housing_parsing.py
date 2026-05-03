import re


def parse_price(price_str):
    if not isinstance(price_str, str):
        return None
    digits = re.sub(r"[^\d]", "", price_str)
    return float(digits) if digits else None


def test_parse_price_with_currency_text():
    assert parse_price("45 000 000 ₸") == 45000000.0


def test_parse_price_invalid_input():
    assert parse_price(None) is None
    assert parse_price("unknown") is None
