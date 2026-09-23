import argparse
import os
import sys
import io
from datetime import datetime

from compare_utils import load_latest_json, match_by_catalog_number
import compare_missing_products
import compare_visibility
import compare_identity
import compare_variants
import compare_images
from compare_categories import (
    load_brand_codes, load_category_codes, load_subcategory_codes,
    check_categories, print_report as print_categories_report,
    check_duplicate_codes, print_duplicates_report,
)


DEFAULT_CS_DIR  = "H:/Desaka/Pincesobchod_CS"
DEFAULT_SK_DIR  = "H:/Desaka/Pincesobchod_SK"
DEFAULT_OUT_DIR = "H:/Desaka/Reports/Pincesobchod"


class _Tee:
    """Write to both a file and the original stdout."""
    def __init__(self, file_handle, original):
        self._file = file_handle
        self._orig = original

    def write(self, data):
        self._orig.write(data)
        self._file.write(data)

    def flush(self):
        self._orig.flush()
        self._file.flush()

    def fileno(self):
        return self._orig.fileno()


def parse_args():
    p = argparse.ArgumentParser(description="Pincesobchod CS vs SK comparison")
    p.add_argument('--cs-dir',     default=DEFAULT_CS_DIR)
    p.add_argument('--sk-dir',     default=DEFAULT_SK_DIR)
    p.add_argument('--output-dir', default=DEFAULT_OUT_DIR)
    return p.parse_args()


def main():
    args = parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    report_path = os.path.join(args.output_dir, f"comparison_{ts}.txt")

    original_stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    report_file     = open(report_path, 'w', encoding='utf-8')
    sys.stdout      = _Tee(report_file, original_stdout)

    try:
        _run(args)
    finally:
        report_file.close()
        sys.stdout = original_stdout
        print(f"\nReport uložen: {report_path}")


def _run(args):
    print(f"Pincesobchod comparison  —  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    print("Načítám CS JSON...")
    cs_products, _, cs_path = load_latest_json(args.cs_dir, "CS")
    print(f"  {cs_path}  ({len(cs_products)} produktů)")

    print("Načítám SK JSON...")
    sk_products, _, sk_path = load_latest_json(args.sk_dir, "SK")
    print(f"  {sk_path}  ({len(sk_products)} produktů)")

    shared_cs, shared_sk, cs_only, sk_only = match_by_catalog_number(cs_products, sk_products)
    print(f"\nSdílené: {len(shared_cs)}  |  jen CS: {len(cs_only)}  |  jen SK: {len(sk_only)}")

    brand_codes    = load_brand_codes()
    category_codes = load_category_codes()
    subcat_codes   = load_subcategory_codes()

    # ── CS-only checks ────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("CS-ONLY KONTROLY")
    print("=" * 60)

    r_duplicates = check_duplicate_codes(cs_products)
    print_duplicates_report(r_duplicates)

    r_categories = check_categories(cs_products, brand_codes, category_codes, subcat_codes)
    print_categories_report(r_categories)

    # ── CS vs SK checks ───────────────────────────────────────────────
    r_missing    = compare_missing_products.check_missing_products(cs_only, sk_only)
    r_visibility = compare_visibility.check_visibility(shared_cs, shared_sk)
    r_identity   = compare_identity.check_identity(shared_cs, shared_sk)
    r_variants   = compare_variants.check_variants(shared_cs, shared_sk, cs_products, sk_products)
    r_images     = compare_images.check_images(shared_cs, shared_sk)

    cs_a = len(r_missing['cs_only_active'])
    sk_a = len(r_missing['sk_only_active'])
    mismatch_total = (len(r_identity['manufacturer_mismatch']) +
                      len(r_identity['name_mismatch']))

    print("\n" + "=" * 60)
    print("CS vs SK — SOUHRN")
    print("=" * 60)
    print(f"Aktivní pouze v CS:           {cs_a}")
    print(f"Aktivní pouze v SK:           {sk_a}")
    print(f"Visibility/archive nesoulad:  {len(r_visibility)}")
    print(f"Různá identita produktu:      {mismatch_total}")
    print(f"Různý počet variant:          {len(r_variants['count_diffs'])}")
    print(f"Různý počet obrázků:          {len(r_images['count_diffs'])}")
    print(f"Různé soubory obrázků:        {len(r_images['file_diffs'])}")

    compare_missing_products.print_report(r_missing)
    compare_visibility.print_report(r_visibility)
    compare_identity.print_report(r_identity)
    compare_variants.print_report(r_variants)
    compare_images.print_report(r_images)

    # Exit code 1 if active discrepancies found
    active_cat_issues = len([r for r in r_categories['mismatches'] if r['active']])
    if cs_a > 0 or sk_a > 0 or mismatch_total > 0 or r_duplicates or active_cat_issues > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
