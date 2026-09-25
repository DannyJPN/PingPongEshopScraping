"""
Kontrola: aktivní produkty s nulovou nebo chybějící cenou.
Produkt s cenou 0 musí být skrytý (visibility=False) nebo archivovaný (archive=True).
"""
import os
import sys
import io
from datetime import datetime

from compare_utils import load_latest_json, get_name, is_active

DEFAULT_CS_DIR  = "F:/Dropbox/DesakaPrivate/PingPongEshopScraping/Desaka/Pincesobchod_CS"
DEFAULT_OUT_DIR = "F:/Dropbox/DesakaPrivate/PingPongEshopScraping/Desaka/Reports/Pincesobchod"


def get_price(product):
    val = product.get('price')
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def check_zero_price(products):
    issues = []
    for p in products:
        price = get_price(p)
        if price is None or price == 0.0:
            issues.append({
                'catalogNumber': p.get('catalogNumber') or '(prázdný)',
                'name': get_name(p),
                'active': is_active(p),
                'visibility': bool(p.get('visibility')),
                'archive': bool(p.get('archive')),
                'price': price,
            })
    issues.sort(key=lambda x: (not x['active'], x['catalogNumber']))
    return issues


def write_report(issues, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    path = os.path.join(out_dir, f"zero_price_{ts}.txt")

    active   = [r for r in issues if r['active']]
    inactive = [r for r in issues if not r['active']]

    lines = []
    lines.append("KONTROLA: PRODUKTY S NULOVOU NEBO CHYBĚJÍCÍ CENOU")
    lines.append(f"Vygenerováno: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Celkem: {len(issues)}  (aktivních: {len(active)}, neaktivních: {len(inactive)})")
    lines.append("=" * 72)

    if active:
        lines.append(f"\nAKTIVNÍ — VYŽADUJÍ OKAMŽITOU OPRAVU ({len(active)} ks):")
        lines.append("Produkty jsou viditelné zákazníkům, ale nemají cenu!")
        lines.append("-" * 72)
        for r in active:
            lines.append(f"  {r['catalogNumber']:<22s}  cena={r['price']}  {r['name'][:48]}")
            lines.append(f"    visibility={r['visibility']}, archive={r['archive']}")
            lines.append("")
    else:
        lines.append("\nAKTIVNÍ: žádné — OK")

    if inactive:
        lines.append(f"\nNeaktivní ({len(inactive)} ks) — informativně:")
        lines.append("-" * 72)
        for r in inactive:
            lines.append(f"  {r['catalogNumber']:<22s}  cena={r['price']}  {r['name'][:48]}")

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

    issues = check_zero_price(cs_products)
    active = [r for r in issues if r['active']]
    print(f"Nulová cena — aktivních: {len(active)}, neaktivních: {len(issues) - len(active)}")

    path, text = write_report(issues, args.output_dir)
    print(text)
    print(f"\nReport uložen: {path}")


if __name__ == '__main__':
    main()