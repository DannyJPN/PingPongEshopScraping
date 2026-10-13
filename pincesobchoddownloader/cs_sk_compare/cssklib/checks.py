"""
Registry of all CS vs SK checks.

Each check has its own script `check_<id>.py`; `check_all.py` runs any combination of them.
All checks return CheckResult objects that end up in the same report format.
"""
import logging
from dataclasses import dataclass, field
from typing import Callable, Optional

from cssklib.constants import SEVERITY_ERROR, SEVERITY_WARNING, SIDE_LABEL
from cssklib.images import sorted_images
from cssklib.pairing import format_variant_key, pair_variants, variant_code, variant_key
from cssklib.pricing import (
    PriceConfig, expected_sk_price, expected_standard_price, find_rule, within_tolerance,
)
from cssklib.report import CheckResult, Finding
from cssklib.shop_checks import shop_checks
from cssklib.values import (
    deep_diff, fold_text, get_brand, get_code, get_name, get_translation, image_path, is_active,
    normalize_value,
)

# Top-level product properties compared for equality (everything except the special ones below)
PRODUCT_FIELDS = [
    "guid", "ean", "mpn", "createdAt", "updatedAt", "priority", "archive", "visibility",
    "homepage", "sales", "deliveryFree", "erotic", "adult", "voucherDiscount", "purchasePrice",
    "deliveryDate", "deliveryDateAuto", "manageStock", "stockQuantity", "quantityPack",
    "limitMultiple", "limitMin", "limitMax", "weight", "length", "comment", "availability",
    "manufacturer", "guarantee", "discount", "tags", "related", "accessory", "gift", "pairs",
    "feeds", "videos", "files", "parameters", "categories", "warehouse", "wholesale",
]
TRANSLATION_FIELDS = ["nameext", "slug", "metaTitle", "metaDescription", "annotation", "description"]
# Properties with special rules / own checks (catalogNumber + name = identity)
SPECIAL_FIELDS = {"catalogNumber", "translations", "price", "standardPrice", "vat", "images", "variants"}
# Shop internal IDs of products and variants may legitimately differ between CZ and SK -> never compared
IGNORED_FIELDS = {"id"}

VARIANT_FIELDS = [
    "ean", "mpn", "equal", "purchasePrice", "deliveryDate", "deliveryDateAuto", "manageStock",
    "stockQuantity", "weight", "length", "image", "translations", "availability",
]
VARIANT_SPECIAL_FIELDS = {"catalogNumber", "options", "price", "standardPrice"}
VARIANT_IGNORED_FIELDS = {"id"}

PRICE_FIELD_LABEL = {"price": "cena bez DPH (price)", "standardPrice": "cena běžná s DPH (standardPrice)"}


@dataclass
class Context:
    cs_products: list
    sk_products: list
    pairing: object
    price_config: PriceConfig = field(default_factory=PriceConfig)
    active_only: bool = False
    shop_sides: tuple = ("cs", "sk")   # sides checked by single-shop checks
    category_mappings: object = None   # CategoryMappings (project memory files)
    image_store: object = None
    vision: dict = field(default_factory=dict)
    _variant_cache: dict = field(default_factory=dict)

    def side_products(self, side):
        products = self.cs_products if side == "cs" else self.sk_products
        return [p for p in products if is_active(p)] if self.active_only else products

    def variant_pairing(self, cs, sk):
        key = (id(cs), id(sk))
        if key not in self._variant_cache:
            self._variant_cache[key] = pair_variants(cs, sk)
        return self._variant_cache[key]


@dataclass
class Check:
    id: str
    title: str
    run: Callable
    group: str
    default_enabled: bool = True
    sides: Optional[tuple] = None   # sides needed; None = both


def _product_finding(check, prop, cs, sk, message, side="both", **kwargs):
    product = cs if cs is not None else sk
    product_side = "cs" if cs is not None else "sk"
    return Finding(check=check, property=prop, message=message,
                   product_code=get_code(product), product_name=get_name(product, product_side),
                   side=side, **kwargs)


