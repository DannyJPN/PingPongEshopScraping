"""
Kontrola: odpovídá catalogNumber (kód) kategorii produktu na webu?
Detekuje produkty, kde kód zakódovává jinou kategorii, než kde produkt na webu leží.
Výstup: report pro opravu catalogNumber v admin panelu e-shopu.
"""
import os
import sys
import io
from datetime import datetime

from compare_utils import load_latest_json, get_name, is_active
from compare_categories import (
    load_brand_codes, load_category_codes, load_subcategory_codes,
    check_categories, parse_catalog_number, SUBCODED_CATEGORIES,
)

DEFAULT_CS_DIR  = "F:/Dropbox/DesakaPrivate/PingPongEshopScraping/Desaka/Pincesobchod_CS"
DEFAULT_OUT_DIR = "F:/Dropbox/DesakaPrivate/PingPongEshopScraping/Desaka/Reports/Pincesobchod"


def format_mismatch(r, category_codes, subcategory_codes):
    """Připraví textový popis nesouladu kódu vs. kategorie."""
    cat_num   = r['catalogNumber']
    _, code_cat, code_sub = parse_catalog_number(cat_num, {})  # brand ignored here
    # Re-parse properly with brand codes available to caller
    code_cat_name = r['expected_category']
    actual       = ', '.join(r['actual_categories'])

    if code_cat in SUBCODED_CATEGORIES and r.get('expected_subcat'):
        code_label = f"{code_cat_name} › {r['expected_subcat']}"
    else:
        code_label = code_cat_name

    return code_label, actual


def write_report(results, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    path = os.path.join(out_dir, f"code_vs_category_{ts}.txt")

    mismatches       = results['mismatches']
    unknown_brand    = results['unknown_brand']
    unknown_cat_code = results['unknown_cat_code']
    unknown_sub_code = results['unknown_sub_code']

    active   = [r for r in mismatches if r['active']]
    inactive = [r for r in mismatches if not r['active']]

    lines = []
    lines.append("KONTROLA: KATALOGOVÝ KÓD vs. KATEGORIE NA WEBU")
    lines.append(f"Vygenerováno: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Celkem neshod: {len(mismatches)}  "
                 f"(aktivních: {len(active)}, neaktivních: {len(inactive)})")
    if unknown_brand:
        lines.append(f"Neznámý brand prefix: {len(unknown_brand)}")
    if unknown_cat_code:
        lines.append(f"Neznámý cat kód:      {len(unknown_cat_code)}")
    if unknown_sub_code:
        lines.append(f"Neznámý sub kód:      {len(unknown_sub_code)}")
    lines.append("=" * 76)
    lines.append("Kód produktu zakódovává jinou kategorii, než kde produkt na webu leží.")
    lines.append("Doporučení: opravit catalogNumber v administraci e-shopu.")

    for section_label, items in [("AKTIVNÍ", active), ("Neaktivní", inactive)]:
        if not items:
            continue
        lines.append(f"\n{section_label} ({len(items)} ks):")
        lines.append("-" * 76)
        for r in items:
            if r.get('expected_subcat'):
                code_label = f"{r['expected_category']} › {r['expected_subcat']}"
            else:
                code_label = r['expected_category']
            lines.append(f"  {r['catalogNumber']:<20s}  {r['name'][:60]}")
            lines.append(f"    Kód zakódovává: {code_label}")
            lines.append(f"    Web má:         {', '.join(r['actual_categories'])}")
            lines.append("")

    if unknown_brand:
        lines.append(f"\nNeznámé brand prefixy ({len(unknown_brand)} ks):")
        lines.append("-" * 76)
        for r in unknown_brand:
            flag = "AKTIVNÍ" if r['active'] else "neaktivní"
            lines.append(f"  [{flag}] {r['catalogNumber']:<20s}  prefix={r['brand_prefix']}  {r['name'][:50]}")
        lines.append("")

    if unknown_cat_code:
        lines.append(f"\nNeznámé category kódy ({len(unknown_cat_code)} ks):")
        lines.append("-" * 76)
        for r in unknown_cat_code:
            lines.append(f"  {r['catalogNumber']:<20s}  kód={r['cat_code']}  {r['name'][:55]}")
        lines.append("")

    if unknown_sub_code:
        lines.append(f"\nNeznámé sub kódy / kategorie 05 ({len(unknown_sub_code)} ks):")
        lines.append("-" * 76)
        for r in unknown_sub_code:
            flag = "AKTIVNÍ" if r['active'] else "neaktivní"
            lines.append(f"  [{flag}] {r['catalogNumber']:<20s}  sub={r['sub_code']}  {r['name'][:50]}")
        lines.append("")

    text = '\n'.join(lines)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    return path, text


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--cs-dir',     default=DEFAULT_CS_DIR)
    p.add_argument('--output-dir', default=DEFAULT_OUT_DIR)
    args = p.parse_args()

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    cs_products, _, cs_path = load_latest_json(args.cs_dir, "CS")
    print(f"CS: {cs_path}  ({len(cs_products)} produktů)")

    brand_codes    = load_brand_codes()
    category_codes = load_category_codes()
    subcat_codes   = load_subcategory_codes()

    results = check_categories(cs_products, brand_codes, category_codes, subcat_codes)
    total = len(results['mismatches'])
    print(f"Neshod kód vs. kategorie: {total}")

    path, text = write_report(results, args.output_dir)
    print(text)
    print(f"\nReport uložen: {path}")


if __name__ == '__main__':
    main()
