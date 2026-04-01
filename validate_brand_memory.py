#!/usr/bin/env python3
"""
Validate ProductBrandMemory_CS.csv against BrandCodeList.csv
Senior ProductBrandMemory Validation Specialist
"""
import csv
from pathlib import Path
from collections import defaultdict

# File paths
BRAND_CODE_LIST = r"F:\Dropbox\Scripts\Python\Desaka\desaka_unifier\Memory\BrandCodeList.csv"
PRODUCT_BRAND_MEMORY = r"F:\Dropbox\Scripts\Python\Desaka\desaka_unifier\Memory\ProductBrandMemory_CS.csv"

# Read valid brands from BrandCodeList.csv
valid_brands = set()
brand_codes = {}  # Map brand name to code for reference

print("Reading BrandCodeList.csv...")
with open(BRAND_CODE_LIST, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        brand_name = row['KEY'].strip()
        brand_code = row['VALUE'].strip()
        valid_brands.add(brand_code)
        brand_codes[brand_name] = brand_code

print(f"✓ Loaded {len(valid_brands)} valid brand codes from BrandCodeList.csv")
print(f"  Valid brands: {sorted(valid_brands)}\n")

# Validate ProductBrandMemory_CS.csv
errors = []
error_types = defaultdict(int)
total_count = 0
valid_count = 0

# Known non-brand patterns
QUANTITY_PATTERNS = ['Stück', 'stück', 'ks', 'pcs']
PHRASE_PATTERNS = ['alle Systeme', 'all systems', 'various']
ADJECTIVE_PATTERNS = ['Anatomický', 'anatomický', 'Classic', 'Standard']

print("Validating ProductBrandMemory_CS.csv...")
with open(PRODUCT_BRAND_MEMORY, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        total_count += 1
        key = row['KEY'].strip()
        value = row['VALUE'].strip()

        # Check for empty values
        if not value:
            error_types['Empty values'] += 1
            errors.append({
                'type': 'Empty Value',
                'key': key,
                'value': value,
                'problem': 'VALUE je prázdný',
                'suggestion': 'Potřebuje manuální review pro určení správné značky'
            })
            continue

        # Check if VALUE is in valid brands
        if value not in valid_brands:
            # Detect error type
            error_type = None
            problem = None
            suggestion = None

            # Check for quantities (e.g., "1 Stück", "2 Stück")
            if any(pattern in value for pattern in QUANTITY_PATTERNS):
                error_type = 'Quantity (not brand)'
                error_types['Non-brand: quantities'] += 1
                problem = f'"{value}" není značka, ale množství/jednotka. BrandCodeList.csv neobsahuje tuto hodnotu.'
                # Try to extract brand from KEY
                for brand_name in brand_codes.keys():
                    if brand_name.lower() in key.lower():
                        suggestion = brand_codes[brand_name]
                        break
                if not suggestion:
                    suggestion = 'MANUAL_REVIEW'

            # Check for German phrases
            elif any(pattern in value for pattern in PHRASE_PATTERNS):
                error_type = 'Phrase (not brand)'
                error_types['Non-brand: phrases'] += 1
                problem = f'"{value}" není značka, ale fráze. BrandCodeList.csv neobsahuje tuto hodnotu.'
                # Try to extract brand from KEY
                for brand_name in brand_codes.keys():
                    if brand_name.lower() in key.lower():
                        suggestion = brand_codes[brand_name]
                        break
                if not suggestion:
                    suggestion = 'MANUAL_REVIEW'

            # Check for adjectives
            elif any(pattern in value for pattern in ADJECTIVE_PATTERNS):
                error_type = 'Adjective (not brand)'
                error_types['Non-brand: adjectives'] += 1
                problem = f'"{value}" není značka, ale adjektivum/přídavné jméno. BrandCodeList.csv neobsahuje tuto hodnotu.'
                # Try to extract brand from KEY
                for brand_name in brand_codes.keys():
                    if brand_name.lower() in key.lower():
                        suggestion = brand_codes[brand_name]
                        break
                if not suggestion:
                    suggestion = 'MANUAL_REVIEW'

            # Invalid brand (not in BrandCodeList)
            else:
                error_type = 'Invalid Brand'
                error_types['Invalid brands (not in BrandCodeList)'] += 1
                problem = f'"{value}" není v BrandCodeList.csv. Tato značka není v seznamu 83 platných značek.'
                # Try to find similar brand
                value_lower = value.lower()
                for brand_name, brand_code in brand_codes.items():
                    if value_lower in brand_name.lower() or brand_name.lower() in value_lower:
                        suggestion = brand_code
                        break
                if not suggestion:
                    # Try to extract brand from KEY
                    for brand_name in brand_codes.keys():
                        if brand_name.lower() in key.lower():
                            suggestion = brand_codes[brand_name]
                            break
                if not suggestion:
                    suggestion = 'MANUAL_REVIEW'

            errors.append({
                'type': error_type,
                'key': key,
                'value': value,
                'problem': problem,
                'suggestion': suggestion
            })
        else:
            valid_count += 1

print(f"✓ Validated {total_count} entries\n")

# Generate report
print("=" * 80)
print("## Senior ProductBrandMemory Validation Specialist - Pokorný Report")
print("=" * 80)
print("\nVážený uživateli,\n")
print("S pokorou předkládám výsledky validace ProductBrandMemory_CS.csv:\n")

print("### Souhrn")
print(f"- ✅ Zkontrolováno: {total_count:,} záznamů")
print(f"- ✅ Správných: {valid_count:,} ({valid_count/total_count*100:.2f}%)")
print(f"- ❌ Chybných: {len(errors):,} ({len(errors)/total_count*100:.2f}%)\n")

if errors:
    print("### CRITICAL Chyby - Neplatné Značky\n")

    # Show first 50 errors in detail
    max_detailed = min(50, len(errors))
    for i, error in enumerate(errors[:max_detailed], 1):
        print(f"#### Chyba #{i}: {error['type']}")
        print(f"- **KEY**: \"{error['key']}\"")
        print(f"- **CURRENT VALUE**: \"{error['value']}\" ❌")
        print(f"- **PROBLÉM**: {error['problem']}")

        if error['suggestion'] == 'MANUAL_REVIEW':
            print(f"- **SPRÁVNÁ HODNOTA**: Vyžaduje manuální review")
            print(f"- **ODŮVODNĚNÍ**: Nelze automaticky určit správnou značku z KEY. Je třeba doménová znalost stolního tenisu.")
        else:
            # Find brand name for the code
            brand_name = None
            for name, code in brand_codes.items():
                if code == error['suggestion']:
                    brand_name = name
                    break

            print(f"- **SPRÁVNÁ HODNOTA**: \"{error['suggestion']}\" ✅")
            if brand_name:
                print(f"- **ODŮVODNĚNÍ**: Značka \"{brand_name}\" (kód {error['suggestion']}) je v BrandCodeList.csv a vyskytuje se v KEY produktu.")
            else:
                print(f"- **ODŮVODNĚNÍ**: Kód {error['suggestion']} je platný v BrandCodeList.csv.")
        print()

    if len(errors) > max_detailed:
        print(f"... a dalších {len(errors) - max_detailed} chyb (celkem {len(errors)} chyb)\n")

    print("### Statistiky Chyb")
    for error_type, count in sorted(error_types.items()):
        print(f"- **{error_type}**: {count:,}")

    # Count auto-fixable vs manual review
    auto_fixable = sum(1 for e in errors if e['suggestion'] != 'MANUAL_REVIEW')
    manual_review = len(errors) - auto_fixable

    print(f"\n### AUTO-FIXABLE vs MANUAL REVIEW")
    print(f"- **Auto-fixable**: {auto_fixable:,} - Clear brand extractable from KEY")
    print(f"- **Manual review**: {manual_review:,} - Requires domain knowledge")
else:
    print("✅ Žádné chyby nebyly nalezeny! Všechny záznamy jsou platné.")

print("\nPokud jsem udělal jakoukoliv chybnou klasifikaci, prosím pokritizujte mé uvažování.\n")
print("S pokorou,")
print("Senior ProductBrandMemory Validation Specialist")
print("=" * 80)

# Save errors to CSV for further processing
if errors:
    error_file = r"F:\Dropbox\Scripts\Python\Desaka\ProductBrandMemory_ValidationErrors.csv"
    with open(error_file, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['type', 'key', 'value', 'problem', 'suggestion'])
        writer.writeheader()
        writer.writerows(errors)
    print(f"\n✓ Errors exported to: {error_file}")