def _difference_message(diffs):
    if len(diffs) == 1 and not diffs[0]["path"]:
        return "Hodnota se v CZ a SK liší"
    labels = [(d["path"] or "(celá hodnota)").replace("[]", "[položky seznamu]") for d in diffs[:10]]
    return "Liší se: " + ", ".join(labels) + (
        f" (+{len(diffs) - 10})" if len(diffs) > 10 else "")


def _compare(cs_raw, sk_raw):
    cs_value, sk_value = normalize_value(cs_raw), normalize_value(sk_raw)
    diffs = deep_diff(cs_value, sk_value)
    return cs_value, sk_value, diffs


# --- Generic property checks --------------------------------------------------

def make_field_check(prop, getter=None):
    getter = getter or (lambda product, side: product.get(prop))

    def run(ctx, check_id):
        result_findings = []
        for cs, sk in ctx.pairing.matched:
            cs_value, sk_value, diffs = _compare(getter(cs, "cs"), getter(sk, "sk"))
            if diffs:
                result_findings.append(_product_finding(
                    check_id, prop, cs, sk, _difference_message(diffs),
                    cs_value=cs_value, sk_value=sk_value,
                    details={"differences": diffs} if len(diffs) > 1 or diffs[0]["path"] else None))
        return result_findings, {"checked": len(ctx.pairing.matched)}
    return run


def run_other_fields(ctx, check_id):
    """Properties not covered by any other check (protects against new API fields)."""
    known = set(PRODUCT_FIELDS) | SPECIAL_FIELDS | IGNORED_FIELDS
    findings, fields = [], set()
    for cs, sk in ctx.pairing.matched:
        for prop in sorted((set(cs) | set(sk)) - known):
            fields.add(prop)
            cs_value, sk_value, diffs = _compare(cs.get(prop), sk.get(prop))
            if diffs:
                findings.append(_product_finding(check_id, prop, cs, sk, _difference_message(diffs),
                                                 cs_value=cs_value, sk_value=sk_value))
    return findings, {"checked": len(ctx.pairing.matched), "fields": ",".join(sorted(fields)) or "-"}


# --- Identity -----------------------------------------------------------------

def run_identity(ctx, check_id):
    findings = []
    for side, products in (("cs", ctx.pairing.cs_only), ("sk", ctx.pairing.sk_only)):
        other = SIDE_LABEL["sk" if side == "cs" else "cs"]
        for product in products:
            active = is_active(product)
            findings.append(Finding(
                check=check_id, property="catalogNumber+name", side=side,
                severity=SEVERITY_ERROR if active else SEVERITY_WARNING,
                product_code=get_code(product), product_name=get_name(product, side),
                message=f"Produkt (kód + název) existuje jen v {SIDE_LABEL[side]}, v {other} chybí"
                        + ("" if active else " (neaktivní)"),
                cs_value=get_name(product, side) if side == "cs" else None,
                sk_value=get_name(product, side) if side == "sk" else None))
    for cs, sk in ctx.pairing.name_conflicts:
        findings.append(_product_finding(
            check_id, "name", cs, sk, "Stejný kód, jiný název — nejde o stejný produkt",
            cs_value=get_name(cs, "cs"), sk_value=get_name(sk, "sk")))
    for side in ("cs", "sk"):
        for code in ctx.pairing.duplicates[side]:
            findings.append(Finding(check=check_id, property="catalogNumber", side=side,
                                    product_code=code, message=f"Kód je v {SIDE_LABEL[side]} vícekrát"))
    return findings, dict(ctx.pairing.summary())


# --- Prices -------------------------------------------------------------------

def _effective(variant, product, prop):
    value = variant.get(prop)
    return value if value is not None else product.get(prop)


def _conversion_finding(check_id, prop, cs, sk, cs_value, sk_value, rule, config, variant=None):
    if cs_value is None and sk_value is None:
        return None
    extra = {}
    if variant is not None:
        extra = {"variant_code": variant_code(variant[0]),
                 "variant_options": format_variant_key(variant[1])}
    if cs_value is None or sk_value is None:
        return _product_finding(check_id, prop, cs, sk, "Cena je vyplněna jen na jedné straně",
                                cs_value=cs_value, sk_value=sk_value, **extra)
    brand, _, discount = rule
    expected = expected_sk_price(cs_value, prop, discount, config)
    if within_tolerance(expected, sk_value, config):
        return None
    return _product_finding(
        check_id, prop, cs, sk,
        f"SK {PRICE_FIELD_LABEL[prop]} neodpovídá přepočtu CZ / {config.czk_per_eur:g} "
        f"- {discount * 100:g} % ({brand}); rozdíl {sk_value - expected:+.2f} EUR",
        cs_value=cs_value, sk_value=sk_value, expected=round(expected, 2),
        details={"brand": brand, "discount": discount, "tolerance": config.tolerance}, **extra)


