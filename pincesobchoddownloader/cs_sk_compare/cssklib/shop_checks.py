"""
Single-shop consistency checks (run separately for the CZ and the SK JSON).

Rules (verified on real exports, ~90-100 % of products follow them):
  * product name is copied to the SEO title (translations.metaTitle) and to the
    Heureka / Zboží product titles (feeds.heurekacs|zbozi.productname|product)
  * meta description = annotation
  * slug = slugified product name
  * feed categories map (project mapping desaka_unifier/Memory/CategoryMapping<Platform>_<LANG>.csv)
    to the same platform category as the product's own categories
  * all feeds use the same CPC
  * exactly one main image, it is the first one, positions are 1..n, no duplicates
  * variant code = <product code>-<suffix>, variant codes are unique in the shop
  * the manufacturer name is part of the product name
  * descriptions contain no hyperlinks except links to another product of the same shop
  * category mapping files are compared with the JSON and with each other (file against file)
"""
import re
import unicodedata
from collections import Counter
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

from cssklib.category_mapping import FEED_PLATFORMS, CategoryMappings
from cssklib.constants import SEVERITY_ERROR, SEVERITY_WARNING, SIDE_LANG
from cssklib.images import sorted_images
from cssklib.pairing import variant_code
from cssklib.report import Finding
from cssklib.values import fold_text, get_brand, get_code, get_name, get_translation, image_path, normalize_text

# Feed titles the product name must be copied to: (feed, field)
FEED_NAME_TARGETS = [
    ("heurekacs", "productname"),
    ("heurekacs", "product"),
    ("zbozi", "productname"),
    ("zbozi", "product"),
]
FEED_CPC_FIELDS = (("glami", "cpc"), ("heurekacs", "cpc"), ("zbozi", "cpc"), ("zbozi", "cpc_search"),
                   ("shopalikecs", "cpc"))


