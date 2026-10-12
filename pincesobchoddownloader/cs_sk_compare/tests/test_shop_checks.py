import pytest

from cssklib.checks import CHECKS, Context, run_check
from cssklib.pairing import pair_products
from cssklib.shop_checks import slugify
from conftest import make_product, make_variant, sk_twin

SHOP_IDS = sorted(c for c, check in CHECKS.items() if check.group == "shop")


def run(check_id, products, side="cs", sides=("cs", "sk")):
    cs, sk = (products, []) if side == "cs" else ([], products)
    ctx = Context(cs_products=cs, sk_products=sk, pairing=pair_products(cs, sk), shop_sides=sides)
    return run_check(CHECKS[check_id], ctx)


def test_shop_group_contents():
    assert {"vat", "price_vat", "variant_price_vat", "shop_name_metaTitle", "shop_name_heurekacs_productname",
            "shop_name_heurekacs_product", "shop_name_zbozi_productname", "shop_name_zbozi_product",
            "shop_metaDescription", "shop_slug", "shop_feed_category", "shop_feed_cpc", "shop_images",
            "shop_variant_codes", "shop_brand_in_name"} == set(SHOP_IDS)


@pytest.mark.parametrize("check_id", SHOP_IDS)
@pytest.mark.parametrize("side", ["cs", "sk"])
def test_consistent_product_has_no_findings(check_id, side):
    cs = make_product(variants=[make_variant("BTY01000001-01", [("Barva", "černá")])])
    product = cs if side == "cs" else sk_twin(cs)
    assert run(check_id, [product], side).findings == []


def test_slugify():
    assert slugify("Čistič ANDRO Combi Free 100 ml") == "cistic-andro-combi-free-100-ml"
    assert slugify("Houbička BUTTERFLY černá/růžová") == "houbicka-butterfly-cerna-ruzova"
    assert slugify(None) == ""


@pytest.mark.parametrize("check_id,mutate,prop", [
    ("shop_name_metaTitle", lambda p: p["translations"]["cs"].update(metaTitle="Jiný"), "translations.metaTitle"),
    ("shop_name_heurekacs_productname", lambda p: p["feeds"]["heurekacs"].update(productname="X"),
     "feeds.heurekacs.productname"),
    ("shop_name_heurekacs_product", lambda p: p["feeds"]["heurekacs"].update(product="X"), "feeds.heurekacs.product"),
    ("shop_name_zbozi_productname", lambda p: p["feeds"]["zbozi"].update(productname="X"), "feeds.zbozi.productname"),
    ("shop_name_zbozi_product", lambda p: p["feeds"]["zbozi"].update(product="X"), "feeds.zbozi.product"),
])
def test_name_copy_mismatch(check_id, mutate, prop):
    product = make_product()
    mutate(product)
    findings = run(check_id, [product]).findings
    assert [(f.property, f.severity, f.side, f.expected) for f in findings] == [
        (prop, "error", "cs", "Potah BUTTERFLY Tenergy 05")]


def test_name_copy_whitespace_is_ignored_case_is_not():
    product = make_product()
    product["translations"]["cs"]["metaTitle"] = "  Potah  BUTTERFLY Tenergy 05 "
    assert run("shop_name_metaTitle", [product]).findings == []
    product["translations"]["cs"]["metaTitle"] = "Potah Butterfly Tenergy 05"
    assert len(run("shop_name_metaTitle", [product]).findings) == 1


def test_name_copy_empty_is_warning_and_stale_hint():
    product = make_product()
    product["translations"]["cs"]["metaTitle"] = None
    result = run("shop_name_metaTitle", [product])
    assert result.findings[0].severity == "warning" and result.stats["empty"] == 1
    product = make_product()
    product["translations"]["cs"]["metaTitle"] = "Starý titulek"
    product["feeds"]["zbozi"]["productname"] = "Starý titulek"
    finding = run("shop_name_zbozi_productname", [product]).findings[0]
    assert "starý SEO titulek" in finding.message


def test_name_copy_sk_side_value():
    product = sk_twin(make_product())
    product["feeds"]["zbozi"]["product"] = "X"
    finding = run("shop_name_zbozi_product", [product], side="sk").findings[0]
    assert (finding.side, finding.sk_value, finding.cs_value) == ("sk", "X", None)


def test_meta_description_and_slug():
    product = make_product()
    product["translations"]["cs"]["metaDescription"] = "Jiný popis"
    product["translations"]["cs"]["slug"] = "stary-slug"
    assert run("shop_metaDescription", [product]).findings[0].expected == "Popis"
    assert run("shop_slug", [product]).findings[0].expected == "potah-butterfly-tenergy-05"