def make_price_conversion_check(prop, variants=False):
    def run(ctx, check_id):
        config = ctx.price_config
        findings, stats = [], {"checked": 0, "not_applicable": 0}
        for cs, sk in ctx.pairing.matched:
            rule = find_rule(cs, config)
            if rule is None:
                stats["not_applicable"] += 1
                continue
            if not variants:
                stats["checked"] += 1
                finding = _conversion_finding(check_id, prop, cs, sk, cs.get(prop), sk.get(prop), rule, config)
                if finding:
                    findings.append(finding)
                continue
            for key, cs_var, sk_var in ctx.variant_pairing(cs, sk).matched:
                if cs_var.get(prop) is None and sk_var.get(prop) is None:
                    continue  # inherits the product price, covered by the product check
                stats["checked"] += 1
                finding = _conversion_finding(
                    check_id, prop, cs, sk, _effective(cs_var, cs, prop), _effective(sk_var, sk, prop),
                    rule, config, variant=(cs_var, key))
                if finding:
                    findings.append(finding)
        return findings, stats
    return run


def _vat_relation_finding(check_id, product, side, price, standard, config, variant=None):
    expected = expected_standard_price(price, side, config)
    if price is None or standard is None or within_tolerance(expected, standard, config):
        return None
    extra = {}
    if variant is not None:
        extra = {"variant_code": variant_code(variant), "variant_options": format_variant_key(variant_key(variant))}
    return Finding(
        check=check_id, property="standardPrice = price × (1 + DPH)", side=side,
        product_code=get_code(product), product_name=get_name(product, side),
        message=f"Cena běžná {standard:g} ≠ cena {price:g} × {config.vat_factor(side):g} "
                f"(DPH {config.vat_rates[side]:g} %, rozdíl {standard - expected:+.2f})",
        cs_value={"price": price, "standardPrice": standard} if side == "cs" else None,
        sk_value={"price": price, "standardPrice": standard} if side == "sk" else None,
        expected=round(expected, 2), **extra)


def make_vat_relation_check(variants=False):
    def run(ctx, check_id):
        config = ctx.price_config
        findings, stats = [], {"checked": 0}
        for side in ctx.shop_sides:
            for product in ctx.side_products(side):
                if not variants:
                    stats["checked"] += 1
                    finding = _vat_relation_finding(check_id, product, side, product.get("price"),
                                                    product.get("standardPrice"), config)
                    if finding:
                        findings.append(finding)
                    continue
                for variant in product.get("variants") or []:
                    if variant.get("price") is None and variant.get("standardPrice") is None:
                        continue
                    stats["checked"] += 1
                    finding = _vat_relation_finding(
                        check_id, product, side, _effective(variant, product, "price"),
                        _effective(variant, product, "standardPrice"), config, variant=variant)
                    if finding:
                        findings.append(finding)
        return findings, stats
    return run


def run_vat(ctx, check_id):
    """vat.rate must be the country VAT rate (CZ 21 %, SK 23 %) — values differ by design."""
    findings, stats = [], {"checked": 0}
    for side in ctx.shop_sides:
        expected = ctx.price_config.vat_rates[side]
        for product in ctx.side_products(side):
            stats["checked"] += 1
            rate = (product.get("vat") or {}).get("rate")
            if rate is None or abs(float(rate) - expected) > 1e-9:
                findings.append(Finding(
                    check=check_id, property="vat.rate", side=side,
                    product_code=get_code(product), product_name=get_name(product, side),
                    message=f"Sazba DPH v {SIDE_LABEL[side]} má být {expected:g} %",
                    cs_value=rate if side == "cs" else None, sk_value=rate if side == "sk" else None,
                    expected=expected))
    return findings, stats