def slugify(text):
    text = unicodedata.normalize("NFD", (text or "").lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def _finding(check_id, product, side, prop, message, value=None, expected=None,
             severity=SEVERITY_ERROR, **extra):
    return Finding(check=check_id, property=prop, message=message, side=side, severity=severity,
                   product_code=get_code(product), product_name=get_name(product, side),
                   cs_value=value if side == "cs" else None, sk_value=value if side == "sk" else None,
                   expected=expected, **extra)


def _iter_products(ctx):
    for side in ctx.shop_sides:
        for product in ctx.side_products(side):
            yield side, product


def _feed(product, key):
    return ((product.get("feeds") or {}).get(key)) or {}


# --- Name copies ------------------------------------------------------------------

def make_name_copy_check(prop, getter, label):
    """The product name must be copied exactly (whitespace-insensitive) to `prop`."""
    def run(ctx, check_id):
        findings, stats = [], {"checked": 0, "empty": 0}
        for side, product in _iter_products(ctx):
            stats["checked"] += 1
            name = get_name(product, side)
            value = normalize_text(getter(product, side))
            if value == name:
                continue
            if not value:
                stats["empty"] += 1
                findings.append(_finding(check_id, product, side, prop, f"{label} je prázdný, má obsahovat název produktu",
                                         value=value, expected=name, severity=SEVERITY_WARNING))
                continue
            meta_title = normalize_text(get_translation(product, "metaTitle", side))
            hint = " (obsahuje starý SEO titulek)" if prop != "translations.metaTitle" and value == meta_title else ""
            findings.append(_finding(check_id, product, side, prop,
                                     f"{label} neodpovídá názvu produktu{hint}", value=value, expected=name))
        return findings, stats
    return run


def run_meta_description(ctx, check_id):
    findings, stats = [], {"checked": 0}
    for side, product in _iter_products(ctx):
        stats["checked"] += 1
        annotation = normalize_text(get_translation(product, "annotation", side))
        description = normalize_text(get_translation(product, "metaDescription", side))
        if annotation != description:
            findings.append(_finding(check_id, product, side, "translations.metaDescription",
                                     "SEO popis (metaDescription) neodpovídá anotaci", value=description,
                                     expected=annotation))
    return findings, stats


def run_slug(ctx, check_id):
    findings, stats = [], {"checked": 0}
    for side, product in _iter_products(ctx):
        stats["checked"] += 1
        expected = slugify(get_name(product, side))
        slug = get_translation(product, "slug", side)
        if slug != expected:
            findings.append(_finding(check_id, product, side, "translations.slug",
                                     "URL (slug) neodpovídá názvu produktu", value=slug, expected=expected))
    return findings, stats


# --- Feeds ------------------------------------------------------------------------

def _category_paths(product):
    return [">".join((c.get("path") or {}).values()) for c in product.get("categories") or [] if c.get("path")]


def run_feed_categories(ctx, check_id):
    """
    The e-shop category stored in each feed (feeds.<feed>.category, e.g. "Potahy>Softy") is mapped
    to the platform category by the project mapping. It has to map to the same platform category
    as (at least one of) the product's own categories.
    """
    mappings = ctx.category_mappings or CategoryMappings()
    findings, stats = [], {"checked": 0, "no_mapping_file": 0}
    used_files = set()
    for side, product in _iter_products(ctx):
        paths = _category_paths(product)
        unmapped = {}   # product category path -> mapping files without it
        for feed_key, platform in FEED_PLATFORMS.items():
            feed_category = normalize_text(_feed(product, feed_key).get("category"))
            if not feed_category:
                continue
            mapping, file_name = mappings.get(platform, SIDE_LANG[side])
            if not mapping:
                stats["no_mapping_file"] += 1
                continue
            used_files.add(file_name)
            stats["checked"] += 1
            prop = f"feeds.{feed_key}.category"
            if feed_category not in mapping:
                findings.append(_finding(check_id, product, side, prop,
                                         f"Rozpor JSON ↔ {file_name}: kategorie z feedu v souboru chybí",
                                         value=feed_category, details={"mapping_file": file_name}))
                continue
            for path in paths:
                if path not in mapping:
                    unmapped.setdefault(path, []).append(file_name)
            expected = sorted({mapping[path] for path in paths if path in mapping})
            if expected and mapping[feed_category] not in expected:
                findings.append(_finding(
                    check_id, product, side, prop,
                    f"Rozpor JSON ↔ {file_name}: kategorie ve feedu '{feed_category}' a kategorie produktu "
                    "se mapují na různé kategorie srovnávače",
                    value=mapping[feed_category], expected=expected[0] if len(expected) == 1 else expected,
                    details={"feed_category": feed_category, "product_categories": paths,
                             "mapping_file": file_name}))
        for path, files in unmapped.items():
            findings.append(_finding(check_id, product, side, "categories",
                                     "Rozpor JSON ↔ " + ", ".join(files) + ": kategorie produktu v souboru chybí",
                                     value=path, severity=SEVERITY_WARNING))
    stats["mapping_files"] = ", ".join(sorted(used_files)) or "-"
    return findings, stats


def run_feed_cpc(ctx, check_id):
    findings, stats = [], {"checked": 0}
    for side, product in _iter_products(ctx):
        values = {f"{feed}.{field}": _feed(product, feed).get(field)
                  for feed, field in FEED_CPC_FIELDS if _feed(product, feed).get(field) not in (None, "")}
        if not values:
            continue
        stats["checked"] += 1
        numbers = set()
        for value in values.values():
            try:
                numbers.add(round(float(value), 2))
            except (TypeError, ValueError):
                numbers.add(str(value))
        if len(numbers) > 1:
            common = Counter(values.values()).most_common(1)[0][0]
            findings.append(_finding(check_id, product, side, "feeds.*.cpc",
                                     "CPC se mezi feedy liší", value=values, expected=common,
                                     severity=SEVERITY_WARNING))
    return findings, stats


# --- Images -----------------------------------------------------------------------

def run_images_structure(ctx, check_id):
    findings, stats = [], {"checked": 0}
    for side, product in _iter_products(ctx):
        images = sorted_images(product)
        if not images:
            continue
        stats["checked"] += 1
        defaults = [i for i in images if i.get("default")]
        if len(defaults) != 1:
            findings.append(_finding(check_id, product, side, "images.default",
                                     f"Produkt má {len(defaults)} hlavních fotek (má mít právě 1)",
                                     value=[image_path(i.get("url")) for i in defaults]))
        elif not images[0].get("default"):
            findings.append(_finding(check_id, product, side, "images.default",
                                     "Hlavní fotka není na první pozici", severity=SEVERITY_WARNING,
                                     value=image_path(defaults[0].get("url")),
                                     expected=image_path(images[0].get("url"))))
        positions = [i.get("position") for i in images]
        if positions != list(range(1, len(images) + 1)):
            findings.append(_finding(check_id, product, side, "images.position",
                                     "Pozice fotek nejdou po sobě od 1", severity=SEVERITY_WARNING,
                                     value=positions, expected=list(range(1, len(images) + 1))))
        paths = [image_path(i.get("url")) for i in images]
        duplicates = sorted(p for p, n in Counter(paths).items() if n > 1)
        if duplicates:
            findings.append(_finding(check_id, product, side, "images.url",
                                     "Stejná fotka je u produktu vícekrát", value=duplicates))
    return findings, stats


# --- Codes, brand -----------------------------------------------------

def run_variant_codes(ctx, check_id):
    findings, stats = [], {"checked": 0}
    for side in ctx.shop_sides:
        seen = {}
        for product in ctx.side_products(side):
            code = get_code(product)
            for variant in product.get("variants") or []:
                stats["checked"] += 1
                vcode = variant_code(variant)
                if not vcode.startswith(code + "-"):
                    findings.append(_finding(check_id, product, side, "variants.catalogNumber",
                                             f"Kód varianty nezačíná kódem produktu '{code}-'",
                                             value=vcode, variant_code=vcode))
                if vcode in seen and seen[vcode] != code:
                    findings.append(_finding(check_id, product, side, "variants.catalogNumber",
                                             f"Kód varianty je použit i u produktu {seen[vcode]}",
                                             value=vcode, variant_code=vcode))
                elif vcode in seen:
                    findings.append(_finding(check_id, product, side, "variants.catalogNumber",
                                             "Kód varianty je u produktu vícekrát", value=vcode, variant_code=vcode))
                seen.setdefault(vcode, code)
    return findings, stats


def run_brand_in_name(ctx, check_id):
    findings, stats = [], {"checked": 0}
    for side, product in _iter_products(ctx):
        brand = get_brand(product)
        if not brand:
            stats["checked"] += 1
            findings.append(_finding(check_id, product, side, "manufacturer",
                                     "Produkt nemá vyplněného výrobce", severity=SEVERITY_WARNING))
            continue
        stats["checked"] += 1
        if fold_text(brand) not in fold_text(get_name(product, side)):
            findings.append(_finding(check_id, product, side, "manufacturer.name",
                                     f"Název produktu neobsahuje značku '{brand}'", severity=SEVERITY_WARNING,
                                     value=get_name(product, side), expected=brand))
    return findings, stats


# --- Category mapping files ---------------------------------------------------------

def _file_finding(check_id, side, file_name, message, value=None, severity=SEVERITY_ERROR, details=None):
    return Finding(check=check_id, property=file_name, message=message, side=side, severity=severity,
                   cs_value=value if side == "cs" else None, sk_value=value if side == "sk" else None,
                   details=details)


def run_category_mapping_files(ctx, check_id):
    """
    File against file: e-shop categories used in the JSON <-> keys of every mapping file, and the
    mapping files of all platforms against each other (none of the files is assumed to be correct).
    """
    mappings = ctx.category_mappings or CategoryMappings()
    findings, stats = [], {"checked": 0}
    for side in ctx.shop_sides:
        json_categories = set()
        for product in ctx.side_products(side):
            json_categories.update(_category_paths(product))
            json_categories.update(normalize_text(_feed(product, k).get("category")) for k in FEED_PLATFORMS)
        json_categories.discard(None)
        json_categories.discard("")
        files = {}
        for platform in FEED_PLATFORMS.values():
            mapping, file_name = mappings.get(platform, SIDE_LANG[side])
            if not mapping:
                findings.append(_file_finding(check_id, side, file_name, "Mapovací soubor chybí nebo je prázdný",
                                              severity=SEVERITY_WARNING))
                continue
            files[file_name] = mapping
            stats["checked"] += 1
            json_label = f"JSON {SIDE_LANG[side]}"
            for category in sorted(json_categories - set(mapping)):
                findings.append(_file_finding(check_id, side, file_name,
                                              f"Rozpor {json_label} ↔ {file_name}: kategorie z JSONu v souboru chybí",
                                              value=category))
            for key in sorted(set(mapping) - json_categories):
                findings.append(_file_finding(check_id, side, file_name,
                                              f"Rozpor {json_label} ↔ {file_name}: kategorie ze souboru se v JSONu "
                                              "nevyskytuje", value=key, severity=SEVERITY_WARNING))
            for key in sorted(k for k, v in mapping.items() if not v):
                findings.append(_file_finding(check_id, side, file_name, "Kategorie nemá v souboru hodnotu",
                                              value=key))
        names = sorted(files)
        for index, first in enumerate(names):
            for second in names[index + 1:]:
                for key in sorted(set(files[first]) ^ set(files[second])):
                    present, missing = (first, second) if key in files[first] else (second, first)
                    findings.append(_file_finding(
                        check_id, side, missing, f"Rozpor {present} ↔ {missing}: kategorie v souboru chybí",
                        value=key, details={"present_in": present, "missing_in": missing}))
    return findings, stats


# --- Hyperlinks in descriptions -----------------------------------------------------

DESCRIPTION_FIELDS = ("description", "annotation", "metaDescription")
SHOP_HOSTS = {"cs": ("www.pincesobchod.cz", "pincesobchod.cz"), "sk": ("www.pincesobchod.sk", "pincesobchod.sk")}
BARE_URL_RE = re.compile(r"(?:https?://|www\.)[^\s\"'<>]+", re.IGNORECASE)


class _LinkParser(HTMLParser):
    """Collects <a href> targets and URLs written as plain text."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.text_urls = []
        self._in_link = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            self._in_link += 1
            href = dict(attrs).get("href")
            self.links.append(href if href is not None else "")

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._in_link:
            self._in_link -= 1

    def handle_data(self, data):
        if not self._in_link:
            self.text_urls.extend(BARE_URL_RE.findall(data))


def extract_links(html):
    parser = _LinkParser()
    parser.feed(html or "")
    parser.close()
    return parser.links, parser.text_urls


def classify_link(href, side, product_slugs):
    """Return None for an allowed link (product of the same shop), otherwise the reason."""
    href = (href or "").strip()
    if not href:
        return "Odkaz bez cíle (prázdný href)"
    parts = urlsplit(href)
    if parts.scheme and parts.scheme.lower() not in ("http", "https"):
        return f"Odkaz typu '{parts.scheme}:' není povolen"
    if parts.netloc and parts.netloc.lower() not in SHOP_HOSTS[side]:
        return "Odkaz mimo e-shop"
    if not parts.netloc and not href.startswith("/"):
        return "Odkaz není na produkt e-shopu"
    if parts.query:
        return "Odkaz na stránku e-shopu, která není produktem"
    path = unquote(parts.path).strip("/")
    if "/" in path or path not in product_slugs:
        return "Odkaz na stránku e-shopu, která není produktem" if "/" in path or not path \
            else "Odkaz na neexistující produkt e-shopu"
    return None


def run_description_links(ctx, check_id):
    """Descriptions must not contain hyperlinks, except links to another product of the same shop."""
    findings, stats = [], {"checked": 0, "links": 0, "allowed_links": 0}
    for side in ctx.shop_sides:
        products = ctx.side_products(side)
        slugs = {get_translation(p, "slug", side) for p in (ctx.cs_products if side == "cs" else ctx.sk_products)}
        slugs.discard(None)
        for product in products:
            own_slug = get_translation(product, "slug", side)
            for field in DESCRIPTION_FIELDS:
                html = get_translation(product, field, side)
                if not html:
                    continue
                stats["checked"] += 1
                links, text_urls = extract_links(html)
                prop = f"translations.{field}"
                for href in links:
                    stats["links"] += 1
                    reason = classify_link(href, side, slugs)
                    if reason is None and unquote(urlsplit(href).path).strip("/") == own_slug:
                        reason = "Odkaz na sebe sama (ne na jiný produkt)"
                    if reason is None:
                        stats["allowed_links"] += 1
                        continue
                    findings.append(_finding(check_id, product, side, prop, reason, value=href))
                for url in text_urls:
                    findings.append(_finding(check_id, product, side, prop, "Adresa URL v textu popisu", value=url))
    return findings, stats


def shop_checks(check_cls):
    """Check definitions of the single-shop group (registered in checks.CHECKS)."""
    checks = [
        check_cls("shop_name_metaTitle", "Jeden e-shop: název produktu = SEO titulek (metaTitle)",
                  make_name_copy_check("translations.metaTitle",
                                       lambda p, side: get_translation(p, "metaTitle", side), "SEO titulek"),
                  "shop"),
    ]
    for feed, field in FEED_NAME_TARGETS:
        label = f"{'Heureka' if feed.startswith('heureka') else 'Zboží'} {field}"
        checks.append(check_cls(
            f"shop_name_{feed}_{field}", f"Jeden e-shop: název produktu = feeds.{feed}.{field} ({label})",
            make_name_copy_check(f"feeds.{feed}.{field}",
                                 lambda p, side, f=feed, k=field: _feed(p, f).get(k), f"Titulek {label}"),
            "shop"))
    checks += [
        check_cls("shop_metaDescription", "Jeden e-shop: SEO popis (metaDescription) = anotace",
                  run_meta_description, "shop"),
        check_cls("shop_slug", "Jeden e-shop: URL (slug) odpovídá názvu", run_slug, "shop"),
        check_cls("shop_feed_category", "Jeden e-shop: kategorie ve feedech dle mapování kategorií projektu",
                  run_feed_categories, "shop"),
        check_cls("shop_category_mapping_files",
                  "Jeden e-shop: mapovací soubory kategorií proti JSONu a proti sobě navzájem",
                  run_category_mapping_files, "shop"),
        check_cls("shop_description_links",
                  "Jeden e-shop: popisy bez odkazů (povolen jen odkaz na jiný produkt téhož e-shopu)",
                  run_description_links, "shop"),
        check_cls("shop_feed_cpc", "Jeden e-shop: stejné CPC ve všech feedech", run_feed_cpc, "shop"),
        check_cls("shop_images", "Jeden e-shop: jedna hlavní fotka na 1. pozici, pozice 1..n, bez duplicit",
                  run_images_structure, "shop"),
        check_cls("shop_variant_codes", "Jeden e-shop: kód varianty = kód produktu-NN, unikátní",
                  run_variant_codes, "shop"),
        check_cls("shop_brand_in_name", "Jeden e-shop: název obsahuje značku výrobce", run_brand_in_name, "shop"),
    ]
    return checks
