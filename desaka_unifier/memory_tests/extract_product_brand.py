#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PURE HEURISTIC Brand Extraction (no dictionary lookup)

Based on pattern analysis, extracts brand from product name using only rules.
"""

import re


# Known brands (from analysis) - these appear in product names
KNOWN_BRANDS = [
    # Top brands (>300 products each)
    'Gewo', 'Donic', 'Tibhar', 'Andro', 'Joola', 'Butterfly', 'Victas',
    'Dr. Neubauer', 'Xiom', 'Stiga', 'Nittaku', 'Friendship', 'DHS',
    'Barna',  # 298 products

    # Mid-tier brands (100-300 products)
    'Yasaka', 'Banda', 'TSP', 'Cornilleau', 'Sauer & Tröger', 'Sauer & Troger',
    'Sunflex', 'SunFlex', 'Killerspin', 'Yinhe', 'Galaxy', 'Palio', '729',
    'Hallmark', 'Milky Way', 'Milk Way',  # Common brands

    # Smaller brands (50-100 products)
    'Darker', 'Avalox', 'Sanwei', 'Sword', 'Spinlord', 'PimplePark', 'Imperial',
    'Air Racket', 'Arbalest', 'Armstrong', 'Der Materialspezialist',
    'Double Fish', 'Lion', 'Neottec', 'Adidas', 'SpinWay', 'Dawei',
    'Asics', 'ASICS', 'Mizuno', 'XIOM', 'BAUERFEIND', 'Alhelg',

    # Special brands
    'Der Materialspezialist', 'Sauer & Troger', 'Sauer & Tröger',
    'Dr Neubauer', 'Dr. Neubauer', 'BAUERFEIND',
]

# Normalize brands for matching (lowercase, no spaces/dashes)
BRAND_PATTERNS = []
for brand in KNOWN_BRANDS:
    # Create regex pattern that matches brand name (case-insensitive, flexible spacing)
    # For multi-word brands, allow various separators
    pattern = re.escape(brand.lower())
    pattern = pattern.replace(r'\ ', r'[\s\-]*')  # Allow space or dash between words
    pattern = pattern.replace(r'\&', r'[\s\&\+]*')  # Allow &, +, or space for ampersand
    BRAND_PATTERNS.append((brand, re.compile(r'\b' + pattern + r'\b', re.IGNORECASE)))


def extract_brand(product_name: str) -> str:
    """
    Extract brand from product name using PURE HEURISTICS.

    Rules (based on pattern analysis):
    1. Check if any known brand name appears in product name
    2. For composite names like "Der Materialspezialist", check both parts
    3. Handle variations (Dr. vs Dr, & vs and, etc.)
    4. Return "Desaka" if no brand is found (generic products)

    Args:
        product_name: Product name

    Returns:
        Detected brand or "Desaka"
    """
    if not product_name:
        return "Desaka"

    product_lower = product_name.lower()

    # Check each brand pattern
    for brand, pattern in BRAND_PATTERNS:
        if pattern.search(product_lower):
            # Found a match!
            # Return the canonical brand name (with proper casing)
            if 'materialspezialist' in brand.lower():
                return 'Der Materialspezialist'
            elif 'neubauer' in brand.lower():
                return 'Dr. Neubauer'
            elif 'sauer' in brand.lower():
                return 'Sauer & Troger'
            else:
                # Return brand with first letter capitalized
                return brand.title() if brand.islower() else brand

    # Special handling for numeric brands
    if re.search(r'\b729\b', product_name):
        return 'Friendship'  # 729 is often part of Friendship brand

    # No brand found - return Desaka (generic/unknown)
    return "Desaka"


# For testing
if __name__ == '__main__':
    # Test cases
    test_cases = [
        ("GEWO Belag Hype EL Pro 50 1", "Gewo"),
        ("Donic Tričko Draft L", "Donic"),
        ("BUTTERFLY - Dignics 05", "Butterfly"),
        ("Der Materialspezialist - Protector", "Der Materialspezialist"),
        ("Dr. Neubauer - Aggressor", "Dr. Neubauer"),
        ("ASICS Schuh Blade FF / 39", "Asics"),
        ("Buch: Tischtennis verstehen lernen", "Desaka"),  # Generic book
        ("5x Ersatzschnur", "Desaka"),  # Generic spare part
    ]

    print("Testing brand extraction (heuristic):")
    print("="*80)

    correct = 0
    for product_name, expected_brand in test_cases:
        extracted = extract_brand(product_name)
        match = "✓" if extracted.lower() == expected_brand.lower() else "✗"
        print(f"{match} '{product_name}'")
        print(f"  Expected: {expected_brand}, Got: {extracted}")
        if extracted.lower() == expected_brand.lower():
            correct += 1

    print(f"\n{correct}/{len(test_cases)} correct")