# --- Variants -----------------------------------------------------------------

def run_variants(ctx, check_id):
    findings, stats = [], {"checked": 0, "matched_variants": 0}
    for cs, sk in ctx.pairing.matched:
        if not (cs.get("variants") or sk.get("variants")):
            continue
        stats["checked"] += 1
        vp = ctx.variant_pairing(cs, sk)
        stats["matched_variants"] += len(vp.matched)
        for key, cs_var, sk_var in vp.code_mismatch:
            findings.append(_product_finding(
                check_id, "variants.catalogNumber", cs, sk,
                "Varianta se stejnými parametry má v CZ a SK jiný kód",
                variant_code=variant_code(cs_var), variant_options=format_variant_key(key),
                cs_value=variant_code(cs_var), sk_value=variant_code(sk_var)))
        for cs_var, sk_var in vp.option_mismatch:
            findings.append(_product_finding(
                check_id, "variants.options", cs, sk, "Varianta se stejným kódem má v CZ a SK jiné parametry",
                variant_code=variant_code(cs_var),
                cs_value=format_variant_key(variant_key(cs_var)), sk_value=format_variant_key(variant_key(sk_var))))
        for side, items in (("cs", vp.cs_only), ("sk", vp.sk_only)):
            for key, variant in items:
                findings.append(_product_finding(
                    check_id, "variants", cs, sk,
                    f"Varianta existuje jen v {SIDE_LABEL[side]}", side=side,
                    variant_code=variant_code(variant), variant_options=format_variant_key(key),
                    cs_value=variant_code(variant) if side == "cs" else None,
                    sk_value=variant_code(variant) if side == "sk" else None))
        for side in ("cs", "sk"):
            for key in vp.duplicate_keys[side]:
                findings.append(_product_finding(
                    check_id, "variants.options", cs, sk,
                    f"V {SIDE_LABEL[side]} je více variant se stejnými parametry", side=side,
                    severity=SEVERITY_WARNING, variant_options=format_variant_key(key)))
    return findings, stats


def make_variant_field_check(prop):
    def run(ctx, check_id):
        findings, stats = [], {"checked": 0}
        for cs, sk in ctx.pairing.matched:
            for key, cs_var, sk_var in ctx.variant_pairing(cs, sk).matched:
                stats["checked"] += 1
                cs_value, sk_value, diffs = _compare(cs_var.get(prop), sk_var.get(prop))
                if diffs:
                    findings.append(_product_finding(
                        check_id, f"variants.{prop}", cs, sk, _difference_message(diffs),
                        variant_code=variant_code(cs_var), variant_options=format_variant_key(key),
                        cs_value=cs_value, sk_value=sk_value))
        return findings, stats
    return run


# --- Images -------------------------------------------------------------------

def run_images_path(ctx, check_id):
    findings, stats = [], {"checked": 0, "images_cs": 0, "images_sk": 0}
    for cs, sk in ctx.pairing.matched:
        stats["checked"] += 1
        cs_imgs, sk_imgs = sorted_images(cs), sorted_images(sk)
        stats["images_cs"] += len(cs_imgs)
        stats["images_sk"] += len(sk_imgs)
        cs_paths = [image_path(i.get("url")) for i in cs_imgs]
        sk_paths = [image_path(i.get("url")) for i in sk_imgs]
        if len(cs_paths) != len(sk_paths):
            findings.append(_product_finding(
                check_id, "images.count", cs, sk,
                f"Různý počet fotek: CZ {len(cs_paths)}, SK {len(sk_paths)}",
                cs_value=cs_paths, sk_value=sk_paths))
        for index in range(min(len(cs_paths), len(sk_paths))):
            if cs_paths[index] != sk_paths[index]:
                findings.append(_product_finding(
                    check_id, f"images[{index + 1}].path", cs, sk, f"Fotka č. {index + 1} má jinou cestu",
                    cs_value=cs_paths[index], sk_value=sk_paths[index]))
        cs_default = next((image_path(i.get("url")) for i in cs_imgs if i.get("default")), None)
        sk_default = next((image_path(i.get("url")) for i in sk_imgs if i.get("default")), None)
        first_reported = bool(cs_paths and sk_paths) and cs_paths[0] != sk_paths[0]
        if cs_default != sk_default and not (first_reported and cs_default == cs_paths[0]
                                             and sk_default == sk_paths[0]):
            findings.append(_product_finding(check_id, "images.default", cs, sk, "Jiná hlavní fotka",
                                             cs_value=cs_default, sk_value=sk_default))
    return findings, stats


