import copy
import hashlib
import os

import pytest

from cssklib.checks import (
    CHECKS, IGNORED_FIELDS, PRODUCT_FIELDS, SPECIAL_FIELDS, TRANSLATION_FIELDS, VARIANT_FIELDS,
    VARIANT_IGNORED_FIELDS, VARIANT_SPECIAL_FIELDS,
    Context, run_check, select_vision_products,
)
from cssklib.images import ImageStore
from cssklib.pairing import pair_products
from conftest import make_product, make_variant, sk_twin

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(check_id, cs, sk, **ctx_kwargs):
    ctx = Context(cs_products=cs, sk_products=sk, pairing=pair_products(cs, sk), **ctx_kwargs)
    return run_check(CHECKS[check_id], ctx)


def test_every_check_has_its_own_script():
    for check_id in CHECKS:
        if check_id == "vision":
            assert os.path.isfile(os.path.join(SCRIPTS_DIR, "check_photos_vision.py"))
            assert os.path.isfile(os.path.join(SCRIPTS_DIR, "check_photos_vision_all.py"))
            continue
        path = os.path.join(SCRIPTS_DIR, f"check_{check_id}.py")
        assert os.path.isfile(path), path
        with open(path, encoding="utf-8") as handle:
            assert f'run_single_check("{check_id}")' in handle.read()
    assert os.path.isfile(os.path.join(SCRIPTS_DIR, "check_all.py"))


def test_registry_covers_all_json_properties():
    product_keys = set(make_product()) | {
        "mpn", "createdAt", "updatedAt", "priority", "homepage", "sales", "deliveryFree", "erotic", "adult",
        "voucherDiscount", "purchasePrice", "deliveryDate", "deliveryDateAuto", "manageStock", "stockQuantity",
        "quantityPack", "limitMultiple", "limitMin", "limitMax", "weight", "length", "comment", "availability",
        "guarantee", "discount", "related", "accessory", "gift", "pairs", "videos", "files", "parameters",
        "warehouse", "wholesale"}
    assert product_keys <= set(PRODUCT_FIELDS) | SPECIAL_FIELDS | IGNORED_FIELDS
    assert set(make_variant("x", [])) | {"mpn", "purchasePrice", "deliveryDate", "deliveryDateAuto",
                                         "manageStock", "weight", "length"} <= set(VARIANT_FIELDS) | VARIANT_SPECIAL_FIELDS | VARIANT_IGNORED_FIELDS
    for field in TRANSLATION_FIELDS:
        assert f"translations_{field}" in CHECKS
    assert not CHECKS["vision"].default_enabled


# dataset level / external checks have their own tests
SPECIAL_CHECKS = ("images_hash", "vision", "shop_category_mapping_files")


@pytest.mark.parametrize("check_id", sorted(c for c in CHECKS if c not in SPECIAL_CHECKS))
def test_identical_shops_have_no_findings(check_id):
    cs = make_product(variants=[make_variant("BTY01000001-01", [("Barva", "černá")])])
    result = run(check_id, [cs], [sk_twin(cs)])
    assert result.findings == [], [f.message for f in result.findings]


def test_field_check_reports_difference():
    cs = make_product(visibility=True)
    sk = sk_twin(cs)
    sk["visibility"] = False
    findings = run("visibility", [cs], [sk]).findings
    assert len(findings) == 1
    assert (findings[0].cs_value, findings[0].sk_value) == (True, False)
    assert findings[0].product_code == "BTY01000001"


def test_nested_field_check_lists_paths():
    cs = make_product(feeds={"glami": {"cpc": 320, "hidden": 0}, "zbozi": {"cpc": 1}})
    sk = sk_twin(cs)
    sk["feeds"] = {"glami": {"cpc": 190, "hidden": 0}, "zbozi": {"cpc": 2}}
    finding = run("feeds", [cs], [sk]).findings[0]
    assert finding.message == "Liší se: glami.cpc, zbozi.cpc"
    assert [d["path"] for d in finding.details["differences"]] == ["glami.cpc", "zbozi.cpc"]


def test_list_field_check_message():
    cs = make_product(tags=[{"id": 4, "name": "Doporučujeme"}])
    sk = sk_twin(cs)
    sk["tags"] = []
    finding = run("tags", [cs], [sk]).findings[0]
    assert "položky seznamu" in finding.message or finding.message == "Hodnota se v CZ a SK liší"


