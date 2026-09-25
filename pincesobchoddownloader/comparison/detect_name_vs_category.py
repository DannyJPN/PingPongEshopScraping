"""
Kontrola: odpovídá název produktu jeho kategorii na webu?
Detekuje produkty, kde název jasně naznačuje jinou kategorii, než kde produkt leží.
Výstup: report pro ruční opravu kategorizace v admin panelu e-shopu.
"""
import os
import re
import sys
import io
from datetime import datetime

from compare_utils import load_latest_json, get_name, is_active
from compare_categories import load_category_codes

DEFAULT_CS_DIR  = "F:/Dropbox/DesakaPrivate/PingPongEshopScraping/Desaka/Pincesobchod_CS"
DEFAULT_OUT_DIR = "F:/Dropbox/DesakaPrivate/PingPongEshopScraping/Desaka/Reports/Pincesobchod"


# ── name → expected category rules ───────────────────────────────────────
# Každé pravidlo: (include_pattern, exclude_pattern_or_None, cat_code, label)
# Kotva ^ zachytí produkty, jejichž název ZAČÍNÁ daným slovem — záměrně
# konzervativní, aby se předešlo false positives (lak na dřevo, měrka na síťku…).
_NAME_RULES = [
    # Roboti a příslušenství k nim
    (r'\brobot\b',               None,                          '09', 'Roboti'),
    (r'na\s+robot',              None,                          '09', 'Roboti'),
    # Záchytné sítě patří do Roboti
    (r'záchytn[aáé]\s+síť',      None,                          '09', 'Roboti'),

    # Tašky NA boty → Sportovní obuv (musí být před obecným bag pravidlem)
    (r'na\s+bot[yu]',            None,                          '07', 'Sportovní obuv'),

    # Síťky — jen pokud název ZAČÍNÁ "Síťka" (ne "měrka na síťku")
    (r'^\s*síťk',                None,                          '08', 'Síťky'),

    # Stoly — jen pokud název ZAČÍNÁ stolem (ne "čistič na stůl")
    (r'^\s*st[oůu]l\b',          None,                          '06', 'Stoly'),

    # Potahy — jen pokud název ZAČÍNÁ "Potah"
    # Výjimka: "Potah na ohrádku" = ochranný kryt → Ohrádky
    (r'^\s*potah\b',             r'na\s+ohrádku',               '01', 'Potahy'),

    # Dřeva — jen pokud název ZAČÍNÁ "Dřevo/Dřeva"
    # (ne "lak na dřevo", ne "Pálka GEWO: Dřevo X s potahy Y")
    (r'^\s*dřev[ao]\b',          None,                          '02', 'Dřeva'),

    # Hotové pálky — název ZAČÍNÁ "Pálka"
    # (zachytí i "Pálka GEWO: Dřevo X s potahy Y")
    (r'^\s*pálk',                None,                          '14', 'Pálky'),

    # Tašky NA míčky → Míčky (musí být před obecným bag pravidlem)
    (r'\btašk.*na\s+míčk|na\s+míčk.*\btašk',
                                 None,                          '03', 'Míčky'),

    # Obecné tašky / batohy / ledvinky — ne "na boty", ne "na robota", ne "na míčky"
    (r'\btašk|\bbatohy?\b|\bkufr|\bledvink',
                                 r'na\s+bot[yu]|na\s+robot',   '04', 'Tašky a batohy'),

    # Sportovní obuv
    (r'\bobuv\b|\bboty\b|\bbota\b|\btenisky\b',
                                 None,                          '07', 'Sportovní obuv'),

    # Čističe, lepidla
    (r'\bčistič',                None,                          '17', 'Čističe'),
    (r'\blepidl',                None,                          '16', 'Lepidla'),
]


def guess_expected_cat(name):
    """Vrátí (cat_code, label) podle jména nebo (None, None)."""
    n = name.lower()
    for include, exclude, cat_code, label in _NAME_RULES:
        if re.search(include, n):
            if exclude is None or not re.search(exclude, n):
                return cat_code, label
    return None, None


def get_product_cat_codes(product, category_codes):
    """Vrátí množinu top-level cat_code hodnot z kategorií produktu na webu."""
    cat_name_to_code = {v: k for k, v in category_codes.items()}
    codes = set()
    for cat in (product.get('categories') or []):
        for name in (cat.get('path') or {}).values():
            if name in cat_name_to_code:
                codes.add(cat_name_to_code[name])
    return codes


def check_name_vs_category(products, category_codes):
    issues = []
    for p in products:
        name = get_name(p)
        if not name:
            continue
        exp_code, exp_label = guess_expected_cat(name)
        if exp_code is None:
            continue

        actual_codes = get_product_cat_codes(p, category_codes)
        if not actual_codes:
            # Bez kategorie — flagovat pokud název naznačuje konkrétní kategorii
            actual_names = ['(bez kategorie)']
            issues.append({
                'catalogNumber': p.get('catalogNumber', ''),
                'name': name,
                'active': is_active(p),
                'expected_category': exp_label,
                'actual_categories': actual_names,
            })
            continue

        if exp_code not in actual_codes:
            actual_names = sorted(
                category_codes[c] for c in actual_codes if c in category_codes
            )
            issues.append({
                'catalogNumber': p.get('catalogNumber', ''),
                'name': name,
                'active': is_active(p),
                'expected_category': exp_label,
                'actual_categories': actual_names,
            })

    issues.sort(key=lambda x: (not x['active'], x['expected_category'], x['catalogNumber']))
    return issues


def write_report(issues, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    path = os.path.join(out_dir, f"name_vs_category_{ts}.txt")

    lines = []
    lines.append("KONTROLA: NÁZEV PRODUKTU vs. KATEGORIE NA WEBU")
    lines.append(f"Vygenerováno: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Celkem podezřelých: {len(issues)}")
    lines.append("=" * 76)
    lines.append("Produkty, jejichž název naznačuje jinou kategorii, než kde jsou na webu.")
    lines.append("Doporučení: přeřadit produkt v administraci e-shopu.")

    active   = [r for r in issues if r['active']]
    inactive = [r for r in issues if not r['active']]

    for section_label, items in [("AKTIVNÍ", active), ("Neaktivní", inactive)]:
        if not items:
            continue
        lines.append(f"\n{section_label} ({len(items)} ks):")
        lines.append("-" * 76)
        for r in items:
            lines.append(f"  {r['catalogNumber']:<22s}  {r['name'][:60]}")
            lines.append(f"    Název naznačuje: {r['expected_category']}")
            lines.append(f"    Web má:          {', '.join(r['actual_categories'])}")
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

    category_codes = load_category_codes()
    issues = check_name_vs_category(cs_products, category_codes)
    print(f"Podezřelé shody název vs. kategorie: {len(issues)}")

    path, text = write_report(issues, args.output_dir)
    print(text)
    print(f"\nReport uložen: {path}")


if __name__ == '__main__':
    main()