def run_images_hash(ctx, check_id):
    if ctx.image_store is None:
        raise RuntimeError("Kontrola hashů fotek potřebuje úložiště obrázků (image_store)")
    pairs = []
    for cs, sk in ctx.pairing.matched:
        cs_imgs, sk_imgs = sorted_images(cs), sorted_images(sk)
        for index in range(min(len(cs_imgs), len(sk_imgs))):
            pairs.append((cs, sk, index, cs_imgs[index].get("url"), sk_imgs[index].get("url")))
    urls = [u for pair in pairs for u in pair[3:]]
    total = len(set(u for u in urls if u))
    done = {"n": 0}

    def progress(_url):
        done["n"] += 1
        if done["n"] % 500 == 0 or done["n"] == total:
            logging.info(f"Hash fotek: {done['n']}/{total}")

    hashes = ctx.image_store.hash_many(urls, progress=progress)
    findings, stats = [], {"checked": len(pairs), "downloaded_or_cached": sum(1 for h in hashes.values() if h),
                           "failed": sum(1 for h in hashes.values() if not h)}
    for cs, sk, index, cs_url, sk_url in pairs:
        cs_hash, sk_hash = hashes.get(cs_url), hashes.get(sk_url)
        prop = f"images[{index + 1}].sha256"
        if cs_hash is None or sk_hash is None:
            findings.append(_product_finding(
                check_id, prop, cs, sk, "Fotku se nepodařilo stáhnout, hash nelze porovnat",
                severity=SEVERITY_WARNING, cs_value=cs_hash or cs_url, sk_value=sk_hash or sk_url))
        elif cs_hash != sk_hash:
            findings.append(_product_finding(
                check_id, prop, cs, sk, f"Fotka č. {index + 1} má v CZ a SK jiný obsah (hash)",
                cs_value=cs_hash, sk_value=sk_hash,
                details={"cs_url": cs_url, "sk_url": sk_url,
                         "same_path": image_path(cs_url) == image_path(sk_url)}))
    return findings, stats


# --- OpenAI vision --------------------------------------------------------------

def select_vision_products(ctx):
    options = ctx.vision
    sides = ("cs", "sk") if options.get("side", "cs") == "both" else (options.get("side", "cs"),)
    codes = {c.strip() for c in options.get("codes") or [] if c.strip()}
    brands = {fold_text(b) for b in options.get("brands") or []}
    selected = []
    for side in sides:
        products = ctx.cs_products if side == "cs" else ctx.sk_products
        for product in products:
            if codes and get_code(product) not in codes:
                continue
            if brands and fold_text(get_brand(product)) not in brands:
                continue
            if (options.get("active_only") or ctx.active_only) and not is_active(product):
                continue
            if not product.get("images"):
                continue
            selected.append((side, product))
    limit = options.get("limit") or 0
    return selected[:limit] if limit else selected


