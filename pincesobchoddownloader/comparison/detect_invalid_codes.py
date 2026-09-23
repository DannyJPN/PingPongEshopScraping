"""
Kontrola: validace formátu catalogNumber.
Ověřuje strukturu [Brand 3+][CatCode 2][SubCode 2][Seq 4].
"""
import os
import re
import sys
import io
from datetime import datetime

from compare_utils import load_latest_json, get_name, is_active
from compare_categories import (
    load_brand_codes, load_category_codes, load_subcategory_codes,
    SUBCODED_CATEGORIES,
)

DEFAULT_CS_DIR  = "F:/Dropbox/DesakaPrivate/PingPongEshopScraping/Desaka/Pincesobchod_CS"
DEFAULT_OUT_DIR = "F:/Dropbox/DesakaPrivate/PingPongEshopScraping/Desaka/Reports/Pincesobchod"

# Minimální délka brand prefixu
MIN_BRAND_LEN = 3
# Délka sekvenční části
SEQ_LEN = 4
# Délka cat kódu a sub kódu
CODE_LEN = 2


def validate_catalog_number(cat_num, brand_codes, category_codes, subcategory_codes):
    """
    Vrátí seznam chyb pro daný catalogNumber, nebo prázdný seznam pokud je OK.
    """
    errors = []

    if not cat_num:
        return ['prázdný catalogNumber']

    # Najdi brand prefix (nejdelší shoda)
    matched_brand = None
    matched_brand_len = 0
    for brand_prefix in brand_codes:
        if cat_num.upper().startswith(brand_prefix.upper()):
            if len(brand_prefix) > matched_brand_len:
                matched_brand = brand_prefix
                matched_brand_len = len(brand_prefix)

    if matched_brand is None:
        # Zkus odhadnout délku prefixu (číslice začínají)
        m = re.match(r'^([A-Za-z]+)(\d+)$', cat_num)
        prefix_guess = m.group(1) if m else cat_num[:3]
        errors.append(f"neznámý brand prefix '{prefix_guess}'")
        return errors  # bez brandu nemá smysl pokračovat

    rest = cat_num[matched_brand_len:]

    # rest musí být přesně CatCode(2) + SubCode(2) + Seq(4) = 8 číslic
    expected_len = CODE_LEN + CODE_LEN + SEQ_LEN
    if not re.match(r'^\d+$', rest):
        errors.append(f"za brand prefixem '{matched_brand}' jsou nečíselné znaky: '{rest}'")
        return errors

    if len(rest) != expected_len:
        errors.append(
            f"za prefixem '{matched_brand}' je {len(rest)} číslic, očekáváno {expected_len} "
            f"(CatCode{CODE_LEN} + SubCode{CODE_LEN} + Seq{SEQ_LEN})"
        )
        return errors

    cat_code = rest[:CODE_LEN]
    sub_code = rest[CODE_LEN:CODE_LEN + CODE_LEN]
    seq      = rest[CODE_LEN + CODE_LEN:]

    # Validace cat kódu
    if cat_code not in category_codes:
        errors.append(f"neznámý cat kód '{cat_code}'")

    # Validace sub kódu
    if cat_code in SUBCODED_CATEGORIES:
        # Pro textil musí být '00' (bez subkategorie) nebo platný subkód
        valid_subcodes = set(subcategory_codes.keys()) | {'00'}
        if sub_code not in valid_subcodes:
            errors.append(f"neznámý sub kód '{sub_code}' pro kategorii {cat_code} (Textil)")
    else:
        # Pro ostatní musí být '00'
        if sub_code != '00':
            errors.append(f"sub kód '{sub_code}' musí být '00' pro kategorii {cat_code}")

    # Sekvenční část nesmí být 0000
    if seq == '0000':
        errors.append("sekvenční část je '0000'")

    return errors


def check_invalid_codes(products, brand_codes, category_codes, subcategory_codes):
    issues = []
    for p in products:
        cat_num = p.get('catalogNumber', '')
        errors = validate_catalog_number(cat_num, brand_codes, category_codes, subcategory_codes)
        if errors:
            issues.append({
                'catalogNumber': cat_num,
                'name': get_name(p),
                'active': is_active(p),
                'errors': errors,
            })
    issues.sort(key=lambda x: (not x['active'], x['catalogNumber'] or ''))
    return issues


def write_report(issues, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    path = os.path.join(out_dir, f"invalid_codes_{ts}.txt")

    active   = [r for r in issues if r['active']]
    inactive = [r for r in issues if not r['active']]

    lines = []
    lines.append("KONTROLA: FORMÁT CATALOGOVACÍCH ČÍSEL")
    lines.append(f"Vygenerováno: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Celkem chybných: {len(issues)}  (aktivních: {len(active)}, neaktivních: {len(inactive)})")
    lines.append("=" * 72)

    for section_label, items in [("AKTIVNÍ", active), ("Neaktivní", inactive)]:
        if not items:
            continue
        lines.append(f"\n{section_label} ({len(items)} ks):")
        lines.append("-" * 72)
        for r in items:
            lines.append(f"  {(r['catalogNumber'] or '(prázdný)'):<22s}  {r['name'][:52]}")
            for err in r['errors']:
                lines.append(f"    • {err}")
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

    issues = check_invalid_codes(cs_products, brand_codes, category_codes, subcat_codes)
    active = [r for r in issues if r['active']]
    print(f"Chybné kódy — aktivních: {len(active)}, neaktivních: {len(issues) - len(active)}")

    path, text = write_report(issues, args.output_dir)
    print(text)
    print(f"\nReport uložen: {path}")


if __name__ == '__main__':
    main()
