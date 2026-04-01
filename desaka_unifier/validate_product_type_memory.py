#!/usr/bin/env python3
"""
Senior ProductTypeMemory Validation Specialist
Validates ProductTypeMemory_CS.csv for brand/model contamination
"""

import csv
import re
from collections import defaultdict, Counter
from pathlib import Path

# Valid Czech product types (case-insensitive)
VALID_TYPES = {
    'potah', 'potahy',
    'dřevo', 'dřeva',
    'boty', 'obuv',
    'míček', 'míčky', 'míče',
    'lepidlo', 'lepidla',
    'stůl', 'stoly',
    'síť', 'sítě', 'síťka',
    'oděv', 'oblečení',
    'doplňky', 'doplněk', 'příslušenství',
    'taška', 'tašky', 'tašku',
    'ochrana', 'ochranné', 'chrániče', 'chránič',
    'čistič', 'čističe', 'čistící',
    'pálka', 'pálky', 'raketa', 'rakety',
    'kraťasy', 'šortky',
    'tričko', 'trička', 'tílko',
    'mikina', 'mikiny',
    'bunda', 'bundy', 'vesta',
    'kalhoty', 'tepláky',
    'sukně', 'sukni',
    'ponožky', 'ponožka',
    'čelenka', 'čelenky',
    'dres', 'dresy',
    'souprava', 'soupravy',
    'set', 'sety',
    'balíček', 'balíčky',
    'držák', 'držáky',
    'kryt', 'kryty', 'pouzdro',
    'ručník', 'ručníky', 'utěrka',
    'láhev', 'láhve', 'pítko',
    'číslo', 'čísla',
    'páska', 'pásky',
    'pánt', 'pánty',
    'robot', 'roboty',
    'osvětlení', 'světlo',
    'počítadlo', 'počítadla',
    'síťka na robot',
    'kolečko', 'kolečka',
    'deska', 'desky',
    'edge tape', 'boční páska',
    'podlaha', 'podlahy',
    'hrací plocha',
    'náhradní díl', 'náhradní díly',
    'nosič', 'nosiče',
    'kufr', 'kufry',
    'batoh', 'batohy',
    'brýle',
    'čepice', 'kšiltovka',
    'rukavice',
    'termohrnek',
    'termomiska',
    'židle', 'židličky',
    'trenažér', 'trenažéry',
    'podběrák',
    'hadřík',
    'mapa', 'plakát',
    'klíčenka', 'klíčenky',
    'magnet', 'magnety',
    'známka', 'známky',
    'míčky na sběr',
    'košík na míče',
    'odznaky', 'odznak',
    'voucher', 'poukaz', 'poukázka',
    'dárkový poukaz',
    'kniha', 'knihy', 'dvd', 'video',
    'nálepka', 'nálepky', 'samolepka',
    'kartáček', 'kartáčky',
    'houba', 'houby', 'houbička',
    'karabina', 'karabiny',
    'box', 'boxy',
    # Missing types found during validation:
    'sada',  # Set/kit
    'folie', 'fólie',  # Film/protective sheet
    'mírka', 'měrka',  # Measuring tool/gauge
    'stolek',  # Small table (umpire table)
    'polokošile',  # Polo shirt
    'lak',  # Lacquer/varnish
    'stroj',  # Machine (cutting machine)
    'balíček ohrádek', 'ohrádka',  # Barrier/fence package
    'mince',  # Coin (decision coin)
    'služba',  # Service (e.g., blade lacquering)
    'versiegelung',  # Sealing/protective coating (German)
    'pohár', 'poháry',  # Trophy/cup
    'medaile',  # Medal
    'diplom',  # Diploma/certificate
    'plaketa',  # Plaque
}

