#!/usr/bin/env python3
"""
Senior ProductBrandMemory Validation Specialist
Validates ProductBrandMemory_CS.csv against BrandCodeList.csv

Based on: .claude/skills/12-memory-validation/senior-product-brand-memory-validator.md
"""
import csv
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

# File paths
BASE_DIR = Path(r"F:\Dropbox\Scripts\Python\Desaka\desaka_unifier\Memory")
BRAND_CODE_LIST = BASE_DIR / "BrandCodeList.csv"
PRODUCT_BRAND_MEMORY = BASE_DIR / "ProductBrandMemory_CS.csv"

# Known non-brand patterns (from skill definition)
QUANTITY_PATTERNS = [
    r'^\d+$',                           # Just numbers: "2", "10"
    r'\d+\s*(ks|Stück|stück|pieces?)',  # Quantities: "1 Stück", "12 ks"
    r'^\d+er\s+Set$',                   # German sets: "3er Set"
]

PHRASE_PATTERNS = [
    r'alle\s+Systeme',     # German "all systems"
    r'ohne\s+Druck',       # German "without printing"
    r'leer',               # German "empty"
]

ADJECTIVE_PATTERNS = [
    r'Anatomický',         # Czech "anatomical"
    r'anatomický',
    r'Classic',
    r'Standard',
]

PRODUCT_TYPE_PATTERNS = [
    r'^Potah$',            # Czech product types
    r'^Dřevo$',
    r'^Boty$',
    r'^Míček$',
    r'^Taktiky$',
    r'^Sada\s+Pálek',      # "Paddle Set"
]