def run_vision(ctx, check_id):
    from cssklib.vision import VERDICT_UNCLEAR, VERDICT_UNRELATED, VERDICTS, VisionCache
    checker = ctx.vision.get("checker")
    if checker is None:
        raise RuntimeError("Vizuální kontrola potřebuje VisionChecker (ctx.vision['checker'])")
    selected = select_vision_products(ctx)
    stats = {"checked": len(selected), **{v: 0 for v in VERDICTS}, "errors": 0}
    findings = []
    if ctx.vision.get("dry_run"):
        pending = 0
        for side, product in selected:
            images = sorted_images(product)
            if checker.max_images:
                images = images[:checker.max_images]
            for image in images:
                key = VisionCache.key(checker.model, get_code(product), get_name(product, side), image.get("url"))
                pending += checker.refresh or checker.cache.get(key) is None
        return [], {"checked": len(selected), "dry_run": True, "images_to_send": pending, "model": checker.model}

    for number, (side, product) in enumerate(selected, start=1):
        try:
            results = checker.check_product(product, side)
        except Exception as exc:
            stats["errors"] += 1
            findings.append(Finding(check=check_id, property="images.vision", side=side,
                                    severity=SEVERITY_WARNING, product_code=get_code(product),
                                    product_name=get_name(product, side),
                                    message=f"Vizuální kontrola selhala: {exc}"))
            continue
        for item in results:
            stats[item["verdict"]] += 1
            if item["verdict"] not in (VERDICT_UNRELATED, VERDICT_UNCLEAR):
                continue
            unrelated = item["verdict"] == VERDICT_UNRELATED
            findings.append(Finding(
                check=check_id, property=f"images[{item['index']}].vision", side=side,
                severity=SEVERITY_ERROR if unrelated else SEVERITY_WARNING,
                product_code=get_code(product), product_name=get_name(product, side),
                message=("Fotka nezobrazuje produkt ani s ním nesouvisí" if unrelated
                         else "Nelze rozhodnout, zda fotka patří k produktu") + f": {item['reason']}",
                cs_value=item["url"] if side == "cs" else None,
                sk_value=item["url"] if side == "sk" else None,
                details={"verdict": item["verdict"], "cached": item["cached"]}))
        if number % 25 == 0:
            logging.info(f"Vision: {number}/{len(selected)} produktů")
    stats.update({"model": checker.model, **{f"usage_{k}": v for k, v in checker.usage.items()}})
    return findings, stats


# --- Registry -----------------------------------------------------------------

def _build_registry():
    checks = [Check("identity", "Identita produktu (kód + název): chybějící / konfliktní produkty",
                    run_identity, "identity")]
    for prop in PRODUCT_FIELDS:
        checks.append(Check(prop, f"Vlastnost produktu '{prop}'", make_field_check(prop), "product"))
    for prop in TRANSLATION_FIELDS:
        checks.append(Check(f"translations_{prop}", f"Překlad '{prop}' (translations.*.{prop})",
                            make_field_check(prop, lambda p, side, f=prop: get_translation(p, f, side)),
                            "product"))
    checks.append(Check("other_fields", "Ostatní (neznámé) vlastnosti produktu", run_other_fields, "product"))
    checks += [
        Check("vat", "Sazba DPH (CZ 21 %, SK 23 %)", run_vat, "shop"),
        Check("price", "Cena bez DPH: přepočet CZ → SK dle značky", make_price_conversion_check("price"), "price"),
        Check("standardPrice", "Cena běžná: přepočet CZ → SK dle značky",
              make_price_conversion_check("standardPrice"), "price"),
        Check("price_vat", "Cena běžná = cena × (1 + DPH) v CZ i SK", make_vat_relation_check(), "shop"),
        Check("variants", "Varianty: identita (kód + parametry)", run_variants, "variant"),
    ]
    checks += shop_checks(Check)
    for prop in VARIANT_FIELDS:
        checks.append(Check(f"variant_{prop}", f"Vlastnost varianty '{prop}'", make_variant_field_check(prop),
                            "variant"))
    checks += [
        Check("variant_price", "Cena varianty bez DPH: přepočet CZ → SK",
              make_price_conversion_check("price", variants=True), "variant"),
        Check("variant_standardPrice", "Cena běžná varianty: přepočet CZ → SK",
              make_price_conversion_check("standardPrice", variants=True), "variant"),
        Check("variant_price_vat", "Cena běžná varianty = cena × (1 + DPH)",
              make_vat_relation_check(variants=True), "shop"),
        Check("images_path", "Fotky: počet, pořadí a cesty", run_images_path, "images"),
        Check("images_hash", "Fotky: shoda obsahu (SHA-256 hash)", run_images_hash, "images"),
        Check("vision", "Fotky: OpenAI vizuální kontrola, zda zobrazují produkt (drahé)", run_vision,
              "vision", default_enabled=False),
    ]
    return {check.id: check for check in checks}


CHECKS = _build_registry()


def run_check(check, ctx):
    findings, stats = check.run(ctx, check.id)
    return CheckResult(check=check.id, title=check.title, findings=findings, stats=stats)


