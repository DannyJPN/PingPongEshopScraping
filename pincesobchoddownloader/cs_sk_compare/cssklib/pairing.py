"""
Product and variant identity.

Product identity = catalog code + name.
Variant identity = catalog code + variant options (e.g. Barva=černá, Velikost=XL).
"""
from collections import OrderedDict, defaultdict

from cssklib.values import get_code, get_name, normalize_text


class Pairing:
    def __init__(self):
        self.matched = []          # [(cs_product, sk_product)]
        self.cs_only = []          # [cs_product]
        self.sk_only = []          # [sk_product]
        self.name_conflicts = []   # [(cs_product, sk_product)] same code, different name
        self.duplicates = {"cs": [], "sk": []}  # codes present more than once

    def summary(self):
        return {
            "matched": len(self.matched),
            "cs_only": len(self.cs_only),
            "sk_only": len(self.sk_only),
            "name_conflicts": len(self.name_conflicts),
            "duplicate_codes_cs": len(self.duplicates["cs"]),
            "duplicate_codes_sk": len(self.duplicates["sk"]),
        }


def _group_by_code(products):
    groups = OrderedDict()
    for product in products:
        groups.setdefault(get_code(product), []).append(product)
    return groups


def pair_products(cs_products, sk_products):
    pairing = Pairing()
    cs_groups = _group_by_code(cs_products)
    sk_groups = _group_by_code(sk_products)
    for side, groups in (("cs", cs_groups), ("sk", sk_groups)):
        pairing.duplicates[side] = sorted(code for code, items in groups.items() if len(items) > 1)

    for code in sorted(set(cs_groups) | set(sk_groups)):
        cs_items = list(cs_groups.get(code, []))
        sk_items = list(sk_groups.get(code, []))
        for cs in list(cs_items):
            twin = next((sk for sk in sk_items if get_name(sk, "sk") == get_name(cs, "cs")), None)
            if twin is not None:
                pairing.matched.append((cs, twin))
                cs_items.remove(cs)
                sk_items.remove(twin)
        while cs_items and sk_items:
            pairing.name_conflicts.append((cs_items.pop(0), sk_items.pop(0)))
        pairing.cs_only.extend(cs_items)
        pairing.sk_only.extend(sk_items)
    return pairing


# --- Variants ----------------------------------------------------------------

def variant_key(variant):
    """Identity of variant options: sorted tuple of (option name, option value)."""
    options = variant.get("options") or []
    return tuple(sorted(
        (normalize_text(o.get("name")) or "", normalize_text(o.get("value")) or "")
        for o in options
    ))


def format_variant_key(key):
    return ", ".join(f"{name}={value}" for name, value in key) or "(bez parametrů)"


def variant_code(variant):
    return normalize_text(variant.get("catalogNumber")) or ""


class VariantPairing:
    def __init__(self):
        self.matched = []          # [(key, cs_variant, sk_variant)] same options and same code
        self.code_mismatch = []    # [(key, cs_variant, sk_variant)] same options, different code
        self.option_mismatch = []  # [(cs_variant, sk_variant)] same code, different options
        self.cs_only = []          # [(key, cs_variant)]
        self.sk_only = []          # [(key, sk_variant)]
        self.duplicate_keys = {"cs": [], "sk": []}


def pair_variants(cs_product, sk_product):
    result = VariantPairing()
    cs_groups, sk_groups = defaultdict(list), defaultdict(list)
    for variant in cs_product.get("variants") or []:
        cs_groups[variant_key(variant)].append(variant)
    for variant in sk_product.get("variants") or []:
        sk_groups[variant_key(variant)].append(variant)
    for side, groups in (("cs", cs_groups), ("sk", sk_groups)):
        result.duplicate_keys[side] = sorted(k for k, items in groups.items() if len(items) > 1)

    cs_rest, sk_rest = [], []
    for key in sorted(set(cs_groups) | set(sk_groups)):
        cs_items = list(cs_groups.get(key, []))
        sk_items = list(sk_groups.get(key, []))
        for cs in list(cs_items):
            twin = next((sk for sk in sk_items if variant_code(sk) == variant_code(cs)), None)
            if twin is not None:
                result.matched.append((key, cs, twin))
                cs_items.remove(cs)
                sk_items.remove(twin)
        while cs_items and sk_items:
            result.code_mismatch.append((key, cs_items.pop(0), sk_items.pop(0)))
        cs_rest.extend((key, v) for v in cs_items)
        sk_rest.extend((key, v) for v in sk_items)

    sk_by_code = defaultdict(list)
    for key, variant in sk_rest:
        sk_by_code[variant_code(variant)].append((key, variant))
    for key, variant in cs_rest:
        candidates = sk_by_code.get(variant_code(variant))
        if variant_code(variant) and candidates:
            _, sk_variant = candidates.pop(0)
            result.option_mismatch.append((variant, sk_variant))
        else:
            result.cs_only.append((key, variant))
    for items in sk_by_code.values():
        result.sk_only.extend(items)
    result.sk_only.sort(key=lambda item: (item[0], variant_code(item[1])))
    return result
