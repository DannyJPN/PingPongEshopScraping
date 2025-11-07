#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Heuristic extraction method for VariantNameMemory_CS.csv

Translates German/English variant names to Czech.
"""

import re

# Variant name translations (German/English → Czech)
VARIANT_TRANSLATIONS = {
    # Color
    'farbe': 'Barva',
    'color': 'Barva',
    'colour': 'Barva',
    'colors': 'Barva',
    'farbe // color': 'Barva',

    # Grip/Handle
    'griff': 'Držení',
    'grip': 'Držení',
    'handle': 'Držení',
    'griffform': 'Držení',

    # Size
    'größe': 'Velikost',
    'size': 'Velikost',
    'groesse': 'Velikost',

    # Thickness
    'stärke': 'Tloušťka',
    'schwammstärke': 'Tloušťka',
    'thickness': 'Tloušťka',
    'sponge': 'Tloušťka',
    'sponge thickness': 'Tloušťka',

    # Speed/Power
    'tempo': 'Rychlost',
    'speed': 'Rychlost',

    # Length
    'länge': 'Délka',
    'length': 'Délka',

    # Material
    'material': 'Materiál',

    # Type
    'typ': 'Typ',
    'type': 'Typ',

    # Weight
    'gewicht': 'Hmotnost',
    'weight': 'Hmotnost',

    # Width
    'breite': 'Šířka',
    'width': 'Šířka',

    # Already Czech
    'barva': 'Barva',
    'velikost': 'Velikost',
    'tloušťka': 'Tloušťka',
}


def extract_variant_name(variant_name: str) -> str:
    """
    Translate variant name from German/English to Czech.

    Args:
        variant_name: Variant name in any language (KEY from memory file)

    Returns:
        Czech variant name
    """
    if not variant_name:
        return variant_name

    variant_lower = variant_name.lower().strip()

    # Direct translation lookup
    if variant_lower in VARIANT_TRANSLATIONS:
        return VARIANT_TRANSLATIONS[variant_lower]

    # If already Czech or unknown, return original
    return variant_name


if __name__ == '__main__':
    # Test with sample variant names
    test_cases = [
        ("Farbe", "Barva"),
        ("Griff", "Držení"),
        ("Größe", "Velikost"),
        ("Stärke", "Tloušťka"),
        ("Farbe // color", "Barva"),
    ]

    print("Testing extract_variant_name function:")
    print("=" * 80)
    for variant, expected in test_cases:
        result = extract_variant_name(variant)
        status = "✓" if result == expected else "✗"
        print(f"{status} Input:    {variant}")
        print(f"  Expected: {expected}")
        print(f"  Got:      {result}")
        print()
