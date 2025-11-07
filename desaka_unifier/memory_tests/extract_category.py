#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Heuristic extraction method for CategoryMemory_CS.csv

Extracts product category from product name.
This is similar to ProductType but uses different category names.
"""

import re

# Category mappings (reusing type patterns)
CATEGORY_PATTERNS = {
    # Trophy
    'Poháry': [
        r'\bpokal\b', r'\btrophy\b', r'\btrophies\b', r'\bpohár',
    ],

    # Nets
    'Síťky': [
        r'\bnetz\b', r'\bnet\b', r'\bsíť\b', r'\bsíťk',
    ],

    # Sets
    'Sada': [
        r'^\d+er\s+set\b', r'^\d+x\s+set\b', r'\bset\b.*\bset\b',
        r'\bsada\b',
    ],

    # Exclude (Vyřadit)
    'Vyřadit': [
        r'\btable.*green\b',  # Green tables to exclude
    ],

    # Ropes/Chains
    'Řetízky': [
        r'\bkettchen\b', r'\bchain\b', r'\břetízek\b',
    ],
}


def extract_category(product_name: str) -> str:
    """
    Extract category from product name.

    Args:
        product_name: Full product name (KEY from memory file)

    Returns:
        Czech category name or empty string if not determined
    """
    if not product_name:
        return ""

    product_lower = product_name.lower()

    # Check each category pattern
    for czech_category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, product_lower, re.IGNORECASE):
                return czech_category

    # No category found
    return ""


if __name__ == '__main__':
    # Test with sample product names
    test_cases = [
        ('10 x Ersatzkettchen "Kugel"', 'Řetízky'),
        ('2er Set GEWO Table Gewomatic SC 25 blue + 2 net', 'Sada'),
    ]

    print("Testing extract_category function:")
    print("=" * 80)
    for product, expected in test_cases:
        category = extract_category(product)
        status = "✓" if category == expected else "✗"
        print(f"{status} Product:  {product}")
        print(f"  Expected: {expected}")
        print(f"  Got:      {category if category else '(empty)'}")
        print()