def test_feed_category_rules():
    product = make_product(categories=[
        {"main": True, "path": {"44": "Potahy"}},
        {"main": False, "path": {"44": "Potahy", "66": "Softy"}},
    ])
    for key in ("glami", "google", "heurekacs", "zbozi"):
        product["feeds"][key]["category"] = "Potahy>Softy"
    assert run("shop_feed_category", [product]).findings == []
    product["feeds"]["glami"]["category"] = "Potahy"
    product["feeds"]["zbozi"]["category"] = "Stoly"
    findings = run("shop_feed_category", [product]).findings
    assert [f.property for f in findings] == ["feeds.*.category", "feeds.glami.category", "feeds.zbozi.category"]
    assert "nemá" in findings[2].message and "nemá" not in findings[1].message
    assert findings[1].expected == "Potahy>Softy"
    assert findings[1].details["product_categories"] == ["Potahy", "Potahy>Softy"]


def test_feed_category_ignores_empty_feed_category():
    product = make_product()
    product["feeds"]["shopalikecs"] = {"hidden": 0, "category": "", "cpc": 1210}
    assert run("shop_feed_category", [product]).findings == []


def test_feed_category_without_feeds_or_categories():
    assert run("shop_feed_category", [make_product(feeds={})]).stats["checked"] == 0
    assert run("shop_feed_category", [make_product(categories=[])]).findings == []


def test_feed_cpc():
    product = make_product()
    product["feeds"]["zbozi"]["cpc_search"] = "1210.0"
    assert run("shop_feed_cpc", [product]).findings == []
    product["feeds"]["zbozi"]["cpc"] = 190
    finding = run("shop_feed_cpc", [product]).findings[0]
    assert finding.severity == "warning" and finding.expected == 1210
    product["feeds"]["zbozi"]["cpc"] = "abc"
    assert len(run("shop_feed_cpc", [product]).findings) == 1
    assert run("shop_feed_cpc", [make_product(feeds={})]).stats["checked"] == 0


def test_images_structure():
    product = make_product()
    product["images"][1]["default"] = True
    assert [f.message for f in run("shop_images", [product]).findings] == [
        "Produkt má 2 hlavních fotek (má mít právě 1)"]
    product["images"][0]["default"] = False
    assert run("shop_images", [product]).findings[0].message == "Hlavní fotka není na první pozici"
    product = make_product()
    product["images"][1]["position"] = 5
    product["images"][1]["url"] = product["images"][0]["url"]
    props = [f.property for f in run("shop_images", [product]).findings]
    assert props == ["images.position", "images.url"]
    assert run("shop_images", [make_product(images=[])]).stats["checked"] == 0


def test_variant_codes():
    first = make_product("A1", "A BUTTERFLY", variants=[make_variant("A1-01", []), make_variant("X-01", []),
                                                         make_variant("A1-01", [])])
    second = make_product("B1", "B BUTTERFLY", variants=[make_variant("A1-01", [])])
    messages = [(f.product_code, f.variant_code, f.message) for f in run("shop_variant_codes", [first, second]).findings]
    assert ("A1", "X-01", "Kód varianty nezačíná kódem produktu 'A1-'") in messages
    assert ("A1", "A1-01", "Kód varianty je u produktu vícekrát") in messages
    assert ("B1", "A1-01", "Kód varianty je použit i u produktu A1") in messages


def test_brand_in_name():
    assert run("shop_brand_in_name", [make_product(name="Potah Tenergy 05")]).findings[0].expected == "Butterfly"
    assert run("shop_brand_in_name", [make_product(name="Potah butterfly x")]).findings == []
    finding = run("shop_brand_in_name", [make_product(manufacturer=None)]).findings[0]
    assert finding.message == "Produkt nemá vyplněného výrobce"


def test_visible_and_archived_is_not_reported():
    """Visible + archived products are fine (no such check)."""
    assert "shop_visibility_archive" not in CHECKS


def test_shop_sides_restrict_checked_side():
    cs = make_product(name="Potah Tenergy")
    sk = sk_twin(cs)
    ctx = Context(cs_products=[cs], sk_products=[sk], pairing=pair_products([cs], [sk]), shop_sides=("sk",))
    findings = run_check(CHECKS["shop_brand_in_name"], ctx).findings
    assert [f.side for f in findings] == ["sk"]
    ctx.shop_sides = ("cs", "sk")
    assert [f.side for f in run_check(CHECKS["shop_brand_in_name"], ctx).findings] == ["cs", "sk"]
