"""
Navrhne nové správné catalogNumber pro produkty, jejichž kód:
  - neodpovídá kategorii produktu, nebo
  - je duplicitní (sdílen dvěma produkty).
Ignoruje visibility a archive — kódy platí pro všechny produkty.
"""
import csv
import json
import os
import re
import sys
import io
from collections import defaultdict
from datetime import datetime

from compare_utils import load_latest_json, get_name, is_active
from compare_categories import (
    load_brand_codes, load_category_codes, load_subcategory_codes,
    check_categories, check_duplicate_codes,
    parse_catalog_number, get_actual_category_names, SUBCODED_CATEGORIES,
)

DEFAULT_CS_DIR  = "F:/Dropbox/DesakaPrivate/PingPongEshopScraping/Desaka/Pincesobchod_CS"
DEFAULT_OUT_DIR = "F:/Dropbox/DesakaPrivate/PingPongEshopScraping/Desaka/Reports/Pincesobchod"


# ── helpers ──────────────────────────────────────────────────────────

def build_reverse(d):
    """Invert a {name: code} dict to {code: name}; also return {name: code}."""
    return {v: k for k, v in d.items()}


def get_semantic_cat_code(product):
    """
    Determine correct category code from product name when website category may be wrong.
    Rule: 'X na míčky' → Míčky (03), EXCEPT 'pouzdro na pálku s kapsou na míčky' → Pouzdra (11).
    Returns cat_code string or None.
    """
    name = get_name(product).lower()
    if re.search(r'na\s+míčk', name) and not re.search(r'na\s+pálk', name):
        return '03'
    return None


def get_leaf_category(product):
    """Return the most specific (leaf) category name — from the deepest path."""
    best_path = {}
    for cat in (product.get('categories') or []):
        path = cat.get('path') or {}
        if len(path) > len(best_path):
            best_path = path
    return list(best_path.values())[-1] if best_path else ''


def resolve_correct_code_parts(product, category_codes, subcategory_codes,
                                brand_code_str):
    """
    Given a product and its brand code string (e.g. 'JOO'), return
    (brand, correct_cat_code, correct_sub_code) or None if undeterminable.
    """
    # Reverse maps: name → code
    cat_name_to_code = {v: k for k, v in category_codes.items()}
    sub_name_to_code = {}
    for subcode, names in subcategory_codes.items():
        for n in names:
            sub_name_to_code[n] = subcode

    leaf = get_leaf_category(product)
    all_cats = get_actual_category_names(product)

    # Semantic override: determine category from product name first
    # (more reliable than website category for accessories)
    cat_code = get_semantic_cat_code(product)

    if cat_code is None:
        # Fall back to website category
        for name in [leaf] + sorted(all_cats):
            if name in cat_name_to_code:
                cat_code = cat_name_to_code[name]
                break
            if name in sub_name_to_code:
                cat_code = '05'
                break

    if cat_code is None:
        return None

    # Determine sub_code
    if cat_code in SUBCODED_CATEGORIES:
        sub_code = sub_name_to_code.get(leaf, '00')
    else:
        sub_code = '00'

    return brand_code_str, cat_code, sub_code


def find_next_code(brand, cat_code, sub_code, all_codes, reserved):
    """Return the next unused catalogNumber for this brand+cat+sub prefix."""
    prefix = f"{brand}{cat_code}{sub_code}"
    existing = set()
    for code in all_codes:
        if re.match(rf'^{re.escape(prefix)}\d{{4}}$', code):
            existing.add(code)
    existing |= reserved
    seq = 1
    while True:
        candidate = f"{prefix}{seq:04d}"
        if candidate not in existing:
            return candidate
        seq += 1


# ── main ─────────────────────────────────────────────────────────────