class BrandValidator:
    """Senior ProductBrandMemory Validation Specialist"""

    def __init__(self):
        self.valid_brands: Set[str] = set()
        self.brand_codes: Dict[str, str] = {}  # brand_name -> code
        self.errors: List[Dict] = []
        self.error_types: Dict[str, int] = defaultdict(int)
        self.total_count = 0
        self.valid_count = 0

    def load_brand_code_list(self) -> None:
        """Load valid brands from BrandCodeList.csv"""
        print("Reading BrandCodeList.csv...")
        with open(BRAND_CODE_LIST, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                brand_name = row['KEY'].strip()
                brand_code = row['VALUE'].strip()
                self.valid_brands.add(brand_name)
                self.brand_codes[brand_name] = brand_code

        print(f"[OK] Loaded {len(self.valid_brands)} valid brands from BrandCodeList.csv")
        print(f"     Brand names: {', '.join(sorted(list(self.valid_brands)[:10]))}... (showing first 10)")
        print()

    def is_non_brand_value(self, value: str) -> Tuple[bool, str]:
        """
        Check if VALUE is a non-brand value (quantity, phrase, adjective, etc.)
        Returns: (is_non_brand, error_type)
        """
        # Check quantities
        for pattern in QUANTITY_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True, "Non-brand: Quantity/Number"

        # Check phrases
        for pattern in PHRASE_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True, "Non-brand: Phrase"

        # Check adjectives
        for pattern in ADJECTIVE_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True, "Non-brand: Adjective"

        # Check product types
        for pattern in PRODUCT_TYPE_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True, "Non-brand: Product Type"

        return False, ""

    def extract_brand_from_key(self, key: str) -> str:
        """
        Try to extract brand from KEY by checking if any valid brand appears in it
        Strategy: Find the FIRST brand that appears in KEY (case-insensitive)
        """
        key_upper = key.upper()

        # Sort brands by length (longest first) to match longer names first
        # e.g., "Der Materialspezialist" before "Der"
        sorted_brands = sorted(self.valid_brands, key=len, reverse=True)

        for brand in sorted_brands:
            # Check if brand appears as whole word in KEY
            if re.search(r'\b' + re.escape(brand) + r'\b', key, re.IGNORECASE):
                return brand

        return None

    def validate_entry(self, key: str, value: str, row_num: int) -> None:
        """Validate a single ProductBrandMemory entry"""
        self.total_count += 1

        # Check for empty values
        if not value:
            self.error_types['Empty values'] += 1
            self.errors.append({
                'row': row_num,
                'type': 'Empty Value',
                'key': key,
                'value': value,
                'problem': 'VALUE je prázdný',
                'suggestion': 'MANUAL_REVIEW',
                'reasoning': 'Nelze automaticky určit správnou značku z KEY. Je třeba doménová znalost.'
            })
            return

        # Check if VALUE is in valid brands (exact match)
        if value in self.valid_brands:
            self.valid_count += 1
            return

        # Not in valid brands - determine error type

        # 1. Check for non-brand values (most common)
        is_non_brand, error_type = self.is_non_brand_value(value)
        if is_non_brand:
            self.error_types[error_type] += 1

            # Try to extract brand from KEY
            suggested_brand = self.extract_brand_from_key(key)

            if error_type == "Non-brand: Quantity/Number":
                problem = f'"{value}" není značka, ale množství/číslo. BrandCodeList.csv neobsahuje tuto hodnotu.'
            elif error_type == "Non-brand: Phrase":
                problem = f'"{value}" není značka, ale fráze. BrandCodeList.csv neobsahuje tuto hodnotu.'
            elif error_type == "Non-brand: Adjective":
                problem = f'"{value}" není značka, ale adjektivum/přídavné jméno. BrandCodeList.csv neobsahuje tuto hodnotu.'
            elif error_type == "Non-brand: Product Type":
                problem = f'"{value}" není značka, ale typ produktu. BrandCodeList.csv neobsahuje tuto hodnotu.'
            else:
                problem = f'"{value}" není platná značka.'

            self.errors.append({
                'row': row_num,
                'type': error_type,
                'key': key,
                'value': value,
                'problem': problem,
                'suggestion': suggested_brand if suggested_brand else 'MANUAL_REVIEW',
                'reasoning': self._get_reasoning(suggested_brand, key)
            })
            return

        # 2. Check for case mismatch
        for brand in self.valid_brands:
            if value.lower() == brand.lower():
                self.error_types['Case mismatch'] += 1
                self.errors.append({
                    'row': row_num,
                    'type': 'Case Mismatch',
                    'key': key,
                    'value': value,
                    'problem': f'"{value}" má špatnou kapitalizaci. Správná forma je "{brand}".',
                    'suggestion': brand,
                    'reasoning': f'Značka "{brand}" existuje v BrandCodeList.csv s touto kapitalizací.'
                })
                return

        # 3. Invalid brand (not in BrandCodeList)
        self.error_types['Invalid brand (not in BrandCodeList)'] += 1

        # Try to extract brand from KEY
        suggested_brand = self.extract_brand_from_key(key)

        self.errors.append({
            'row': row_num,
            'type': 'Invalid Brand',
            'key': key,
            'value': value,
            'problem': f'"{value}" není v BrandCodeList.csv. Tato značka není v seznamu {len(self.valid_brands)} platných značek.',
            'suggestion': suggested_brand if suggested_brand else 'MANUAL_REVIEW',
            'reasoning': self._get_reasoning(suggested_brand, key)
        })

    def _get_reasoning(self, suggested_brand: str, key: str) -> str:
        """Generate reasoning for suggestion"""
        if suggested_brand:
            brand_code = self.brand_codes.get(suggested_brand, '?')
            return f'Značka "{suggested_brand}" (kód {brand_code}) je v BrandCodeList.csv a vyskytuje se v KEY produktu: "{key}"'
        else:
            return 'Nelze automaticky určit správnou značku z KEY. Je třeba doménová znalost stolního tenisu.'

    def validate_all(self) -> None:
        """Validate all entries in ProductBrandMemory_CS.csv"""
        print(f"Validating ProductBrandMemory_CS.csv...")
        print(f"File: {PRODUCT_BRAND_MEMORY}")
        print()

        with open(PRODUCT_BRAND_MEMORY, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (skip header)
                key = row['KEY'].strip()
                value = row['VALUE'].strip()
                self.validate_entry(key, value, row_num)

        print(f"[OK] Validated {self.total_count:,} entries\n")

    def generate_report(self) -> None:
        """Generate validation report in Czech (submissive tone)"""
        print("=" * 80)
        print("## Senior ProductBrandMemory Validation Specialist - Pokorný Report")
        print("=" * 80)
        print()
        print("Vážený uživateli,\n")
        print("S pokorou předkládám výsledky validace ProductBrandMemory_CS.csv:\n")

        # Summary
        print("### Souhrn")
        print(f"- [OK] Zkontrolovano: {self.total_count:,} zaznamu")
        print(f"- [OK] Spravnych: {self.valid_count:,} ({self.valid_count/self.total_count*100:.2f}%)")
        print(f"- [ERROR] Chybnych: {len(self.errors):,} ({len(self.errors)/self.total_count*100:.2f}%)")
        print()

        if not self.errors:
            print("[SUCCESS] Zadne chyby nebyly nalezeny! Vsechny zaznamy jsou platne.\n")
            print("S pokorou,")
            print("Senior ProductBrandMemory Validation Specialist")
            print("=" * 80)
            return

        # Detailed errors (first 50)
        print("### CRITICAL Chyby - Neplatné Značky\n")

        max_detailed = min(50, len(self.errors))
        for i, error in enumerate(self.errors[:max_detailed], 1):
            print(f"#### Chyba #{i}: {error['type']}")
            print(f"- **ROW**: {error['row']}")
            print(f"- **KEY**: \"{error['key'][:100]}{'...' if len(error['key']) > 100 else ''}\"")
            print(f"- **CURRENT VALUE**: \"{error['value']}\" ❌")
            print(f"- **PROBLÉM**: {error['problem']}")

            if error['suggestion'] == 'MANUAL_REVIEW':
                print(f"- **SPRÁVNÁ HODNOTA**: Vyžaduje manuální review")
            else:
                print(f"- **SPRÁVNÁ HODNOTA**: \"{error['suggestion']}\" ✅")

            print(f"- **ODŮVODNĚNÍ**: {error['reasoning']}")
            print()

        if len(self.errors) > max_detailed:
            print(f"... a dalších {len(self.errors) - max_detailed:,} chyb (celkem {len(self.errors):,} chyb)\n")

        # Error statistics
        print("### Statistiky Chyb")
        for error_type, count in sorted(self.error_types.items(), key=lambda x: x[1], reverse=True):
            print(f"- **{error_type}**: {count:,}")

        # Auto-fixable vs manual review
        auto_fixable = sum(1 for e in self.errors if e['suggestion'] != 'MANUAL_REVIEW')
        manual_review = len(self.errors) - auto_fixable

        print(f"\n### AUTO-FIXABLE vs MANUAL REVIEW")
        print(f"- **Auto-fixable**: {auto_fixable:,} - Clear brand extractable from KEY")
        print(f"- **Manual review**: {manual_review:,} - Requires domain knowledge")

        print("\nPokud jsem udělal jakoukoliv chybnou klasifikaci, prosím pokritizujte mé uvažování.\n")
        print("S pokorou,")
        print("Senior ProductBrandMemory Validation Specialist")
        print("=" * 80)

    def save_errors_to_csv(self) -> None:
        """Save errors to CSV for further processing"""
        if not self.errors:
            return

        error_file = Path(r"F:\Dropbox\Scripts\Python\Desaka\ProductBrandMemory_ValidationErrors.csv")
        with open(error_file, 'w', encoding='utf-8-sig', newline='') as f:
            fieldnames = ['row', 'type', 'key', 'value', 'problem', 'suggestion', 'reasoning']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.errors)

        print(f"\n[SAVE] Errors exported to: {error_file}")


def main():
    """Main validation routine"""
    validator = BrandValidator()

    # Step 1: Load valid brands
    validator.load_brand_code_list()

    # Step 2: Validate all entries
    validator.validate_all()

    # Step 3: Generate report
    validator.generate_report()

    # Step 4: Save errors to CSV
    validator.save_errors_to_csv()


if __name__ == "__main__":
    main()
