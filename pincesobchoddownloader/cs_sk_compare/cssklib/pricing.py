"""
Price rules.

Fields (verified on real exports):
  price          cena bez DPH
  standardPrice  cena běžná = price * (1 + DPH)   (CZ 21 %, SK 23 %)

CZ -> SK conversion (only listed brands / categories, otherwise prices are set manually):
  SK standardPrice = CZ standardPrice / 25 * (1 - discount)
  SK price         = CZ price * (1 + DPH_CZ) / 25 * (1 - discount) / (1 + DPH_SK)
"""
from dataclasses import dataclass, field

from cssklib.constants import BRAND_PRICE_RULES, CZK_PER_EUR, PRICE_TOLERANCE, VAT_RATES
from cssklib.values import fold_text, get_brand, get_root_categories


@dataclass
class PriceConfig:
    vat_rates: dict = field(default_factory=lambda: dict(VAT_RATES))
    czk_per_eur: float = CZK_PER_EUR
    tolerance: float = PRICE_TOLERANCE
    brand_rules: dict = field(default_factory=lambda: dict(BRAND_PRICE_RULES))

    def vat_factor(self, side):
        return 1 + self.vat_rates[side] / 100.0


def find_rule(cs_product, config):
    """Return (brand, categories, discount) if the conversion rule applies to the product, else None."""
    brand = fold_text(get_brand(cs_product))
    rule = config.brand_rules.get(brand)
    if rule is None:
        return None
    categories, discount = rule
    if categories is not None:
        roots = get_root_categories(cs_product)
        if not any(root in categories for root in roots):
            return None
    return brand, categories, discount


def expected_sk_price(cs_value, field_name, discount, config):
    """Expected SK value of `price` or `standardPrice` from the CZ value."""
    if cs_value is None:
        return None
    gross = cs_value * config.vat_factor("cs") if field_name == "price" else cs_value
    sk_gross = gross / config.czk_per_eur * (1 - discount)
    if field_name == "price":
        return sk_gross / config.vat_factor("sk")
    return sk_gross


def within_tolerance(expected, actual, config):
    return abs(expected - actual) <= config.tolerance + 1e-9


def expected_standard_price(price, side, config):
    if price is None:
        return None
    return price * config.vat_factor(side)
