import pytest

from cssklib.category_mapping import CategoryMappings, load_mapping
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


def _mapping_dir(tmp_path, cs_rows, sk_rows=None):
    for platform in ("Glami", "Google", "Heureka", "Zbozi"):
        for lang, rows in (("CS", cs_rows), ("SK", sk_rows)):
            path = tmp_path / f"CategoryMapping{platform}_{lang}.csv"
            text = '"KEY","VALUE"\n' + "".join(f'"{k}","{platform}: {v}"\n' for k, v in (rows or {}).items())
            path.write_text("\ufeff" + text if rows is not None else "\ufeff", encoding="utf-8")
    return CategoryMappings(str(tmp_path))


def run_mapped(products, mappings, side="cs"):
    cs, sk = (products, []) if side == "cs" else ([], products)
    ctx = Context(cs_products=cs, sk_products=sk, pairing=pair_products(cs, sk), category_mappings=mappings)
    return run_check(CHECKS["shop_feed_category"], ctx)


ROWS = {"Potahy": "Potahy na pálky", "Potahy>Softy": "Potahy na pálky", "Čističe": "Doplňky",
        "Příslušenství": "Doplňky", "Síťky": "Síťky", "Stoly": "Stoly"}


def test_feed_category_follows_project_mapping(tmp_path):
    mappings = _mapping_dir(tmp_path, ROWS)
    product = make_product(categories=[{"main": True, "path": {"44": "Potahy"}},
                                       {"main": False, "path": {"44": "Potahy", "66": "Softy"}}])
    for key in ("glami", "google", "heurekacs", "zbozi"):
        product["feeds"][key]["category"] = "Potahy>Softy"   # other shop category, same platform category
    result = run_mapped([product], mappings)
    assert result.findings == [] and result.stats["checked"] == 4
    assert result.stats["mapping_files"] == ", ".join(f"CategoryMapping{p}_CS.csv"
                                                      for p in ("Glami", "Google", "Heureka", "Zbozi"))
    # different shop category with the same platform category is fine (Čističe vs Příslušenství)
    product = make_product(categories=[{"main": True, "path": {"37": "Čističe"}}])
    for key in ("glami", "google", "heurekacs", "zbozi"):
        product["feeds"][key]["category"] = "Příslušenství"
    assert run_mapped([product], mappings).findings == []


def test_feed_category_mapped_elsewhere(tmp_path):
    mappings = _mapping_dir(tmp_path, ROWS)
    product = make_product(categories=[{"main": True, "path": {"48": "Síťky"}}])
    product["feeds"]["zbozi"]["category"] = "Stoly"
    for key in ("glami", "google", "heurekacs"):
        product["feeds"][key]["category"] = "Síťky"
    findings = run_mapped([product], mappings).findings
    assert [(f.property, f.cs_value, f.expected) for f in findings] == [
        ("feeds.zbozi.category", "Zbozi: Stoly", "Zbozi: Síťky")]
    assert findings[0].details == {"feed_category": "Stoly", "product_categories": ["Síťky"]}


def test_feed_category_missing_mappings(tmp_path):
    mappings = _mapping_dir(tmp_path, ROWS)
    product = make_product(categories=[{"main": True, "path": {"53": "Textil", "83": "Trička"}}])
    for key in ("glami", "google", "heurekacs", "zbozi"):
        product["feeds"][key]["category"] = "Textil>Trička"
    findings = run_mapped([product], mappings).findings
    assert {(f.property, f.severity) for f in findings} == {("feeds.glami.category", "error"),
                                                           ("feeds.google.category", "error"),
                                                           ("feeds.heurekacs.category", "error"),
                                                           ("feeds.zbozi.category", "error")}
    product["feeds"]["zbozi"]["category"] = "Potahy"
    findings = run_mapped([product], mappings).findings
    warnings = [f for f in findings if f.property == "categories"]
    assert [(f.severity, f.cs_value) for f in warnings] == [("warning", "Textil>Trička")]
    assert "CategoryMappingZbozi_CS.csv" in warnings[0].message


def test_feed_category_sk_falls_back_to_cs_mapping(tmp_path):
    mappings = _mapping_dir(tmp_path, ROWS, sk_rows=None)
    product = sk_twin(make_product())
    product["feeds"]["zbozi"]["category"] = "Stoly"
    result = run_mapped([product], mappings, side="sk")
    assert [f.property for f in result.findings] == ["feeds.zbozi.category"]
    assert "záloha" in result.findings[0].message
    sk_dir = tmp_path / "sk"
    sk_dir.mkdir()
    sk_mappings = _mapping_dir(sk_dir, ROWS, sk_rows={"Potahy": "SK potahy", "Stoly": "SK potahy"})
    assert run_mapped([product], sk_mappings, side="sk").findings == []


def test_feed_category_without_mapping_files(tmp_path):
    result = run_mapped([make_product()], CategoryMappings(str(tmp_path)))
    assert result.findings == [] and result.stats["no_mapping_file"] == 4


def test_feed_category_uses_project_memory_by_default():
    product = make_product()
    ctx = Context(cs_products=[product], sk_products=[], pairing=pair_products([product], []))
    result = run_check(CHECKS["shop_feed_category"], ctx)
    assert result.findings == [] and result.stats["checked"] == 4


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


def test_feed_category_ignores_empty_values_and_products_without_categories(tmp_path):
    mappings = _mapping_dir(tmp_path, ROWS)
    product = make_product()
    product["feeds"]["glami"]["category"] = ""
    assert run_mapped([product], mappings).stats["checked"] == 3
    assert run_mapped([make_product(feeds={})], mappings).stats["checked"] == 0
    assert run_mapped([make_product(categories=[])], mappings).findings == []


def test_load_mapping_edge_cases(tmp_path):
    assert load_mapping(str(tmp_path), "Zbozi", "CS") == ({}, "CategoryMappingZbozi_CS.csv")
    (tmp_path / "CategoryMappingZbozi_CS.csv").write_text("A;B\n1;2\n", encoding="utf-8")
    assert load_mapping(str(tmp_path), "Zbozi", "CS")[0] == {}
    (tmp_path / "CategoryMappingZbozi_CS.csv").write_text('"KEY","VALUE"\n" Potahy ","X"\n"",""\n', encoding="utf-8")
    assert load_mapping(str(tmp_path), "Zbozi", "CS")[0] == {"Potahy": "X"}