def test_translation_check():
    cs = make_product()
    sk = sk_twin(cs)
    sk["translations"]["cs"]["description"] = "<p>jiný</p>"
    findings = run("translations_description", [cs], [sk]).findings
    assert [f.property for f in findings] == ["description"]


def test_other_fields_detects_new_properties():
    cs = make_product(newField=1)
    sk = sk_twin(cs)
    sk["newField"] = 2
    result = run("other_fields", [cs], [sk])
    assert [f.property for f in result.findings] == ["newField"]
    assert result.stats["fields"] == "newField"


def test_identity_check():
    cs = [make_product("A", "A"), make_product("B", "B", visibility=False), make_product("C", "C")]
    sk = [make_product("A", "A", side="sk"), make_product("C", "C x", side="sk"),
          make_product("D", "D", side="sk"), make_product("D", "D", side="sk")]
    result = run("identity", cs, sk)
    messages = [(f.product_code, f.severity, f.property) for f in result.findings]
    assert ("B", "warning", "catalogNumber+name") in messages
    assert ("C", "error", "name") in messages
    assert ("D", "error", "catalogNumber+name") in messages
    assert ("D", "error", "catalogNumber") in messages
    assert result.stats["matched"] == 1


def test_vat_check():
    cs = make_product()
    sk = sk_twin(cs)
    sk["vat"] = None
    findings = run("vat", [cs], [sk]).findings
    assert [(f.side, f.expected) for f in findings] == [("sk", 23.0)]


def test_price_conversion_within_and_outside_tolerance():
    cs = make_product(standardPrice=1100, price=909.09, manufacturer={"name": "Victas"})
    ok = sk_twin(cs, standard=39.65, price=32.24)
    assert run("standardPrice", [cs], [ok]).findings == []
    assert run("price", [cs], [ok]).findings == []
    bad = sk_twin(cs, standard=39.8, price=32.36)
    finding = run("standardPrice", [cs], [bad]).findings[0]
    assert finding.expected == 39.6 and finding.details["discount"] == 0.10
    assert "rozdíl +0.20" in finding.message
    assert run("price", [cs], [bad]).findings[0].expected == pytest.approx(32.2, abs=0.01)


def test_price_conversion_not_applicable_and_missing():
    cs = make_product(manufacturer={"name": "Donic"})
    result = run("standardPrice", [cs], [sk_twin(cs, standard=999)])
    assert result.findings == [] and result.stats == {"checked": 0, "not_applicable": 1}
    cs = make_product()
    sk = sk_twin(cs)
    sk["standardPrice"] = None
    assert run("standardPrice", [cs], [sk]).findings[0].message == "Cena je vyplněna jen na jedné straně"
    cs["standardPrice"] = None
    assert run("standardPrice", [cs], [sk]).findings == []


def test_price_vat_relation_both_sides():
    cs = make_product(price=619.83, standardPrice=580)
    sk = sk_twin(cs, standard=7.8, price=6.34)
    findings = run("price_vat", [cs], [sk]).findings
    assert [(f.side, f.expected) for f in findings] == [("cs", 749.99)]
    sk["price"] = 7.0
    assert {f.side for f in run("price_vat", [cs], [sk]).findings} == {"cs", "sk"}


def test_price_vat_checks_unpaired_products_too():
    cs = make_product("A", "A", price=100, standardPrice=100)
    assert len(run("price_vat", [cs], []).findings) == 1


def test_variants_check_reports_identity_problems():
    cs = make_product(variants=[make_variant("P-01", [("Barva", "černá")]), make_variant("P-02", [("Barva", "bílá")]),
                                make_variant("P-03", [("Barva", "modrá")])])
    sk = sk_twin(cs)
    sk["variants"] = [make_variant("P-09", [("Barva", "černá")]), make_variant("P-03", [("Barva", "zelená")]),
                      make_variant("P-04", [("Barva", "žlutá")])]
    findings = run("variants", [cs], [sk]).findings
    props = sorted((f.property, f.variant_code, f.side) for f in findings)
    assert props == [
        ("variants", "P-02", "cs"),
        ("variants", "P-04", "sk"),
        ("variants.catalogNumber", "P-01", "both"),
        ("variants.options", "P-03", "both"),
    ]


