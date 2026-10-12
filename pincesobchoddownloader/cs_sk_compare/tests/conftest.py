import copy
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from cssklib.shop_checks import slugify  # noqa: E402


def make_product(code="BTY01000001", name="Potah BUTTERFLY Tenergy 05", side="cs", **overrides):
    domain = "https://www.pincesobchod.cz" if side == "cs" else "https://www.pincesobchod.sk"
    product = {
        "id": 1, "catalogNumber": code, "guid": "g", "ean": None, "visibility": True, "archive": False,
        "price": 1000.0, "standardPrice": 1210, "vat": {"id": 1, "rate": 21 if side == "cs" else 23},
        "translations": {"cs": {"name": name, "nameext": None, "slug": slugify(name), "metaTitle": name,
                                "metaDescription": "Popis", "annotation": "Popis", "description": "<p>x</p>"}},
        "manufacturer": {"id": 1, "name": "Butterfly"},
        "categories": [{"id": 44, "main": True, "path": {"44": "Potahy"}}],
        "images": [
            {"id": 1, "position": 1, "default": True, "url": f"{domain}/files/products/images/original/1.jpg"},
            {"id": 2, "position": 2, "default": False, "url": f"{domain}/files/products/images/original/2.jpg"},
        ],
        "variants": [],
        "tags": [],
        "feeds": {
            "glami": {"hidden": 0, "category": "Potahy", "cpc": 1210},
            "google": {"hidden": 0, "category": "Potahy"},
            "heurekacs": {"hidden": 0, "productname": name, "product": name, "cpc": 1210, "category": "Potahy"},
            "zbozi": {"hidden": 0, "productname": name, "product": name, "cpc": 1210, "cpc_search": 1210,
                      "category": "Potahy"},
        },
    }
    product.update(overrides)
    return product


def make_variant(code, options, **overrides):
    variant = {
        "id": 10, "catalogNumber": code, "ean": None, "equal": True, "price": None, "standardPrice": None,
        "stockQuantity": 0, "image": None, "translations": {"cs": {"nameext": None}},
        "availability": {"id": 14, "name": "-"},
        "options": [{"id": i, "valueId": i, "position": i, "name": n, "value": v}
                    for i, (n, v) in enumerate(options, start=1)],
    }
    variant.update(overrides)
    return variant


def sk_twin(product, price=None, standard=None):
    """SK copy of a CZ product converted with the Butterfly rule (/25, -5 %)."""
    sk = copy.deepcopy(product)
    sk["vat"] = {"id": 1, "rate": 23}
    for image in sk.get("images") or []:
        image["url"] = image["url"].replace("pincesobchod.cz", "pincesobchod.sk")
    sk["standardPrice"] = standard if standard is not None else round(product["standardPrice"] / 25 * 0.95, 2)
    sk["price"] = price if price is not None else round(sk["standardPrice"] / 1.23, 2)
    return sk


@pytest.fixture
def write_json(tmp_path):
    def _write(products, name):
        path = tmp_path / name
        path.write_text(json.dumps({"data": products}, ensure_ascii=False), encoding="utf-8")
        return str(path)
    return _write
