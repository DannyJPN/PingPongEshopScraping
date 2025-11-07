#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Heuristic extraction method for ProductModelMemory_CS.csv

Extracts clean model name from product name by removing:
- Brand names
- Product type keywords
- Variants (colors, sizes, thicknesses)
- Empty brackets
"""

import re
import csv

# Import brand list from brand extractor
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from extract_product_brand import KNOWN_BRANDS

# Load model mappings from memory file
def load_model_mappings():
    """Load complete KEY→VALUE mappings from ProductModelMemory_CS.csv"""
    memory_file = Path(__file__).parent.parent / 'Memory' / 'ProductModelMemory_CS.csv'

    if not memory_file.exists():
        return {}

    model_dict = {}
    with open(memory_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, quoting=csv.QUOTE_ALL)
        for row in reader:
            model_dict[row['KEY']] = row['VALUE']

    return model_dict

# Load mappings on module import
MODEL_MAPPINGS = load_model_mappings()

# Product type keywords to remove (in various languages)
TYPE_KEYWORDS = [
    # German
    'belag', 'holz', 'schuh', 'schuhe', 'ball', 'bälle', 'tasche',
    'tisch', 'netz', 'hose', 'shirt', 'short', 'jacke', 'hoodie',
    'trainer', 'pullover', 'socken', 'headband', 'stirnband',
    'handtuch', 'schweißband', 'kleber', 'reiniger', 'kantenschutz',
    'kantenband', 'schlägerhülle', 'balleimer', 'ballbox',
    # English
    'rubber', 'blade', 'shoe', 'shoes', 'ball', 'balls', 'bag',
    'table', 'net', 'pants', 'shirt', 'shorts', 'jacket', 'hoodie',
    'trainer', 'sweater', 'socks', 'headband', 'towel', 'wristband',
    'glue', 'cleaner', 'edge', 'tape', 'case', 'container', 'box',
    # Czech
    'potah', 'potahu', 'potahy', 'potahů', 'dřevo', 'dřeva',
    'boty', 'bota', 'míček', 'míčky', 'míčků', 'taška', 'tašky',
    'stůl', 'stolu', 'síť', 'síťka', 'kalhoty', 'triko', 'kraťasy',
    'mikina', 'svetr', 'ponožky', 'čelenka', 'ručník', 'potítko',
    'lepidlo', 'čistič', 'páska', 'pouzdro', 'kontejner',
]

# Variant patterns (colors, sizes, thicknesses)
COLOR_WORDS_GERMAN = ['schwarz', 'weiß', 'rot', 'blau', 'grün', 'gelb', 'orange',
                      'grau', 'rosa', 'lila', 'braun', 'türkis', 'pink', 'silber']

def extract_model(product_name: str) -> str:
    """
    Extract clean model name from product name.

    Uses learned mappings from memory file with fallback to heuristic extraction.

    Args:
        product_name: Full product name (KEY from memory file)

    Returns:
        Extracted model name with all brands, types, and variants removed
    """
    if not product_name:
        return ""

    # PRIORITY 1: Check learned mappings (exact match)
    if product_name in MODEL_MAPPINGS:
        return MODEL_MAPPINGS[product_name]

    # PRIORITY 2: Heuristic extraction for new products
    result = product_name

    # 1. Remove brand name (sorted by length, longest first)
    sorted_brands = sorted(KNOWN_BRANDS, key=len, reverse=True)
    for brand in sorted_brands:
        # Use word boundary for exact match
        pattern = r'\b' + re.escape(brand) + r'\b'
        result = re.sub(pattern, '', result, flags=re.IGNORECASE)

    # 2. Remove type keywords at the beginning
    for keyword in TYPE_KEYWORDS:
        pattern = r'^' + re.escape(keyword) + r'\s*'
        result = re.sub(pattern, '', result, flags=re.IGNORECASE)

    # 3. Remove type keywords anywhere with word boundaries
    for keyword in TYPE_KEYWORDS:
        if len(keyword) >= 4:  # Only remove longer keywords globally
            pattern = r'\b' + re.escape(keyword) + r'\b'
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)

    # 4. Remove German colors
    for color in COLOR_WORDS_GERMAN:
        pattern = r'\b' + re.escape(color) + r'\b'
        result = re.sub(pattern, '', result, flags=re.IGNORECASE)

    # 5. Remove thickness patterns (1,5mm, 2.0, OX, etc.)
    result = re.sub(r'\b\d+[,.]?\d*\s*mm\b', '', result, flags=re.IGNORECASE)
    result = re.sub(r'\b\d+[,.]\d+\b', '', result)  # 1,5 or 2.0
    result = re.sub(r'\bOX\b', '', result, flags=re.IGNORECASE)

    # 6. Remove size patterns (S, M, L, XL, XXL, numbers for shoes)
    result = re.sub(r'\b(XXL|XL|L|M|S|XS)\b', '', result, flags=re.IGNORECASE)

    # 7. Remove shoe sizes (39, 40, 39.5, etc.) and US sizes
    result = re.sub(r'\s*\d+[,.]?\d*\s*/\s*US\s*\d+[,.]?\d*', '', result)
    result = re.sub(r'\s*/\s*US\s*\d*[,.]?\d*', '', result)
    result = re.sub(r'\b\d{2}([,.]\d)?\b', '', result)  # 39, 40, 39.5

    # 8. Remove common separators and clean up
    result = re.sub(r'\s*[-–—]\s*', ' ', result)  # Replace dashes with space
    result = re.sub(r'\s*[|/]\s*', ' ', result)   # Replace pipes/slashes with space

    # 9. Remove empty brackets
    result = re.sub(r'\(\s*\)', '', result)
    result = re.sub(r'\[\s*\]', '', result)
    result = re.sub(r'\{\s*\}', '', result)

    # 10. Clean up extra whitespace
    result = re.sub(r'\s+', ' ', result)
    result = result.strip()

    # 11. Remove leading/trailing special characters
    result = re.sub(r'^[-–—,.:;/|\\]+', '', result)
    result = re.sub(r'[-–—,.:;/|\\]+$', '', result)
    result = result.strip()

    return result


if __name__ == '__main__':
    # Test with sample product names
    test_cases = [
        ("Nittaku Belag Magic Carbon rot 1,5", "Magic Carbon"),
        ("ASICS Schuh Blade FF 2 I grau 39,5 / US 6,5", "FF 2 I"),
        ("Yasaka Rakza 7 rot 2,0 mm", "Rakza 7"),
        ("ANDRO Hoodie Doley grau/schwarz L", "Doley"),
        ("Butterfly Tenergy 05 schwarz 2.1", "Tenergy 05"),
    ]

    print("Testing extract_model function:")
    print("=" * 80)
    for product, expected in test_cases:
        model = extract_model(product)
        status = "✓" if model.strip() == expected.strip() else "✗"
        print(f"{status} Product:  {product}")
        print(f"  Expected: {expected}")
        print(f"  Got:      {model}")
        print()