def test_variants_check_duplicate_warning():
    cs = make_product(variants=[make_variant("P-01", [("Barva", "černá")]), make_variant("P-02", [("Barva", "černá")])])
    sk = sk_twin(cs)
    findings = run("variants", [cs], [sk]).findings
    assert [(f.severity, f.side) for f in findings] == [("warning", "cs"), ("warning", "sk")]


def test_variant_field_check():
    cs = make_product(variants=[make_variant("P-01", [("Barva", "černá")], stockQuantity=5, id=1)])
    sk = sk_twin(cs)
    sk["variants"][0]["stockQuantity"] = 3
    sk["variants"][0]["id"] = 99
    findings = run("variant_stockQuantity", [cs], [sk]).findings
    assert [(f.variant_code, f.cs_value, f.sk_value) for f in findings] == [("P-01", 5, 3)]
    assert findings[0].variant_options == "Barva=černá"


def test_variant_price_checks_use_inherited_price():
    cs = make_product(variants=[make_variant("P-01", [("Barva", "černá")], standardPrice=2420, price=2000)])
    sk = sk_twin(cs)
    sk["variants"][0]["standardPrice"] = None  # inherits SK product price 45.98, expected 91.96
    finding = run("variant_standardPrice", [cs], [sk]).findings[0]
    assert finding.expected == 91.96 and finding.variant_code == "P-01"
    sk["variants"][0]["standardPrice"] = 91.96
    sk["variants"][0]["price"] = 74.76
    assert run("variant_standardPrice", [cs], [sk]).findings == []
    assert run("variant_price", [cs], [sk]).findings == []
    sk["variants"][0]["price"] = 70
    assert len(run("variant_price_vat", [cs], [sk]).findings) == 1


def test_images_path_check():
    cs = make_product()
    sk = sk_twin(cs)
    sk["images"][1]["url"] = "https://www.pincesobchod.sk/files/products/images/original/9.jpg"
    sk["images"].append({"id": 3, "position": 3, "default": False, "url": "https://www.pincesobchod.sk/3.jpg"})
    props = [f.property for f in run("images_path", [cs], [sk]).findings]
    assert props == ["images.count", "images[2].path"]


def test_images_path_default_image():
    cs = make_product()
    sk = sk_twin(cs)
    sk["images"][0]["default"], sk["images"][1]["default"] = False, True
    assert [f.property for f in run("images_path", [cs], [sk]).findings] == ["images.default"]
    sk["images"][0]["url"] = "https://www.pincesobchod.sk/other.jpg"
    sk["images"][0]["default"], sk["images"][1]["default"] = True, False
    assert [f.property for f in run("images_path", [cs], [sk]).findings] == ["images[1].path"]
    sk["images"] = []
    assert [f.property for f in run("images_path", [cs], [sk]).findings] == ["images.count", "images.default"]


def test_images_hash_check(tmp_path):
    cs = make_product()
    sk = sk_twin(cs)
    content = {
        cs["images"][0]["url"]: b"same", sk["images"][0]["url"]: b"same",
        cs["images"][1]["url"]: b"cz", sk["images"][1]["url"]: b"sk",
    }
    store = ImageStore(str(tmp_path), fetch=content.get, workers=2)
    result = run("images_hash", [cs], [sk], image_store=store)
    assert [f.property for f in result.findings] == ["images[2].sha256"]
    assert result.findings[0].cs_value == hashlib.sha256(b"cz").hexdigest()
    assert result.findings[0].details["same_path"] is True
    assert result.stats["checked"] == 2 and result.stats["failed"] == 0


def test_images_hash_download_failure(tmp_path):
    cs = make_product(images=[make_product()["images"][0]])
    sk = sk_twin(cs)
    store = ImageStore(str(tmp_path), fetch=lambda url: None)
    finding = run("images_hash", [cs], [sk], image_store=store).findings[0]
    assert finding.severity == "warning"


def test_images_hash_requires_store():
    cs = make_product()
    with pytest.raises(RuntimeError):
        run("images_hash", [cs], [sk_twin(cs)])


