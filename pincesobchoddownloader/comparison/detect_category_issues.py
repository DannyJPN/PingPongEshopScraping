"""
Detekuje produkty, jejichž aktuální kategorie na webu je podezřelá.
Pro každou neshodu (kód vs. web) odhadne správnou kategorii z názvu produktu
a klasifikuje:
  A) Kód správně, web špatně → doporučí přeřadit produkt v admin panelu
  B) Web správně, kód špatně → doporučí opravit catalogNumber
  C) Nejednoznačné / nelze určit → pro ruční kontrolu
"""
import csv
import os
import re
import sys
import io
from datetime import datetime

from compare_utils import load_latest_json, get_name, is_active
from compare_categories import (
    load_brand_codes, load_category_codes, load_subcategory_codes,
    check_categories, parse_catalog_number, SUBCODED_CATEGORIES,
)

DEFAULT_CS_DIR  = "H:/Desaka/Pincesobchod_CS"
DEFAULT_OUT_DIR = "H:/Desaka/Reports/Pincesobchod"


# ── name-based category guesser ───────────────────────────────────────────

# Rules: (pattern, cat_code, note) — first match wins, case-insensitive.
# Order matters: more specific first.
_NAME_RULES = [
    # Robots and robot accessories
    (r'\brobot\b',              '09', 'Roboti'),
    (r'na\s+robot',             '09', 'Roboti'),          # "taška na robota"
    # Balls accessories (bags/cases FOR balls — not paddle cases)
    (r'na\s+míčk',              '03', 'Míčky'),           # "taška na míčky"
    # Balls themselves
    (r'\bmíček\b',              '03', 'Míčky'),
    (r'\bmíčk[yůui]',          '03', 'Míčky'),
    # Nets
    (r'\bsíťk',                 '08', 'Síťky'),
    # Tables
    (r'\bstůl\b|\bstoly\b|\bstolu\b|\bstole\b', '06', 'Stoly'),
    # Table accessories (separators, enclosures)
    (r'\bohrádka\b|\bohrádky\b', '15', 'Ohrádky'),
    (r'\brozhodčí\b',           '18', 'Stolky pro rozhodčí'),
    # Rubbers
    (r'\bpotah\b|\bpotahy\b',   '01', 'Potahy'),
    # Blades
    (r'\bdřevo\b|\bdřeva\b|\bdřev[uo]\b', '02', 'Dřeva'),
    # Complete bats (before "na pálku" paddle-case rule)
    (r'\bhotová\s+pálka\b|\bhotové\s+pálky\b', '14', 'Pálky'),
    # Paddle cases — must be before generic bag rule
    (r'na\s+pálk',              '11', 'Pouzdra'),
    (r'\bpouzdr',               '11', 'Pouzdra'),
    # General bags / backpacks / suitcases
    (r'\btašk',                 '04', 'Tašky a batohy'),
    (r'\bbatohy?\b',            '04', 'Tašky a batohy'),
    (r'\bkufr',                 '04', 'Tašky a batohy'),
    (r'\bledvink',              '04', 'Tašky a batohy'),  # ledvinka = hip bag
    # Clothing
    (r'\btriček|\btriko\b|\bdres\b|\bkalhot|\bmikina|\bbund[ay]\b'
     r'|\bteplák|\bsukn|\bpolo\b|\bponožk|\bčepic|\bčelenk|\bpotítk'
     r'|\bspodní\b',           '05', 'Textil'),
    # Footwear
    (r'\bobuv\b|\bboty\b|\bbota\b|\btenisky\b', '07', 'Sportovní obuv'),
    # Cleaners / glues / accessories
    (r'\bčistič',               '17', 'Čističe'),
    (r'\blepidl',               '16', 'Lepidla'),
    # Counters / trophies
    (r'\bpočítadl',             '13', 'Počítadla'),
    (r'\bpohár\b|\bpoháry\b',   '12', 'Poháry'),
]


def guess_category_from_name(name):
    """Return (cat_code, category_label) from name heuristics, or (None, None)."""
    n = name.lower()
    for pattern, cat_code, label in _NAME_RULES:
        if re.search(pattern, n):
            return cat_code, label
    return None, None


# ── classification ────────────────────────────────────────────────────────

