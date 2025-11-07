#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Heuristic extraction method for ProductTypeMemory_CS.csv

Extracts product type (category) from product name using keyword matching.
Returns Czech product type names.
"""

import re

# Product type mappings (keywords → Czech type)
TYPE_PATTERNS = {
    # Rubbers (Potah)
    'Potah': [
        r'\bbelag\b', r'\brubber\b', r'\bpotah', r'\bpotahu\b',
        r'\brasanter\b', r'\btenergy\b', r'\brakza\b', r'\bhexer\b',
        r'\bevo\b', r'\bacuda\b', r'\bvega\b', r'\bmagna\b',
    ],

    # Blades (Dřevo)
    'Dřevo': [
        r'\bholz\b', r'\bblade\b', r'\bdřevo\b', r'\bdřeva\b',
        r'\bviscaria\b', r'\btimo\s+boll\b', r'\binner\s*force\b',
        r'\bfortissimo\b', r'\bprimorac\b',
    ],

    # Shoes (Boty)
    'Boty': [
        r'\bschuh\b', r'\bschuhe\b', r'\bshoe\b', r'\bshoes\b',
        r'\bboty\b', r'\bbota\b', r'\btrainer\b',
    ],

    # Balls (Míčky)
    'Míčky': [
        r'\bball(?!box)\b', r'\bbälle\b', r'\bmíček\b', r'\bmíčky\b',
        r'\b3[- ]?star\b.*\bball', r'\bnexcel\b', r'\bpremium\b.*\bball',
    ],

    # Ball containers (Pouzdro)
    'Pouzdro': [
        r'\bballbox\b', r'\bball\s+box\b', r'\bball\s+case\b',
        r'\bball\s+container\b', r'\bballeimer\b', r'\bpouzdro\b',
    ],

    # Tables (Stůl)
    'Stůl': [
        r'\btisch\b', r'\btable\b', r'\bstůl\b', r'\bstolu\b',
    ],

    # Nets (Síťka/Síť)
    'Síťka': [
        r'\bnetz\b', r'\bnet\b', r'\bsíť\b', r'\bsíťk', r'\bsíťov',
    ],

    # Clothing - Shirts (Triko)
    'Triko': [
        r'\bshirt\b', r'\btriko\b', r'\btričko\b', r'\bdres\b',
        r'\bjersey\b', r'\btop\b',
    ],

    # Clothing - Shorts (Kraťasy)
    'Kraťasy': [
        r'\bshort\b', r'\bshorts\b', r'\bkraťasy\b', r'\bkraťas',
    ],

    # Clothing - Pants (Kalhoty)
    'Kalhoty': [
        r'\bhose\b', r'\bpants\b', r'\bkalhoty\b', r'\btrousers\b',
    ],

    # Clothing - Hoodie (Mikina)
    'Mikina': [
        r'\bhoodie\b', r'\bmikina\b', r'\bsweatshirt\b', r'\bsweater\b',
    ],

    # Clothing - Jacket (Bunda)
    'Bunda': [
        r'\bjacke\b', r'\bjacket\b', r'\bbunda\b',
    ],

    # Clothing - Socks (Ponožky)
    'Ponožky': [
        r'\bsocken\b', r'\bsocks\b', r'\bponožky\b', r'\bponožek\b',
    ],

    # Accessories - Bag (Taška)
    'Taška': [
        r'\btasche\b', r'\bbag\b', r'\btaška\b', r'\btašky\b',
    ],

    # Accessories - Edge tape (Ochranná páska)
    'Ochranná páska': [
        r'\bkantenband\b', r'\bkantenschutz\b', r'\bedge\s+tape\b',
        r'\bpáska\b',
    ],

    # Accessories - Glue (Lepidlo)
    'Lepidlo': [
        r'\bkleber\b', r'\bglue\b', r'\blepidlo\b',
    ],

    # Accessories - Cleaner (Čistič)
    'Čistič': [
        r'\breiniger\b', r'\bcleaner\b', r'\bčistič\b',
    ],

    # Accessories - Towel (Ručník)
    'Ručník': [
        r'\bhandtuch\b', r'\btowel\b', r'\bručník\b',
    ],

    # Accessories - Headband (Čelenka)
    'Čelenka': [
        r'\bheadband\b', r'\bstirn\s*band\b', r'\bčelenka\b',
    ],

    # Accessories - Wristband (Potítko)
    'Potítko': [
        r'\bschweißband\b', r'\bwristband\b', r'\bpotítko\b',
    ],

    # Sets (Sada)
    'Sada': [
        r'^\d+er\s+set\b', r'^\d+x\s+set\b', r'\bset\b.*\bset\b',
        r'\bsada\b', r'\bbalíček\b',
    ],

    # Trophy (Poháry)
    'Poháry': [
        r'\bpokal\b', r'\btrophy\b', r'\btrophies\b', r'\bpohár',
    ],

    # Chain (Řetízek)
    'Řetízek': [
        r'\bkettchen\b', r'\bchain\b', r'\břetízek\b', r'\břetíz',
    ],

    # Rope (Šňůra)
    'Šňůra': [
        r'\bschnur\b', r'\brope\b', r'\bšňůra\b',
    ],
}


def extract_type(product_name: str) -> str:
    """
    Extract product type from product name using pattern matching.

    Args:
        product_name: Full product name (KEY from memory file)

    Returns:
        Czech product type name or empty string if not determined
    """
    if not product_name:
        return ""

    product_lower = product_name.lower()

    # Special case: ASICS shoes
    if 'asics' in product_lower and 'schuh' in product_lower:
        return 'Boty'

    # Special case: Ball containers (before general ball detection)
    if re.search(r'\bball\b', product_lower):
        if re.search(r'\b(box|case|container|eimer)\b', product_lower):
            return 'Pouzdro'

    # Check each type pattern
    for czech_type, patterns in TYPE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, product_lower, re.IGNORECASE):
                # Special handling for "Belag" - always Potah, never Dřevo
                if 'belag' in product_lower and czech_type == 'Dřevo':
                    continue
                return czech_type

    # No type found
    return ""


if __name__ == '__main__':
    # Test with sample product names
    test_cases = [
        ("Nittaku Belag Magic Carbon rot 1,5", "Potah"),
        ("ASICS Schuh Blade FF 2 I grau 39", "Boty"),
        ("Butterfly Viscaria FL", "Dřevo"),
        ("Nittaku 3-Star Premium Ball", "Míčky"),
        ("ANDRO Hoodie Doley grau L", "Mikina"),
        ("GEWO Ballbox 144", "Pouzdro"),
    ]

    print("Testing extract_type function:")
    print("=" * 80)
    for product, expected in test_cases:
        ptype = extract_type(product)
        status = "✓" if ptype == expected else "✗"
        print(f"{status} Product:  {product}")
        print(f"  Expected: {expected}")
        print(f"  Got:      {ptype if ptype else '(empty)'}")
        print()
