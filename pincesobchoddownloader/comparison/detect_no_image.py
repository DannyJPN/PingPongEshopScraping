"""
Kontrola: aktivní produkty bez obrázku nebo bez výchozího (default) obrázku.
"""
import os
import sys
import io
from datetime import datetime

from compare_utils import load_latest_json, get_name, is_active

DEFAULT_CS_DIR  = "F:/Dropbox/DesakaPrivate/PingPongEshopScraping/Desaka/Pincesobchod_CS"
DEFAULT_OUT_DIR = "F:/Dropbox/DesakaPrivate/PingPongEshopScraping/Desaka/Reports/Pincesobchod"


def check_no_image(products):
    no_image   = []  # žádný obrázek vůbec
    no_default = []  # má obrázky, ale žádný není default=True

    for p in products:
        images = p.get('images') or []
        if not images:
            no_image.append({
                'catalogNumber': p.get('catalogNumber') or '(prázdný)',
                'name': get_name(p),
                'active': is_active(p),
            })
        elif not any(img.get('default') for img in images):
            no_default.append({
                'catalogNumber': p.get('catalogNumber') or '(prázdný)',
                'name': get_name(p),
                'active': is_active(p),
                'image_count': len(images),
            })

    no_image.sort(key=lambda x: (not x['active'], x['catalogNumber']))
    no_default.sort(key=lambda x: (not x['active'], x['catalogNumber']))
    return no_image, no_default


def write_report(no_image, no_default, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    path = os.path.join(out_dir, f"no_image_{ts}.txt")

    ni_active   = [r for r in no_image   if r['active']]
    ni_inactive = [r for r in no_image   if not r['active']]
    nd_active   = [r for r in no_default if r['active']]
    nd_inactive = [r for r in no_default if not r['active']]

    lines = []
    lines.append("KONTROLA: PRODUKTY BEZ OBRÁZKU")
    lines.append(f"Vygenerováno: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Bez obrázku vůbec  (aktivních: {len(ni_active)}, neaktivních: {len(ni_inactive)})")
    lines.append(f"Bez default obrázku (aktivních: {len(nd_active)}, neaktivních: {len(nd_inactive)})")
    lines.append("=" * 72)

    # A: žádný obrázek
    if ni_active:
        lines.append(f"\nA — AKTIVNÍ BEZ OBRÁZKU ({len(ni_active)} ks):")
        lines.append("-" * 72)
        for r in ni_active:
            lines.append(f"  {r['catalogNumber']:<22s}  {r['name'][:50]}")
    else:
        lines.append("\nA — aktivní bez obrázku: žádné — OK")

    if ni_inactive:
        lines.append(f"\nA — Neaktivní bez obrázku ({len(ni_inactive)} ks) — informativně:")
        lines.append("-" * 72)
        for r in ni_inactive:
            lines.append(f"  {r['catalogNumber']:<22s}  {r['name'][:50]}")

    # B: bez default obrázku
    if nd_active:
        lines.append(f"\nB — AKTIVNÍ BEZ DEFAULT OBRÁZKU ({len(nd_active)} ks):")
        lines.append("Produkt má obrázky, ale žádný není označen jako hlavní.")
        lines.append("-" * 72)
        for r in nd_active:
            lines.append(f"  {r['catalogNumber']:<22s}  ({r['image_count']} obr.)  {r['name'][:46]}")
    else:
        lines.append("\nB — aktivní bez default obrázku: žádné — OK")

    if nd_inactive:
        lines.append(f"\nB — Neaktivní bez default obrázku ({len(nd_inactive)} ks) — informativně:")
        lines.append("-" * 72)
        for r in nd_inactive:
            lines.append(f"  {r['catalogNumber']:<22s}  ({r['image_count']} obr.)  {r['name'][:46]}")

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

    no_image, no_default = check_no_image(cs_products)
    ni_active = [r for r in no_image   if r['active']]
    nd_active = [r for r in no_default if r['active']]
    print(f"Bez obrázku — aktivních: {len(ni_active)}, neaktivních: {len(no_image) - len(ni_active)}")
    print(f"Bez default  — aktivních: {len(nd_active)}, neaktivních: {len(no_default) - len(nd_active)}")

    path, text = write_report(no_image, no_default, args.output_dir)
    print(text)
    print(f"\nReport uložen: {path}")


if __name__ == '__main__':
    main()