def build_corrections(cs_products, brand_codes, category_codes, subcategory_codes):
    all_codes = {p['catalogNumber'] for p in cs_products if p.get('catalogNumber')}
    reserved  = set()

    corrections   = []   # code needs changing
    website_fixes = []   # code is correct, website category is wrong

    # ── 1. Category mismatches ────────────────────────────────────────
    r_cat = check_categories(cs_products, brand_codes, category_codes, subcategory_codes)
    mismatch_codes = {r['catalogNumber'] for r in r_cat['mismatches']}

    for r in r_cat['mismatches']:
        cat_num   = r['catalogNumber']
        product   = next(p for p in cs_products if p.get('catalogNumber') == cat_num)
        brand_code_str, current_cat, current_sub = parse_catalog_number(cat_num, brand_codes)
        if brand_code_str is None:
            continue

        parts = resolve_correct_code_parts(
            product, category_codes, subcategory_codes, brand_code_str)
        if parts is None:
            corrections.append({
                'old_code': cat_num,
                'new_code': '???',
                'name': r['name'],
                'active': r['active'],
                'reason': f"kategorie nesedí ({r['expected_category']} vs {', '.join(r['actual_categories'])})",
                'note': 'nelze určit správnou kategorii',
            })
            continue

        brand, new_cat, new_sub = parts

        if new_cat == current_cat and new_sub == current_sub:
            # Code is already correct — the website category is wrong
            website_fixes.append({
                'code': cat_num,
                'name': r['name'],
                'active': r['active'],
                'correct_category': category_codes.get(new_cat, new_cat),
                'actual_categories': r['actual_categories'],
            })
            continue

        new_code = find_next_code(brand, new_cat, new_sub, all_codes, reserved)
        reserved.add(new_code)
        corrections.append({
            'old_code': cat_num,
            'new_code': new_code,
            'name': r['name'],
            'active': r['active'],
            'reason': f"kategorie nesedí ({r['expected_category']} vs {', '.join(r['actual_categories'])})",
            'note': '',
        })

    # ── 2. Duplicates ─────────────────────────────────────────────────
    r_dup = check_duplicate_codes(cs_products)

    for dup_code, dup_products in r_dup.items():
        if dup_code in mismatch_codes:
            continue

        keeper = dup_products[0]
        for p_info in dup_products[1:]:
            product = next(
                p for p in cs_products
                if p.get('catalogNumber') == dup_code
                and get_name(p) == p_info['name']
            )
            brand_code_str, cat_code, sub_code = parse_catalog_number(dup_code, brand_codes)
            if brand_code_str is None:
                continue

            new_code = find_next_code(brand_code_str, cat_code, sub_code, all_codes, reserved)
            reserved.add(new_code)
            keeper_name = keeper['name']
            corrections.append({
                'old_code': dup_code,
                'new_code': new_code,
                'name': p_info['name'],
                'active': p_info['active'],
                'reason': f"duplicita s '{keeper_name[:60]}'",
                'note': f"zachovává kód: {keeper_name[:50]}",
            })

    corrections.sort(key=lambda x: (not x['active'], x['old_code']))
    website_fixes.sort(key=lambda x: (not x['active'], x['code']))
    return corrections, website_fixes


def write_report(corrections, website_fixes, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    path = os.path.join(out_dir, f"code_corrections_{ts}.txt")

    lines = []
    lines.append("NÁVRH OPRAV KATALOGOVÝCH ČÍSEL")
    lines.append(f"Vygenerováno: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Celkem oprav kódů: {len(corrections)}  |  Oprav webu: {len(website_fixes)}")
    lines.append("=" * 72)

    # ── A: kód je špatně → navrhnout nový kód ─────────────────────────────
    if corrections:
        active   = [c for c in corrections if c['active']]
        inactive = [c for c in corrections if not c['active']]
        lines.append("\nA — OPRAVIT CATALOGNUMBER")
        lines.append("Kód produktu zakódovává špatnou kategorii nebo je duplicitní.")
        lines.append("-" * 72)
        for section, items in [("AKTIVNÍ", active), ("Neaktivní", inactive)]:
            if not items:
                continue
            lines.append(f"\n  [{section}]")
            for c in items:
                lines.append(f"  {c['old_code']:<20s}  →  {c['new_code']:<20s}  {c['name'][:50]}")
                lines.append(f"    Důvod: {c['reason']}")
                if c['note']:
                    lines.append(f"    Pozn.: {c['note']}")

    # ── B: web je špatně → kód je správně ────────────────────────────────
    if website_fixes:
        active   = [c for c in website_fixes if c['active']]
        inactive = [c for c in website_fixes if not c['active']]
        lines.append("\n\nB — OPRAVIT KATEGORII NA WEBU (kód je správně)")
        lines.append("Kód zakódovává správnou kategorii, ale web má produkt jinde.")
        lines.append("-" * 72)
        for section, items in [("AKTIVNÍ", active), ("Neaktivní", inactive)]:
            if not items:
                continue
            lines.append(f"\n  [{section}]")
            for c in items:
                lines.append(f"  {c['code']:<20s}  {c['name'][:55]}")
                lines.append(f"    Správná kategorie: {c['correct_category']}")
                lines.append(f"    Web má:            {', '.join(c['actual_categories'])}")

    text = '\n'.join(lines)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    return path, text


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--cs-dir',    default=DEFAULT_CS_DIR)
    p.add_argument('--output-dir', default=DEFAULT_OUT_DIR)
    args = p.parse_args()

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    cs_products, _, cs_path = load_latest_json(args.cs_dir, "CS")
    print(f"CS: {cs_path}  ({len(cs_products)} produktů)")

    brand_codes    = load_brand_codes()
    category_codes = load_category_codes()
    subcat_codes   = load_subcategory_codes()

    corrections, website_fixes = build_corrections(cs_products, brand_codes, category_codes, subcat_codes)
    print(f"Oprav kódů: {len(corrections)}  |  Oprav webu: {len(website_fixes)}")

    path, text = write_report(corrections, website_fixes, args.output_dir)
    print(text)
    print(f"\nReport uložen: {path}")


if __name__ == '__main__':
    main()