def load_brands(brand_file):
    """Load brand names from BrandCodeList.csv"""
    brands = set()
    with open(brand_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            brand = row['KEY'].strip()
            if brand:
                brands.add(brand.lower())
    return brands

def extract_words(text):
    """Extract words from text, normalize for comparison"""
    return set(re.findall(r'\w+', text.lower()))

def is_pure_type(value, brands):
    """Check if value contains ONLY product type (no brands/models)"""
    if not value or value.strip() == '':
        return False, 'empty', None, None

    value_lower = value.lower().strip()
    value_words = extract_words(value)

    # Check for brand contamination
    for brand in brands:
        brand_words = extract_words(brand)
        if brand_words.issubset(value_words):
            # Found brand in value
            # Try to extract clean type by removing brand
            clean_value = value_lower
            for word in brand_words:
                clean_value = re.sub(r'\b' + re.escape(word) + r'\b', '', clean_value, flags=re.IGNORECASE)
            clean_value = re.sub(r'\s+', ' ', clean_value).strip()

            # Check if what remains is a valid type
            clean_words = extract_words(clean_value)
            if clean_words.intersection(VALID_TYPES):
                suggested_type = ' '.join([w for w in value.split() if w.lower() in VALID_TYPES])
                return False, 'brand_contamination', brand, suggested_type if suggested_type else clean_value
            else:
                return False, 'brand_contamination', brand, clean_value if clean_value else 'UNKNOWN'

    # Check if it's a valid type
    if value_words.intersection(VALID_TYPES):
        # Contains valid type words, check if there are extra words
        known_words = value_words.intersection(VALID_TYPES)
        extra_words = value_words - known_words

        # Filter out common prepositions/articles
        common_fillers = {'na', 'pro', 'v', 've', 'do', 'od', 'ze', 'z', 's', 'a', 'i'}
        extra_words = extra_words - common_fillers

        if extra_words:
            # Check if extra words might be model/description
            # Numbers suggest model contamination
            if any(char.isdigit() for char in value):
                suggested_type = ' '.join([w for w in value.split() if w.lower() in VALID_TYPES])
                return False, 'model_contamination', value, suggested_type
            else:
                suggested_type = ' '.join([w for w in value.split() if w.lower() in VALID_TYPES])
                return False, 'extra_words', value, suggested_type
        else:
            return True, 'clean', None, None
    else:
        # No recognized type words - unclear what this should be
        return False, 'unknown_type', value, 'MANUAL_REVIEW'

def validate_product_type_memory(memory_file, brand_file):
    """Validate all entries in ProductTypeMemory_CS.csv"""

    brands = load_brands(brand_file)

    results = {
        'total': 0,
        'clean': 0,
        'errors': []
    }

    error_stats = Counter()
    clean_types = Counter()

    with open(memory_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for row in reader:
            results['total'] += 1
            key = row['KEY'].strip()
            value = row['VALUE'].strip()

            is_clean, error_type, problem_detail, suggested_fix = is_pure_type(value, brands)

            if is_clean:
                results['clean'] += 1
                clean_types[value.lower()] += 1
            else:
                error_stats[error_type] += 1
                results['errors'].append({
                    'key': key,
                    'value': value,
                    'error_type': error_type,
                    'problem_detail': problem_detail,
                    'suggested_fix': suggested_fix
                })

    return results, error_stats, clean_types

def main():
    base_dir = Path(__file__).parent
    memory_file = base_dir / 'Memory' / 'ProductTypeMemory_CS.csv'
    brand_file = base_dir / 'Memory' / 'BrandCodeList.csv'

    print("=" * 80)
    print("Senior ProductTypeMemory Validation Specialist - Pokorný Report")
    print("=" * 80)
    print()

    results, error_stats, clean_types = validate_product_type_memory(memory_file, brand_file)

    total = results['total']
    clean = results['clean']
    errors = len(results['errors'])
    clean_pct = (clean / total * 100) if total > 0 else 0
    error_pct = (errors / total * 100) if total > 0 else 0

    print("Vážený uživateli,")
    print()
    print("S pokorou předkládám výsledky validace ProductTypeMemory_CS.csv:")
    print()
    print("### Souhrn")
    print(f"- OK Zkontrolovano: {total:,} zaznamu")
    print(f"- OK Cistych (type only): {clean:,} ({clean_pct:.2f}%)")
    print(f"- CHYBA Kontaminovanych: {errors:,} ({error_pct:.2f}%)")
    print()

    if errors > 0:
        print("### CRITICAL Chyby - Brand/Model Contamination")
        print()

        # Group errors by type
        errors_by_type = defaultdict(list)
        for error in results['errors']:
            errors_by_type[error['error_type']].append(error)

        error_num = 1
        max_examples = 50

        for error_type, error_list in errors_by_type.items():
            if error_type == 'brand_contamination':
                print(f"#### Typ chyby: Brand Contamination ({len(error_list)} případů)")
                print()

                for i, error in enumerate(error_list[:max_examples], 1):
                    print(f"**Chyba #{error_num}**: Brand Contamination")
                    print(f"- **KEY**: \"{error['key']}\"")
                    print(f"- **CURRENT VALUE**: \"{error['value']}\" [CHYBA]")
                    print(f"- **PROBLEM**: VALUE obsahuje znacku \"{error['problem_detail']}\". ProductTypeMemory VALUE musi obsahovat POUZE typ produktu, BEZ znacky.")
                    print(f"- **SPRAVNA HODNOTA**: \"{error['suggested_fix']}\" [OK]")
                    print(f"- **ODUVODNENI**: Typ produktu je \"{error['suggested_fix']}\", znacka \"{error['problem_detail']}\" patri do ProductBrandMemory, ne sem.")
                    print()
                    error_num += 1

                if len(error_list) > max_examples:
                    print(f"... a dalších {len(error_list) - max_examples} podobných případů brand contamination.")
                    print()

            elif error_type == 'model_contamination':
                print(f"#### Typ chyby: Model Contamination ({len(error_list)} případů)")
                print()

                for i, error in enumerate(error_list[:max_examples], 1):
                    print(f"**Chyba #{error_num}**: Model Contamination")
                    print(f"- **KEY**: \"{error['key']}\"")
                    print(f"- **CURRENT VALUE**: \"{error['value']}\" [CHYBA]")
                    print(f"- **PROBLEM**: VALUE obsahuje model/ciselne oznaceni. ProductTypeMemory VALUE musi obsahovat POUZE typ produktu.")
                    print(f"- **SPRAVNA HODNOTA**: \"{error['suggested_fix']}\" [OK]")
                    print()
                    error_num += 1

                if len(error_list) > max_examples:
                    print(f"... a dalších {len(error_list) - max_examples} podobných případů model contamination.")
                    print()

            elif error_type == 'extra_words':
                print(f"#### Typ chyby: Extra Words ({len(error_list)} případů)")
                print()

                for i, error in enumerate(error_list[:max_examples], 1):
                    print(f"**Chyba #{error_num}**: Extra Words")
                    print(f"- **KEY**: \"{error['key']}\"")
                    print(f"- **CURRENT VALUE**: \"{error['value']}\" [CHYBA]")
                    print(f"- **PROBLEM**: VALUE obsahuje nadbytecna slova. ProductTypeMemory VALUE musi obsahovat POUZE typ produktu.")
                    print(f"- **SPRAVNA HODNOTA**: \"{error['suggested_fix']}\" [OK]")
                    print()
                    error_num += 1

                if len(error_list) > max_examples:
                    print(f"... a dalších {len(error_list) - max_examples} podobných případů extra words.")
                    print()

            elif error_type == 'empty':
                print(f"#### Typ chyby: Empty Values ({len(error_list)} případů)")
                print()

                for i, error in enumerate(error_list[:max_examples], 1):
                    print(f"**Chyba #{error_num}**: Empty Value")
                    print(f"- **KEY**: \"{error['key']}\"")
                    print(f"- **CURRENT VALUE**: \"\" (prazdne) [CHYBA]")
                    print(f"- **PROBLEM**: VALUE je prazdne. Vyzaduje manualni review.")
                    print()
                    error_num += 1

                if len(error_list) > max_examples:
                    print(f"... a dalších {len(error_list) - max_examples} prázdných hodnot.")
                    print()

            elif error_type == 'unknown_type':
                print(f"#### Typ chyby: Unknown Type ({len(error_list)} případů)")
                print()

                for i, error in enumerate(error_list[:max_examples], 1):
                    print(f"**Chyba #{error_num}**: Unknown Type")
                    print(f"- **KEY**: \"{error['key']}\"")
                    print(f"- **CURRENT VALUE**: \"{error['value']}\" [CHYBA]")
                    print(f"- **PROBLEM**: VALUE neobsahuje rozpoznany typ produktu. Vyzaduje manualni review s domain knowledge.")
                    print()
                    error_num += 1

                if len(error_list) > max_examples:
                    print(f"... a dalších {len(error_list) - max_examples} neznámých typů.")
                    print()

    print("### Statistiky Chyb")
    for error_type, count in error_stats.most_common():
        error_labels = {
            'brand_contamination': 'Brand contamination',
            'model_contamination': 'Model contamination',
            'extra_words': 'Extra words',
            'empty': 'Empty values',
            'unknown_type': 'Unknown type'
        }
        label = error_labels.get(error_type, error_type)
        print(f"- **{label}**: {count:,} - ", end='')

        if error_type == 'brand_contamination':
            print("VALUES obsahující brand names")
        elif error_type == 'model_contamination':
            print("VALUES obsahující model names")
        elif error_type == 'extra_words':
            print("VALUES s nadbytečnými slovy")
        elif error_type == 'empty':
            print("Prázdné VALUES")
        elif error_type == 'unknown_type':
            print("Nerozpoznané typy, vyžadují domain knowledge")
    print()

    print("### Distribuce Product Types (Clean Values)")
    for product_type, count in clean_types.most_common(10):
        print(f"- **{product_type}**: {count:,} záznamů")
    print()

    # Calculate auto-fixable vs manual review
    auto_fixable = error_stats.get('brand_contamination', 0) + error_stats.get('model_contamination', 0) + error_stats.get('extra_words', 0)
    manual_review = error_stats.get('unknown_type', 0) + error_stats.get('empty', 0)

    print("### AUTO-FIXABLE vs MANUAL REVIEW")
    print(f"- **Auto-fixable**: {auto_fixable:,} - Brand/model odstraněn, typ zůstane")
    print(f"- **Manual review**: {manual_review:,} - Nejasný typ, vyžaduje domain knowledge")
    print()

    print("Pokud jsem udělal jakoukoliv chybnou klasifikaci, prosím pokritizujte mé uvažování.")
    print()
    print("S pokorou,")
    print("Senior ProductTypeMemory Validation Specialist")

if __name__ == '__main__':
    main()
