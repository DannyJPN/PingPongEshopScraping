"""
Kontrola: kód varianty musí začínat kódem mateřského produktu.
Konvence: varianta BTY17000001-01 patří k mateřskému BTY17000001.
"""
import os
import sys
import io
from datetime import datetime

from compare_utils import load_latest_json, get_name, is_active

DEFAULT_CS_DIR  = "F:/Dropbox/DesakaPrivate/PingPongEshopScraping/Desaka/Pincesobchod_CS"
DEFAULT_OUT_DIR = "F:/Dropbox/DesakaPrivate/PingPongEshopScraping/Desaka/Reports/Pincesobchod"


def check_variant_code_mismatch(products):
    issues = []
    for p in products:
        parent_code = p.get('catalogNumber') or ''
        variants = p.get('variants') or []
        for v in variants:
            var_code = v.get('catalogNumber') or ''
            if not var_code:
                issues.append({
                    'parent_code': parent_code,
                    'parent_name': get_name(p),
                    'parent_active': is_active(p),
                    'variant_code': '(prázdný)',
                    'error': 'varianta nemá catalogNumber',
                })
            elif not var_code.startswith(parent_code):
                issues.append({
                    'parent_code': parent_code,
                    'parent_name': get_name(p),
                    'parent_active': is_active(p),
                    'variant_code': var_code,
                    'error': f"'{var_code}' nezačíná '{parent_code}'",
                })

    issues.sort(key=lambda x: (not x['parent_active'], x['parent_code']))
    return issues


def write_report(issues, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    path = os.path.join(out_dir, f"variant_code_mismatch_{ts}.txt")

    active   = [r for r in issues if r['parent_active']]
    inactive = [r for r in issues if not r['parent_active']]

    lines = []
    lines.append("KONTROLA: KÓD VARIANTY vs. KÓD MATEŘSKÉHO PRODUKTU")
    lines.append(f"Vygenerováno: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Celkem neshod: {len(issues)}  (aktivních: {len(active)}, neaktivních: {len(inactive)})")
    lines.append("=" * 72)
    lines.append("Kód varianty musí začínat kódem mateřského produktu.")

    for section_label, items in [("AKTIVNÍ", active), ("Neaktivní", inactive)]:
        if not items:
            continue
        lines.append(f"\n{section_label} ({len(items)} ks):")
        lines.append("-" * 72)
        for r in items:
            lines.append(f"  Mateřský:  {r['parent_code']:<22s}  {r['parent_name'][:48]}")
            lines.append(f"  Varianta:  {r['variant_code']}")
            lines.append(f"  Chyba:     {r['error']}")
            lines.append("")

    if not issues:
        lines.append("\nŽádné neshody — OK")

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

    issues = check_variant_code_mismatch(cs_products)
    active = [r for r in issues if r['parent_active']]
    print(f"Neshody variant — aktivních: {len(active)}, neaktivních: {len(issues) - len(active)}")

    path, text = write_report(issues, args.output_dir)
    print(text)
    print(f"\nReport uložen: {path}")


if __name__ == '__main__':
    main()