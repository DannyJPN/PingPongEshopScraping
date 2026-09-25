"""
Kontrola: aktivní produkty bez přiřazené kategorie na webu.
Produkt bez kategorie se zákazníkům nezobrazí v žádném katalogu.
"""
import os
import sys
import io
from datetime import datetime

from compare_utils import load_latest_json, get_name, is_active
from compare_categories import get_actual_category_names

DEFAULT_CS_DIR  = "F:/Dropbox/DesakaPrivate/PingPongEshopScraping/Desaka/Pincesobchod_CS"
DEFAULT_OUT_DIR = "F:/Dropbox/DesakaPrivate/PingPongEshopScraping/Desaka/Reports/Pincesobchod"


def check_no_category(products):
    issues = []
    for p in products:
        cats = get_actual_category_names(p)
        if not cats:
            issues.append({
                'catalogNumber': p.get('catalogNumber') or '(prázdný)',
                'name': get_name(p),
                'active': is_active(p),
            })
    issues.sort(key=lambda x: (not x['active'], x['catalogNumber']))
    return issues


def write_report(issues, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    path = os.path.join(out_dir, f"no_category_{ts}.txt")

    active   = [r for r in issues if r['active']]
    inactive = [r for r in issues if not r['active']]

    lines = []
    lines.append("KONTROLA: PRODUKTY BEZ KATEGORIE")
    lines.append(f"Vygenerováno: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Celkem: {len(issues)}  (aktivních: {len(active)}, neaktivních: {len(inactive)})")
    lines.append("=" * 72)

    if active:
        lines.append(f"\nAKTIVNÍ — VYŽADUJÍ OPRAVU ({len(active)} ks):")
        lines.append("Produkty jsou viditelné, ale nezobrazí se v žádné kategorii!")
        lines.append("-" * 72)
        for r in active:
            lines.append(f"  {r['catalogNumber']:<22s}  {r['name'][:52]}")
        lines.append("")
    else:
        lines.append("\nAKTIVNÍ: žádné — OK")

    if inactive:
        lines.append(f"\nNeaktivní ({len(inactive)} ks) — informativně:")
        lines.append("-" * 72)
        for r in inactive:
            lines.append(f"  {r['catalogNumber']:<22s}  {r['name'][:52]}")

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

    issues = check_no_category(cs_products)
    active = [r for r in issues if r['active']]
    print(f"Bez kategorie — aktivních: {len(active)}, neaktivních: {len(issues) - len(active)}")

    path, text = write_report(issues, args.output_dir)
    print(text)
    print(f"\nReport uložen: {path}")


if __name__ == '__main__':
    main()