def classify_mismatch(product, cat_num, code_cat_code, code_sub_code, code_cat_name,
                      actual_categories, category_codes, subcategory_codes):
    """
    Returns a dict describing the mismatch and its likely cause.
    For subcoded categories (05 = Textil), also checks subcode correctness.
    """
    name = get_name(product)
    name_cat_code, name_cat_label = guess_category_from_name(name)

    # web_cat_code: top-level category from website
    web_cat_code = next(
        (k for k, v in category_codes.items() if v in actual_categories), None)
    web_cat_name = actual_categories[0] if actual_categories else '?'

    # ── Special handling for subcoded categories (e.g. Textil = 05) ──────
    # Build reverse map: subcat name → subcode (needed for both checks below)
    sub_name_to_code = {}
    for subcode, names in subcategory_codes.items():
        for n in names:
            sub_name_to_code[n] = subcode

    if code_cat_code in SUBCODED_CATEGORIES:
        top_level_name = category_codes.get(code_cat_code, '')
        # Web is "in the same category" if actual_categories contains the top-level
        # name OR any known subcat name (leaf may be subcat without top-level parent)
        web_subcat_names = [c for c in actual_categories if c in sub_name_to_code]
        web_is_in_same_cat = (top_level_name in actual_categories
                               or bool(web_subcat_names))

        if web_is_in_same_cat:
            if web_subcat_names:
                web_sub_code    = sub_name_to_code[web_subcat_names[0]]
                web_subcat_label = web_subcat_names[0]
            else:
                web_sub_code    = '00'
                web_subcat_label = top_level_name
            code_subcat_label = next(
                (n for subcode, names in subcategory_codes.items()
                 if subcode == code_sub_code for n in names), f"subkód {code_sub_code}")
            return {
                'catalogNumber': cat_num,
                'name': name,
                'active': is_active(product),
                'code_category': f"{code_cat_name} › {code_subcat_label}",
                'web_categories': actual_categories,
                'name_suggests': None,
                'verdict': 'kod_spatne',
                'suggestion': (
                    f"Opravit catalogNumber — subkód říká '{code_subcat_label}' "
                    f"(kód {code_sub_code}), ale produkt patří do '{web_subcat_label}' "
                    f"(subkód {web_sub_code})"
                ),
            }

    # ── Standard top-level category mismatch ─────────────────────────────
    verdict = 'nejednoznacne'
    suggestion = ''

    if name_cat_code is not None:
        if name_cat_code == code_cat_code:
            verdict = 'web_spatne'
            suggestion = (f"Přeřadit produkt do kategorie '{name_cat_label}' "
                          f"v administraci e-shopu")
        elif name_cat_code == web_cat_code:
            verdict = 'kod_spatne'
            suggestion = (f"Opravit catalogNumber — kód říká '{code_cat_name}', "
                          f"ale produkt patří do '{name_cat_label}'")
        else:
            verdict = 'nejednoznacne'
            suggestion = (f"Kód: {code_cat_name} | Web: {web_cat_name} | "
                          f"Název naznačuje: {name_cat_label} — prověřte ručně")
    else:
        verdict = 'neznamo'
        suggestion = (f"Nelze určit kategorii z názvu — "
                      f"kód říká '{code_cat_name}', web má '{web_cat_name}'")

    return {
        'catalogNumber': cat_num,
        'name': name,
        'active': is_active(product),
        'code_category': code_cat_name,
        'web_categories': actual_categories,
        'name_suggests': name_cat_label,
        'verdict': verdict,
        'suggestion': suggestion,
    }


# ── report ────────────────────────────────────────────────────────────────

def write_report(results, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    path = os.path.join(out_dir, f"category_issues_{ts}.txt")

    lines = []
    lines.append("DETEKCE PODEZŘELÝCH KATEGORIÍ PRODUKTŮ")
    lines.append(f"Vygenerováno: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Celkem neshod: {len(results)}")
    lines.append("=" * 76)

    groups = {
        'web_spatne':   ("A — KÓD SPRÁVNĚ, WEB ŠPATNĚ",
                         "Pro tyto produkty opravte kategorii v admin panelu e-shopu."),
        'kod_spatne':   ("B — WEB SPRÁVNĚ, KÓD ŠPATNĚ",
                         "Pro tyto produkty je třeba opravit catalogNumber."),
        'nejednoznacne': ("C — NEJEDNOZNAČNÉ",
                          "Nelze automaticky určit. Prověřte ručně."),
        'neznamo':      ("D — NELZE DETEKOVAT Z NÁZVU",
                         "Název neposkytuje dostatek informací."),
    }

    for verdict_key, (heading, note) in groups.items():
        items = [r for r in results if r['verdict'] == verdict_key]
        if not items:
            continue
        active   = [r for r in items if r['active']]
        inactive = [r for r in items if not r['active']]

        lines.append(f"\n{'=' * 76}")
        lines.append(f"{heading}  ({len(items)} ks)")
        lines.append(note)
        lines.append('-' * 76)

        for section_label, section_items in [("AKTIVNÍ", active), ("Neaktivní", inactive)]:
            if not section_items:
                continue
            lines.append(f"\n  [{section_label}]")
            for r in section_items:
                lines.append(f"  {r['catalogNumber']:<20s}  {r['name'][:60]}")
                lines.append(f"    Kód říká:      {r['code_category']}")
                lines.append(f"    Web má:        {', '.join(r['web_categories'])}")
                if r['name_suggests']:
                    lines.append(f"    Název naznačuje: {r['name_suggests']}")
                lines.append(f"    Doporučení:    {r['suggestion']}")
                lines.append("")

    text = '\n'.join(lines)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    return path, text


# ── main ─────────────────────────────────────────────────────────────────

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

    r_cat = check_categories(cs_products, brand_codes, category_codes, subcat_codes)
    mismatches = r_cat['mismatches']
    print(f"Neshod kód vs. web: {len(mismatches)}")

    product_map = {p['catalogNumber']: p for p in cs_products if p.get('catalogNumber')}

    results = []
    for r in mismatches:
        cat_num = r['catalogNumber']
        product = product_map.get(cat_num)
        if product is None:
            continue
        _, code_cat_code, code_sub_code = parse_catalog_number(cat_num, brand_codes)
        code_cat_name = category_codes.get(code_cat_code, code_cat_code)
        result = classify_mismatch(
            product, cat_num, code_cat_code, code_sub_code, code_cat_name,
            r['actual_categories'], category_codes, subcat_codes,
        )
        results.append(result)

    # Sort: active first, then by verdict severity
    verdict_order = {'web_spatne': 0, 'kod_spatne': 1, 'nejednoznacne': 2, 'neznamo': 3}
    results.sort(key=lambda x: (not x['active'], verdict_order.get(x['verdict'], 9), x['catalogNumber']))

    path, text = write_report(results, args.output_dir)
    print(text)
    print(f"\nReport uložen: {path}")


if __name__ == '__main__':
    main()
