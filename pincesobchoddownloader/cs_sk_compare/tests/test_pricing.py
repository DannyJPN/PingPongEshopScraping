import pytest

from cssklib.pricing import PriceConfig, expected_sk_price, expected_standard_price, find_rule, within_tolerance
from conftest import make_product


def _product(brand, root):
    return make_product(manufacturer={"name": brand}, categories=[{"main": True, "path": {"1": root}}])


@pytest.mark.parametrize("brand,root,discount", [
    ("Butterfly", "Textil", 0.05),
    ("Butterfly", "Potahy", 0.05),
    ("Andro", "Potahy", 0.05),
    ("Andro", "Dřeva", 0.05),
    ("Andro", "Textil", None),
    ("Stiga", "Potahy", 0.05),
    ("Stiga", "Dřeva", None),
    ("Tibhar", "Míčky", 0.05),
    ("Victas", "Potahy", 0.10),
    ("Victas", "Dřeva", 0.10),
    ("Victas", "Pouzdra", None),
    ("Donic", "Potahy", None),
])
def test_find_rule(brand, root, discount):
    rule = find_rule(_product(brand, root), PriceConfig())
    assert (rule[2] if rule else None) == discount


def test_find_rule_without_manufacturer():
    assert find_rule(make_product(manufacturer=None), PriceConfig()) is None


def test_expected_prices():
    config = PriceConfig()
    assert expected_sk_price(2500, "standardPrice", 0.05, config) == pytest.approx(95.0)
    assert expected_sk_price(1100, "standardPrice", 0.10, config) == pytest.approx(39.6)
    # net price goes through gross: 1000 * 1.21 / 25 * 0.95 / 1.23
    assert expected_sk_price(1000, "price", 0.05, config) == pytest.approx(37.3821, abs=1e-3)
    assert expected_sk_price(None, "price", 0.05, config) is None
    assert expected_standard_price(264.46, "cs", config) == pytest.approx(320.0, abs=0.01)
    assert expected_standard_price(6.34, "sk", config) == pytest.approx(7.8, abs=0.01)
    assert expected_standard_price(None, "sk", config) is None


def test_tolerance_boundary():
    config = PriceConfig()
    assert within_tolerance(39.6, 39.7, config)
    assert not within_tolerance(39.6, 39.8, config)
    assert within_tolerance(10, 10.1, PriceConfig(tolerance=0.1))
