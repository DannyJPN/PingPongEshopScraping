"""
Detekce sdílených obrázků: stejné image ID se vyskytuje u více různých produktů.
Pokud dva různé produkty sdílejí totožný obrázek, jeden z nich má pravděpodobně
fotky jiného produktu.

Výstup je seskupen podle typu problému:
  A — Sdílený VÝCHOZÍ obrázek (default=True)  → nejvyšší priorita
  B — Sdílený galeriový obrázek (default=False)
"""
import json
import os
import sys
import io
from collections import defaultdict
from datetime import datetime

from compare_utils import load_latest_json, get_name, is_active

DEFAULT_CS_DIR  = "F:/Dropbox/DesakaPrivate/PingPongEshopScraping/Desaka/Pincesobchod_CS"
DEFAULT_OUT_DIR = "F:/Dropbox/DesakaPrivate/PingPongEshopScraping/Desaka/Reports/Pincesobchod"


def build_image_index(products):
    """Vrátí {image_id: [{catalogNumber, name, active, is_default}]}."""
    index = defaultdict(list)
    for p in products:
        cat    = p.get('catalogNumber') or '(prázdný)'
        name   = get_name(p)
        active = is_active(p)
        for img in (p.get('images') or []):
            img_id = img.get('id')
            if img_id is None:
                continue
            index[img_id].append({
                'catalogNumber': cat,
                'name':          name,
                'active':        active,
                'is_default':    bool(img.get('default')),
                'position':      img.get('position', 0),
                'url':           img.get('url', ''),
            })
    return index


def detect_shared(index):
    """Vrátí skupiny sdílených obrázků rozdělené na default a galeriové."""
    shared_default  = []  # image je default alespoň u jednoho produktu
    shared_gallery  = []  # image není default u žádného

    for img_id, entries in index.items():
        # Sdílený = vyskytuje se u více různých produktů
        codes = {e['catalogNumber'] for e in entries}
        if len(codes) < 2:
            continue

        any_default = any(e['is_default'] for e in entries)
        record = {
            'image_id': img_id,
            'url':      entries[0]['url'],
            'products': sorted(entries, key=lambda e: (not e['active'], e['catalogNumber'])),
        }
        if any_default:
            shared_default.append(record)
        else:
            shared_gallery.append(record)

    shared_default.sort(key=lambda r: r['image_id'])
    shared_gallery.sort(key=lambda r: r['image_id'])
    return shared_default, shared_gallery


def write_report(shared_default, shared_gallery, out_dir, cs_path):
    os.makedirs(out_dir, exist_ok=True)
    ts   = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    path = os.path.join(out_dir, f"shared_images_{ts}.txt")

    def active_label(e):
        return "" if e['active'] else " [neaktivní]"

    lines = []
    lines.append("DETEKCE SDÍLENÝCH OBRÁZKŮ — ČESKÝ ESHOP")
    lines.append(f"Vygenerováno : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Zdroj        : {cs_path}")
    lines.append("")
    lines.append(f"A — Sdílený VÝCHOZÍ obrázek  : {len(shared_default)} případů")
    lines.append(f"B — Sdílený galeriový obrázek : {len(shared_gallery)} případů")
    lines.append("=" * 72)

    # A
    if shared_default:
        lines.append(f"\nA — SDÍLENÝ VÝCHOZÍ OBRÁZEK ({len(shared_default)} případů)")
        lines.append("Stejný obrázek je hlavní fotkou u více produktů — jeden z nich")
        lines.append("pravděpodobně ukazuje fotku jiného produktu.")
        lines.append("-" * 72)
        for r in shared_default:
            lines.append(f"  image #{r['image_id']}  {r['url']}")
            for e in r['products']:
                dflag = " [VÝCHOZÍ]" if e['is_default'] else ""
                lines.append(f"    {e['catalogNumber']:<22s}{dflag}{active_label(e)}  {e['name'][:45]}")
    else:
        lines.append("\nA — Sdílený výchozí obrázek: žádný — OK")

    # B
    if shared_gallery:
        lines.append(f"\nB — SDÍLENÝ GALERIOVÝ OBRÁZEK ({len(shared_gallery)} případů)")
        lines.append("Stejný obrázek se vyskytuje v galerii u více produktů.")
        lines.append("-" * 72)
        for r in shared_gallery:
            lines.append(f"  image #{r['image_id']}  {r['url']}")
            for e in r['products']:
                lines.append(f"    {e['catalogNumber']:<22s}{active_label(e)}  {e['name'][:45]}")
    else:
        lines.append("\nB — Sdílený galeriový obrázek: žádný — OK")

    text = '\n'.join(lines)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    return path, text


def main():
    import argparse
    p = argparse.ArgumentParser(description="Detekce produktů se sdílenými (cizími) obrázky")
    p.add_argument('--cs-dir',     default=DEFAULT_CS_DIR)
    p.add_argument('--output-dir', default=DEFAULT_OUT_DIR)
    args = p.parse_args()

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    cs_dir = args.cs_dir
    # Pokud cs_dir je přímo složka s JSON souborem, projdeme nadřazený adresář
    direct_json = os.path.join(cs_dir, "Pincesobchod_CS.json")
    if os.path.isfile(direct_json):
        with open(direct_json, encoding='utf-8') as f:
            cs_products = json.load(f).get('data', [])
        cs_path = direct_json
    else:
        cs_products, _, cs_path = load_latest_json(cs_dir, "CS")
    print(f"CS: {cs_path}  ({len(cs_products)} produktů)")

    index = build_image_index(cs_products)
    shared_default, shared_gallery = detect_shared(index)

    print(f"Sdílený výchozí obrázek : {len(shared_default)}")
    print(f"Sdílený galeriový obrázek: {len(shared_gallery)}")

    path, text = write_report(shared_default, shared_gallery, args.output_dir, cs_path)
    print(text)
    print(f"\nReport uložen: {path}")


if __name__ == '__main__':
    main()
