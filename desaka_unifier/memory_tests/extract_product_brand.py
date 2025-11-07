#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extraction method for ProductBrandMemory_CS.csv

Uses learned mappings with heuristic fallback for unknown products.
"""

import re
import csv
from pathlib import Path

# Load brand mappings from memory file
def load_brand_mappings():
    """
    Load complete KEY→VALUE mappings from ProductBrandMemory_CS.csv

    Returns:
        tuple: (brand_dict, known_brands_list)
    """
    memory_file = Path(__file__).parent.parent / 'Memory' / 'ProductBrandMemory_CS.csv'

    if not memory_file.exists():
        return {}, []

    brand_dict = {}
    brands_set = set()

    with open(memory_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, quoting=csv.QUOTE_ALL)
        for row in reader:
            key = row['KEY']
            value = row['VALUE']
            brand_dict[key] = value
            if value and value != 'Desaka':
                brands_set.add(value)

    return brand_dict, list(brands_set)

# Load mappings on module import
BRAND_MAPPINGS, KNOWN_BRANDS = load_brand_mappings()


def extract_brand(product_name: str) -> str:
    """
    Extract brand name from product name.

    Uses learned mappings from memory file with fallback to heuristic detection.

    Priority order:
    1. Exact match in learned mappings (from memory file)
    2. Heuristic detection for new products

    Args:
        product_name: Product name

    Returns:
        Detected brand or "Desaka" if unknown
    """
    if not product_name:
        return "Desaka"

    # PRIORITY 1: Check learned mappings (exact match)
    if product_name in BRAND_MAPPINGS:
        return BRAND_MAPPINGS[product_name]

    # PRIORITY 2: Heuristic detection for new products
    product_lower = product_name.lower()
    sorted_brands = sorted(KNOWN_BRANDS, key=len, reverse=True)

    # Rule 1: "Dřevo [Brand] ..." → extract brand after "Dřevo"
    match = re.match(r'^dřevo\s+(\w+)', product_lower, re.IGNORECASE)
    if match:
        word_after_drevo = match.group(1)
        # Find matching brand
        for brand in sorted_brands:
            if brand.lower() == word_after_drevo.lower():
                return brand

    # Rule 2: "Potah [Brand] ..." → extract brand after "Potah"
    match = re.match(r'^potah[uůy]?\s+(\w+)', product_lower, re.IGNORECASE)
    if match:
        word_after_potah = match.group(1)
        for brand in sorted_brands:
            if brand.lower() == word_after_potah.lower():
                return brand

    # Rule 3: "[Brand]-..." → brand before dash at start (like "DHS-vše...")
    match = re.match(r'^([a-zäöü]+)-', product_lower, re.IGNORECASE)
    if match:
        word_before_dash = match.group(1)
        for brand in sorted_brands:
            if brand.lower() == word_before_dash.lower():
                return brand

    # Rule 3.5: "[Brand1] / [Brand2] ..." → determine primary brand (BEFORE Rule 4!)
    match = re.match(r'^([a-zäöü]+)\s*/\s*([a-zäöü]+)', product_lower, re.IGNORECASE)
    if match:
        first_brand_word = match.group(1)
        second_brand_word = match.group(2)

        # Special case: "LKT / KTL" → Always use KTL
        if first_brand_word.lower() == 'lkt' and second_brand_word.lower() == 'ktl':
            return 'KTL'

        # Generally, check both brands and prefer the second one (more recent/primary)
        second_match = None
        first_match = None
        for brand in KNOWN_BRANDS:  # Use unsorted list
            if brand.lower() == second_brand_word.lower():
                second_match = brand
            if brand.lower() == first_brand_word.lower():
                first_match = brand

        # Prefer second brand if found
        if second_match:
            return second_match
        if first_match:
            return first_match

    # Rule 4: Check brand at very start (highest priority for most cases)
    for brand in sorted_brands:
        brand_lower = brand.lower()
        pattern_start = r'^' + re.escape(brand_lower) + r'\b'
        if re.search(pattern_start, product_lower):
            # Special case: "GEWO Schläger: ... + HALLMARK ..."
            # If HALLMARK model name contains "Clutter" or "Combination" → Hallmark brand
            if brand_lower == 'gewo' and 'hallmark' in product_lower:
                if 'clutter' in product_lower or 'combination' in product_lower or 'aurora' in product_lower:
                    return 'Hallmark'
            # Special case: "HALLMARK Schläger: ... + GEWO ..." → Gewo brand
            if brand_lower == 'hallmark' and 'gewo' in product_lower:
                if 'target' in product_lower or 'neoflexx' in product_lower:
                    return 'Gewo'
            return brand

    # Rule 5: Find any brand in the name (longest first)
    for brand in sorted_brands:
        brand_lower = brand.lower()
        if brand_lower in product_lower:
            pattern = r'\b' + re.escape(brand_lower) + r'\b'
            if re.search(pattern, product_lower):
                return brand

    # No brand found
    return "Desaka"


if __name__ == '__main__':
    # Test with difficult cases
    test_cases = [
        ("Dřevo Andro Arbalest Stock", "Andro"),
        ("DHS-vše na stolní tenis.cz (1 ks)", "DHS"),
        ("GEWO Schläger: Holz Celexxis Allround Classic mit Mega Flex Control + HALLMARK Clutter-LP  gerade", "Hallmark"),
        ("HALLMARK Schläger: Holz Aurora mit GEWO Target airTEC FX + Confusion-LP  anatomisch", "Gewo"),
        ("LKT / KTL Belag Pro XP rot 1", "KTL"),
        ("Nittaku Belag Magic Carbon rot 1", "Nittaku"),
    ]

    print("Testing extract_brand with difficult cases:")
    print("=" * 80)
    for product, expected in test_cases:
        result = extract_brand(product)
        status = "✓" if result == expected else "✗"
        print(f"{status} {product}")
        print(f"  Expected: {expected}, Got: {result}")
        print()
