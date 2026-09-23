"""
Detekce produktů, které mají fotky jiného produktu.

Metoda: SSIM (Structural Similarity Index) na obrázcích zmenšených na šířku
RESIZE_WIDTH px při zachování poměru stran.

Optimalizace: obrázky s různým poměrem stran (tolerance AR_TOLERANCE) se
považují za různé bez výpočtu SSIM.

Skupiny výsledků:
  A — Stejná HLAVNÍ fotka u různých produktů  (nejvyšší priorita)
  B — Stejná GALERIOVÁ fotka u různých produktů
  C — Hlavní fotka shodná s galerií jiného

Soubory: {catalogNumber}_{position}.jpg
Placeholder soubory jsou vyřazeny z porovnání.
"""
import os
import sys
import io
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity as ssim
from tqdm import tqdm

PHOTOS_DIR   = "F:/Dropbox/DesakaPrivate/PingPongEshopScraping/Desaka/Pincesobchod_CS/Full_23.09.2026/Photos"
DEFAULT_OUT  = "F:/Dropbox/DesakaPrivate/PingPongEshopScraping/Desaka/Reports/Pincesobchod"

# Soubory, které smí sdílet více produktů (placeholdery)
PLACEHOLDERS = {"JOO15000003_01.jpg", "DES19000007_01.jpg"}

RESIZE_WIDTH  = 192      # šířka pro porovnání
AR_TOLERANCE  = 0.02     # max. rozdíl poměru stran (2 %)
SSIM_THRESHOLD = 0.97    # SSIM >= tato hodnota = stejný obrázek


def catalog_from_filename(fname):
    stem = Path(fname).stem
    parts = stem.rsplit('_', 1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0], int(parts[1])
    return stem, 0


def resize_to_width(img, width):
    w, h = img.size
    new_h = max(1, round(h * width / w))
    return img.resize((width, new_h), Image.LANCZOS)


def load_images(photos_dir, placeholders):
    """Vrátí list {'catalogNumber', 'position', 'fname', 'ar', 'arr'} a set placeholder kódů."""
    entries = []
    placeholder_cats = set()
    files = sorted(f for f in os.listdir(photos_dir) if f.lower().endswith('.jpg'))
    for fname in tqdm(files, desc="Načítám fotky", unit="obr"):
        path = os.path.join(photos_dir, fname)
        cat, pos = catalog_from_filename(fname)
        try:
            img = Image.open(path).convert('RGB')
            w, h = img.size
            ar = w / h
            resized = resize_to_width(img, RESIZE_WIDTH)
            arr = np.array(resized, dtype=np.float32) / 255.0
            entry = {
                'catalogNumber': cat,
                'position':      pos,
                'fname':         fname,
                'ar':            ar,
                'arr':           arr,
            }
            if fname in placeholders:
                placeholder_cats.add(cat)
                tqdm.write(f"  Placeholder: {fname}  (AR={ar:.3f})")
            entries.append(entry)
        except Exception as e:
            tqdm.write(f"  Chyba {fname}: {e}", file=sys.stderr)
    return entries, placeholder_cats


def find_duplicates(entries, placeholder_cats):
    results = []
    n = len(entries)
    compared = 0
    skipped_ar = 0
    total_pairs = n * (n - 1) // 2
    with tqdm(total=total_pairs, desc="Porovnávám páry", unit="pár",
              bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]") as pbar:
        for i in range(n):
            for j in range(i + 1, n):
                pbar.update(1)
                a = entries[i]
                b = entries[j]
                if a['catalogNumber'] == b['catalogNumber']:
                    continue
                if a['catalogNumber'] in placeholder_cats and b['catalogNumber'] in placeholder_cats:
                    continue
                if abs(a['ar'] - b['ar']) > AR_TOLERANCE:
                    skipped_ar += 1
                    continue
                if a['arr'].shape != b['arr'].shape:
                    skipped_ar += 1
                    continue
                compared += 1
                score = ssim(a['arr'], b['arr'], data_range=1.0, channel_axis=2)
                if score >= SSIM_THRESHOLD:
                    a_main = (a['position'] == 1)
                    b_main = (b['position'] == 1)
                    if a_main and b_main:
                        group = 'A'
                    elif not a_main and not b_main:
                        group = 'B'
                    else:
                        group = 'C'
                    results.append({
                        'cat_a':  a['catalogNumber'], 'pos_a': a['position'],
                        'cat_b':  b['catalogNumber'], 'pos_b': b['position'],
                        'score':  score, 'group': group,
                    })
    tqdm.write(f"  SSIM porovnání: {compared:,}, přeskočeno (AR): {skipped_ar:,}")
    results.sort(key=lambda r: (r['group'], -r['score'], r['cat_a']))
    return results


