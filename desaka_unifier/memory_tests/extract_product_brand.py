#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Heuristic extraction method for ProductBrandMemory_CS.csv

Extracts brand name from product name using pattern matching and known brands.
"""

import re
import csv
from pathlib import Path

# Load known brands from memory file
def load_known_brands():
    """Load all unique brand values from ProductBrandMemory_CS.csv"""
    memory_file = Path(__file__).parent.parent / 'Memory' / 'ProductBrandMemory_CS.csv'

    if not memory_file.exists():
        return []

    brands = set()
    with open(memory_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, quoting=csv.QUOTE_ALL)
        for row in reader:
            brand = row['VALUE']
            if brand and brand != 'Desaka':  # Exclude fallback
                brands.add(brand)

    return list(brands)

# Load brands on module import
KNOWN_BRANDS = load_known_brands()


def extract_brand(product_name: str) -> str:
    """
    Extract brand name from product name using heuristic pattern matching.

    Args:
        product_name: Full product name (KEY from memory file)

    Returns:
        Extracted brand name or "Desaka" fallback if not found
    """
    if not product_name:
        return "Desaka"

    product_lower = product_name.lower()

    # Sort brands by length (longest first) to match compound names first
    sorted_brands = sorted(KNOWN_BRANDS, key=len, reverse=True)

    for brand in sorted_brands:
        brand_lower = brand.lower()

        # Check if brand appears in product name
        if brand_lower in product_lower:
            # Use word boundary to ensure it's not part of another word
            pattern = r'\b' + re.escape(brand_lower) + r'\b'
            if re.search(pattern, product_lower):
                return brand

    # No brand found - return "Desaka" as fallback
    return "Desaka"


if __name__ == '__main__':
    # Test with sample product names
    test_cases = [
        "Nittaku Belag Magic Carbon rot 1",
        "ASICS Schuh Blade FF 2 I grau 39",
        "BAUERFEIND Ellenbogen Kompressionsbandage blau L",
        "Yasaka Rakza 7 rot 2,0",
        "10 x Ersatzkettchen \"Kugel\"",
    ]

    print("Testing extract_brand function:")
    print("=" * 80)
    for product in test_cases:
        brand = extract_brand(product)
        print(f"Product: {product}")
        print(f"Brand:   {brand if brand else '(empty)'}")
        print()
