import csv
import re
from compare_utils import get_name, is_active

BRAND_CODE_LIST = "F:/Dropbox/Scripts/Python/Desaka/desaka_unifier/Memory/BrandCodeList.csv"
CATEGORY_CODE_LIST = "F:/Dropbox/Scripts/Python/Desaka/desaka_unifier/Memory/CategoryCodeList.csv"
CATEGORY_SUBCODE_LIST = "F:/Dropbox/Scripts/Python/Desaka/desaka_unifier/Memory/CategorySubCodeList.csv"

# Categories that use a subcode in positions 5-6 of the catalogNumber.
# Extend this set if subcoding is introduced for other categories.
SUBCODED_CATEGORIES = {'05'}


def load_brand_codes():
    """Returns dict: brand_code (3 letters) -> brand_name"""
    result = {}
    with open(BRAND_CODE_LIST, encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            result[row['VALUE'].strip()] = row['KEY'].strip()
    return result


def load_category_codes():
    """Returns dict: category_code (2 digits) -> category_name"""
    result = {}
    with open(CATEGORY_CODE_LIST, encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            result[row['VALUE'].strip()] = row['KEY'].strip()
    return result


def load_subcategory_codes():
    """Returns dict: subcode (2 digits) -> set of valid subcategory names"""
    result = {}
    with open(CATEGORY_SUBCODE_LIST, encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            code = row['VALUE'].strip()
            name = row['KEY'].strip()
            result.setdefault(code, set()).add(name)
    return result


def parse_catalog_number(cat_num, brand_codes):
    """
    Parses catalogNumber into (brand_code, cat_code, sub_code).
    Format: [Brand 3+][CatCode 2][SubCode 2][Sequential 4]
    SubCode is only meaningful for categories in SUBCODED_CATEGORIES.
    Returns (None, None, None) if not parseable or unknown brand.
    """
    if not cat_num:
        return None, None, None
    m = re.match(r'^([A-Za-z]+)(\d{2})(\d{2})\d{4}$', cat_num)
    if not m:
        return None, None, None
    brand_code = m.group(1).upper()
    cat_code = m.group(2)
    sub_code = m.group(3)
    if brand_code not in brand_codes:
        return None, None, None
    return brand_code, cat_code, sub_code


def get_actual_category_names(product):
    """Extract leaf category names from product's categories[].path"""
    names = set()
    for cat in (product.get('categories') or []):
        path = cat.get('path') or {}
        if path:
            names.add(list(path.values())[-1])
    return names


def check_categories(products, brand_codes, category_codes, subcategory_codes):
    mismatches = []
    unknown_brand = []
    unknown_cat_code = []
    unknown_sub_code = []

    # All valid leaf names for each top-level category code.
    # For subcoded categories the leaves come from subcategory_codes.
    # For non-subcoded categories the leaf IS the category name itself,
    # plus known subcategories observed in the data (Dřeva OFF, etc.).
    KNOWN_SUBCATS = {
        '01': {'Potahy', 'Softy', 'Softy OFF', 'Softy ALL', 'Softy DEF',
               'Antitopspiny', 'Trávy', 'Sendviče'},
        '02': {'Dřeva', 'Dřeva OFF', 'Dřeva ALL', 'Dřeva DEF'},
        '03': {'Míčky', 'Tréninkové', '*** I.T.T.F'},
        '04': {'Tašky a batohy', 'Tašky', 'Batohy', 'Kufry'},
        '11': {'Pouzdra', 'Na 1 pálku', 'Na 2 pálky', 'Kufříky'},
        '14': {'Pálky', 'Hotové pálky'},
    }

    for p in products:
        cat_num = p.get('catalogNumber') or ''
        brand_code, cat_code, sub_code = parse_catalog_number(cat_num, brand_codes)

        if brand_code is None:
            m = re.match(r'^([A-Za-z]+)', cat_num)
            if m and m.group(1).upper() not in brand_codes:
                unknown_brand.append({
                    'catalogNumber': cat_num,
                    'name': get_name(p),
                    'brand_prefix': m.group(1).upper(),
                    'active': is_active(p),
                })
            continue

        if cat_code not in category_codes:
            unknown_cat_code.append({
                'catalogNumber': cat_num,
                'name': get_name(p),
                'cat_code': cat_code,
                'active': is_active(p),
            })
            continue

        expected_category = category_codes[cat_code]
        if expected_category == 'Vyřadit':
            continue

        actual_cats = get_actual_category_names(p)
        if not actual_cats:
            continue

        if cat_code in SUBCODED_CATEGORIES:
            # sub_code 00 = no subcategory distinction, skip validation
            if sub_code == '00':
                continue
            # Validate subcode: sub_code must be in subcategory_codes
            if sub_code not in subcategory_codes:
                unknown_sub_code.append({
                    'catalogNumber': cat_num,
                    'name': get_name(p),
                    'sub_code': sub_code,
                    'active': is_active(p),
                })
                continue
            valid_subcat_names = subcategory_codes[sub_code]  # set of strings
            # At least one valid subcat name must appear in actual categories
            if not actual_cats.intersection(valid_subcat_names):
                mismatches.append({
                    'catalogNumber': cat_num,
                    'name': get_name(p),
                    'brand': brand_codes[brand_code],
                    'expected_category': expected_category,
                    'expected_subcat': sorted(valid_subcat_names)[0],
                    'actual_categories': sorted(actual_cats),
                    'active': is_active(p),
                })
        else:
            # No subcode: check that actual leaf is an accepted name for this cat_code
            accepted = KNOWN_SUBCATS.get(cat_code, {expected_category})
            if not actual_cats.intersection(accepted):
                mismatches.append({
                    'catalogNumber': cat_num,
                    'name': get_name(p),
                    'brand': brand_codes[brand_code],
                    'expected_category': expected_category,
                    'expected_subcat': None,
                    'actual_categories': sorted(actual_cats),
                    'active': is_active(p),
                })

    return {
        'mismatches': sorted(mismatches, key=lambda x: (not x['active'], x['catalogNumber'])),
        'unknown_brand': sorted(unknown_brand, key=lambda x: x['brand_prefix']),
        'unknown_cat_code': sorted(unknown_cat_code, key=lambda x: x['cat_code']),
        'unknown_sub_code': sorted(unknown_sub_code, key=lambda x: x['catalogNumber']),
    }


def check_duplicate_codes(products):
    """Find catalogNumbers that appear more than once."""
    from collections import defaultdict
    seen = defaultdict(list)
    for p in products:
        cat_num = p.get('catalogNumber')
        if cat_num:
            seen[cat_num].append({
                'name': get_name(p),
                'active': is_active(p),
            })
    duplicates = {k: v for k, v in seen.items() if len(v) > 1}
    return dict(sorted(duplicates.items()))


def print_duplicates_report(duplicates):
    print("\n" + "=" * 70)
    print(f"DUPLICITNÍ KÓDY  ({len(duplicates)} kódů)")
    print("=" * 70)
    if not duplicates:
        print("  Žádné duplikáty.")
        return
    active_dups = {k: v for k, v in duplicates.items() if any(p['active'] for p in v)}
    inactive_dups = {k: v for k, v in duplicates.items() if not any(p['active'] for p in v)}
    if active_dups:
        print(f"\nDuplikáty s alespoň jedním aktivním produktem ({len(active_dups)} ks):")
        for code, products in active_dups.items():
            print(f"  {code}")
            for p in products:
                flag = "AKTIVNÍ" if p['active'] else "neaktivní"
                print(f"    [{flag}]  {p['name'][:70]}")
    if inactive_dups:
        print(f"\nDuplikáty pouze neaktivních ({len(inactive_dups)} ks):")
        for code, products in inactive_dups.items():
            print(f"  {code}")
            for p in products:
                print(f"    [neaktivní]  {p['name'][:70]}")


def print_report(results):
    mismatches = results['mismatches']
    active = [r for r in mismatches if r['active']]
    inactive = [r for r in mismatches if not r['active']]

    print("\n" + "=" * 70)
    print("KÓD PRODUKTU NEODPOVÍDÁ KATEGORII")
    print("=" * 70)
    print(f"Celkem neshod:    {len(mismatches)}  (aktivních: {len(active)}, neaktivních: {len(inactive)})")
    if results['unknown_brand']:
        print(f"Neznámý brand:    {len(results['unknown_brand'])}")
    if results['unknown_cat_code']:
        print(f"Neznámý cat kód:  {len(results['unknown_cat_code'])}")
    if results['unknown_sub_code']:
        print(f"Neznámý sub kód:  {len(results['unknown_sub_code'])}")

    if active:
        print(f"\nAKTIVNÍ produkty s neshodou ({len(active)} ks):")
        for r in active:
            expected = (f"{r['expected_category']} › {r['expected_subcat']}"
                        if r['expected_subcat'] else r['expected_category'])
            print(f"  {r['catalogNumber']:<20s}  {r['name'][:60]}")
            print(f"    Kód říká:   {expected}")
            print(f"    Skutečnost: {', '.join(r['actual_categories'])}")

    if inactive:
        print(f"\nNeaktivní produkty s neshodou ({len(inactive)} ks):")
        for r in inactive:
            expected = (f"{r['expected_category']} › {r['expected_subcat']}"
                        if r['expected_subcat'] else r['expected_category'])
            print(f"  {r['catalogNumber']:<20s}  {r['name'][:60]}")
            print(f"    Kód říká:   {expected}")
            print(f"    Skutečnost: {', '.join(r['actual_categories'])}")

    if results['unknown_brand']:
        print(f"\nNeznámé brand prefixy:")
        for r in results['unknown_brand']:
            flag = "AKTIVNÍ" if r['active'] else "neaktivní"
            print(f"  [{flag}] {r['catalogNumber']:<20s} prefix={r['brand_prefix']}  {r['name'][:55]}")

    if results['unknown_cat_code']:
        print(f"\nNeznámé category kódy:")
        for r in results['unknown_cat_code']:
            print(f"  {r['catalogNumber']:<20s} kód={r['cat_code']}  {r['name'][:55]}")

    if results['unknown_sub_code']:
        print(f"\nNeznámé sub kódy (kategorie 05):")
        for r in results['unknown_sub_code']:
            flag = "AKTIVNÍ" if r['active'] else "neaktivní"
            print(f"  [{flag}] {r['catalogNumber']:<20s} sub={r['sub_code']}  {r['name'][:55]}")
