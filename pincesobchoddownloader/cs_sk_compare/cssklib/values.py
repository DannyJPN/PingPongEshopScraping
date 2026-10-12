"""Value normalization, product accessors and deep comparison helpers."""
import json
import unicodedata
from urllib.parse import urlsplit

from cssklib.constants import SHOP_DOMAINS


def normalize_text(text):
    """Collapse whitespace and strip; None stays None."""
    if text is None:
        return None
    return " ".join(str(text).split())


def fold_text(text):
    """Lowercase text without diacritics (used for brand / category rule matching)."""
    text = normalize_text(text) or ""
    text = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def strip_shop_domain(value):
    """Return URL path for pincesobchod URLs so CZ and SK URLs are comparable."""
    if not isinstance(value, str):
        return value
    for domain in SHOP_DOMAINS:
        if value.startswith(domain):
            return value[len(domain):] or "/"
    return value


def image_path(url):
    """Path part of an image URL (domain independent)."""
    if not url:
        return None
    stripped = strip_shop_domain(url)
    if stripped != url:
        return stripped
    return urlsplit(url).path or url


def canonical(value):
    """Stable JSON representation used for sorting and set comparison."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def normalize_value(value):
    """
    Normalize a JSON value for CS/SK comparison.

    - empty string / empty list / empty dict -> None
    - strings: whitespace collapsed, shop domain stripped from URLs
    - whole floats -> int (320.0 == 320)
    - lists are order-insensitive (sorted by canonical JSON)
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        text = normalize_text(strip_shop_domain(value))
        return text or None
    if isinstance(value, dict):
        result = {k: normalize_value(v) for k, v in value.items()}
        return result if any(v is not None for v in result.values()) else None
    if isinstance(value, (list, tuple)):
        items = [normalize_value(v) for v in value]
        items = [v for v in items if v is not None]
        if not items:
            return None
        return sorted(items, key=canonical)
    return value


def deep_diff(cs_value, sk_value, path=""):
    """
    Compare two normalized values; return list of {'path', 'cs', 'sk'}.

    Dicts are compared key by key, lists as multisets (items only on one side are reported).
    """
    if cs_value == sk_value:
        return []
    if isinstance(cs_value, dict) and isinstance(sk_value, dict):
        diffs = []
        for key in sorted(set(cs_value) | set(sk_value), key=str):
            sub = f"{path}.{key}" if path else str(key)
            diffs.extend(deep_diff(cs_value.get(key), sk_value.get(key), sub))
        return diffs
    if isinstance(cs_value, list) and isinstance(sk_value, list):
        cs_keys = [canonical(v) for v in cs_value]
        sk_keys = [canonical(v) for v in sk_value]
        cs_only = [v for v, k in zip(cs_value, cs_keys) if k not in sk_keys]
        sk_only = [v for v, k in zip(sk_value, sk_keys) if k not in cs_keys]
        if not cs_only and not sk_only:
            # Same items, different multiplicity
            return [{"path": path or "", "cs": cs_value, "sk": sk_value}]
        return [{"path": f"{path}[]" if path else "[]", "cs": cs_only or None, "sk": sk_only or None}]
    return [{"path": path, "cs": cs_value, "sk": sk_value}]


# --- Product accessors -------------------------------------------------------

def get_translation(product, field, side):
    """Translation field; tries the side language first, then 'cs', then any language."""
    translations = (product or {}).get("translations") or {}
    for lang in (side, "cs"):
        value = (translations.get(lang) or {}).get(field)
        if value is not None:
            return value
    for data in translations.values():
        if isinstance(data, dict) and data.get(field) is not None:
            return data.get(field)
    return None


def get_name(product, side="cs"):
    return normalize_text(get_translation(product, "name", side)) or ""


def get_code(product):
    return normalize_text((product or {}).get("catalogNumber")) or ""


def get_brand(product):
    return ((product or {}).get("manufacturer") or {}).get("name")


def get_root_categories(product):
    """Folded names of root categories; main category first, all categories as fallback."""
    categories = (product or {}).get("categories") or []
    main = [c for c in categories if c.get("main")]
    roots = []
    for category in (main or categories):
        path = category.get("path") or {}
        if path:
            roots.append(fold_text(next(iter(path.values()))))
    return roots


def is_active(product):
    return bool(product.get("visibility")) and not bool(product.get("archive"))


def short(value, limit=120):
    """Short human readable representation of a value."""
    if value is None:
        return "∅"
    text = value if isinstance(value, str) else canonical(value)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit - 1] + "…"