class FakeChecker:
    model = "fake"
    max_images = 0
    refresh = False

    def __init__(self, verdicts, fail_codes=()):
        self.verdicts = verdicts
        self.fail_codes = fail_codes
        self.usage = {"requests": 1}
        self.cache = type("C", (), {"get": staticmethod(lambda key: None)})()

    def check_product(self, product, side):
        if product["catalogNumber"] in self.fail_codes:
            raise RuntimeError("boom")
        return [{"index": i + 1, "url": img["url"], "verdict": self.verdicts[i], "reason": "r", "cached": False}
                for i, img in enumerate(product["images"])]


def test_vision_check_findings():
    cs = [make_product("A", "A"), make_product("B", "B")]
    vision = {"checker": FakeChecker(["product", "unrelated"], fail_codes=("B",)), "side": "cs"}
    result = run("vision", cs, [], vision=vision)
    assert [(f.product_code, f.severity, f.property) for f in result.findings] == [
        ("A", "error", "images[2].vision"), ("B", "warning", "images.vision")]
    assert result.stats["product"] == 1 and result.stats["unrelated"] == 1 and result.stats["errors"] == 1


def test_vision_unclear_is_warning():
    vision = {"checker": FakeChecker(["related", "unclear"]), "side": "cs"}
    findings = run("vision", [make_product()], [], vision=vision).findings
    assert [f.severity for f in findings] == ["warning"]


def test_vision_requires_checker():
    with pytest.raises(RuntimeError):
        run("vision", [make_product()], [])


def test_vision_dry_run_counts_images():
    vision = {"checker": FakeChecker([]), "side": "both", "dry_run": True}
    cs = make_product()
    result = run("vision", [cs], [sk_twin(cs)], vision=vision)
    assert result.stats["images_to_send"] == 4 and result.findings == []


def test_select_vision_products_filters():
    products = [make_product("A", "A"), make_product("B", "B", manufacturer={"name": "Andro"}),
                make_product("C", "C", visibility=False), make_product("D", "D", images=[])]
    ctx = Context(cs_products=products, sk_products=[], pairing=pair_products(products, []))
    ctx.vision = {"side": "cs"}
    assert [p["catalogNumber"] for _, p in select_vision_products(ctx)] == ["A", "B", "C"]
    ctx.vision = {"side": "cs", "codes": ["B", "C"], "active_only": True}
    assert [p["catalogNumber"] for _, p in select_vision_products(ctx)] == ["B"]
    ctx.vision = {"side": "cs", "brands": ["andro"]}
    assert [p["catalogNumber"] for _, p in select_vision_products(ctx)] == ["B"]
    ctx.vision = {"side": "cs", "limit": 1}
    assert len(select_vision_products(ctx)) == 1


def test_active_only_context_filters_unpaired_side_checks():
    active = make_product("A", "A", price=1, standardPrice=5)
    inactive = make_product("B", "B", price=1, standardPrice=5, visibility=False)
    products = [active, inactive]
    ctx = Context(cs_products=products, sk_products=[], pairing=pair_products(products, []), active_only=True)
    assert [f.product_code for f in run_check(CHECKS["price_vat"], ctx).findings] == ["A"]


def test_variant_pairing_is_cached():
    cs = make_product()
    sk = sk_twin(cs)
    ctx = Context(cs_products=[cs], sk_products=[sk], pairing=pair_products([cs], [sk]))
    assert ctx.variant_pairing(cs, sk) is ctx.variant_pairing(cs, sk)


def test_sk_twin_helper_is_independent_copy():
    cs = make_product()
    sk = sk_twin(cs)
    sk["images"][0]["url"] = "changed"
    assert cs["images"][0]["url"] != "changed" and copy.deepcopy(cs) == cs


def test_product_and_variant_ids_are_never_compared():
    """Shop internal IDs may differ between CZ and SK."""
    assert "id" not in CHECKS and "variant_id" not in CHECKS
    assert not os.path.exists(os.path.join(SCRIPTS_DIR, "check_id.py"))
    assert not os.path.exists(os.path.join(SCRIPTS_DIR, "check_variant_id.py"))
    cs = make_product(id=1, variants=[make_variant("BTY01000001-01", [("Barva", "černá")], id=10)])
    sk = sk_twin(cs)
    sk["id"] = 999
    sk["variants"][0]["id"] = 888
    ctx = Context(cs_products=[cs], sk_products=[sk], pairing=pair_products([cs], [sk]))
    for check in CHECKS.values():
        if check.id in SPECIAL_CHECKS:
            continue
        assert run_check(check, ctx).findings == [], check.id