def write_report(results, out_dir, photos_dir):
    os.makedirs(out_dir, exist_ok=True)
    ts   = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    path = os.path.join(out_dir, f"wrong_photos_ssim_{ts}.txt")

    g = {'A': [], 'B': [], 'C': []}
    for r in results:
        g[r['group']].append(r)

    lines = []
    lines.append("DETEKCE ZÁMĚNY FOTEK — ČESKÝ ESHOP (SSIM)")
    lines.append(f"Vygenerováno  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Zdroj fotek   : {photos_dir}")
    lines.append(f"Šířka resize  : {RESIZE_WIDTH} px")
    lines.append(f"AR tolerance  : {AR_TOLERANCE}")
    lines.append(f"SSIM threshold: {SSIM_THRESHOLD}")
    lines.append("")
    lines.append(f"A — Stejná HLAVNÍ fotka u různých produktů    : {len(g['A'])} párů")
    lines.append(f"B — Stejná GALERIOVÁ fotka u různých produktů : {len(g['B'])} párů")
    lines.append(f"C — Hlavní fotka shodná s galerií jiného      : {len(g['C'])} párů")
    lines.append("=" * 72)

    descs = {
        'A': ("STEJNÁ HLAVNÍ FOTKA",
              "Oba produkty mají vizuálně totožnou hlavní fotku.\n"
              "Jeden z nich pravděpodobně zobrazuje špatný produkt."),
        'B': ("STEJNÁ GALERIOVÁ FOTKA",
              "V galerii obou produktů se vyskytuje vizuálně totožná fotka."),
        'C': ("HLAVNÍ FOTKA = GALERIE JINÉHO",
              "Hlavní fotka jednoho produktu odpovídá galerii jiného."),
    }

    for grp in ('A', 'B', 'C'):
        items = g[grp]
        title, desc = descs[grp]
        if items:
            lines.append(f"\n{grp} — {title} ({len(items)} párů)")
            lines.append(desc)
            lines.append("-" * 72)
            for r in items:
                lines.append(
                    f"  {r['cat_a']} (foto #{r['pos_a']})  ↔  "
                    f"{r['cat_b']} (foto #{r['pos_b']})   [SSIM={r['score']:.4f}]"
                )
        else:
            lines.append(f"\n{grp} — {title}: žádný — OK")

    text = '\n'.join(lines)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    return path, text


def main():
    import argparse
    p = argparse.ArgumentParser(description="Detekce záměny fotek (SSIM)")
    p.add_argument('--photos-dir',     default=PHOTOS_DIR)
    p.add_argument('--output-dir',     default=DEFAULT_OUT)
    p.add_argument('--resize-width',   type=int,   default=RESIZE_WIDTH)
    p.add_argument('--ar-tolerance',   type=float, default=AR_TOLERANCE)
    p.add_argument('--ssim-threshold', type=float, default=SSIM_THRESHOLD)
    args = p.parse_args()

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    print(f"Načítám fotky z: {args.photos_dir}")
    entries, placeholder_cats = load_images(args.photos_dir, PLACEHOLDERS)
    print(f"Načteno {len(entries)} fotek pro {len({e['catalogNumber'] for e in entries})} produktů")
    print(f"Placeholdery: {placeholder_cats}")

    print("Porovnávám páry (SSIM)...")
    results = find_duplicates(entries, placeholder_cats)
    print(f"Nalezeno {len(results)} podezřelých párů")

    path, text = write_report(results, args.output_dir, args.photos_dir)
    print(text)
    print(f"\nReport uložen: {path}")


if __name__ == '__main__':
    main()