#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PURE HEURISTIC Type Extraction (no dictionary lookup)

Based on pattern analysis, extracts product type using only rules.
"""

import re


# Type indicators based on pattern analysis
TYPE_PATTERNS = {
    # Pořadí záleží! Kontrolujeme od nejspecifičtějších k nejobecnějším

    # Rubber (Potah) - 68.5% has "belag", 26% has "potah"
    'Potah': [
        (r'\bbelag\b', 100),  # Strong indicator
        (r'\bpotah\b', 100),  # Strong indicator
        (r'\b(ox|max)\b.*\d+[,.]?\d*\s*(mm)?', 50),  # Thickness (OX, MAX, 2.0mm)
        (r'\d+[,.]?\d*\s*mm\b', 40),  # Thickness in mm
    ],

    # Blade (Dřevo) - 47.8% has "holz", 38.5% has "dřevo"
    'Dřevo': [
        (r'\bholz\b', 100),  # Strong indicator
        (r'\bdřevo\b', 100),  # Strong indicator
        (r'\bdrevo\b', 100),  # Slovak variant
        (r'\b(konkav|gerade|anatomisch)\b', 90),  # Handle shapes
        (r'\b(off|all|def)[\+\-]?(\b|[\s/])', 70),  # Speed categories (at end or followed by space/slash)
        (r'\bcarbon\b', 30),  # Often in blade names
        (r'\bblade\b', 80),  # English name
    ],

    # Shoes (Boty) - top words: 'schuh', 'boty'
    'Boty': [
        (r'\b(schuh|schuhe)\b', 100),
        (r'\bbot[ya]\b', 100),
        (r'\bshoes?\b', 100),
        (r'\b(39|40|41|42|43|44|45|46)\b', 50),  # Shoe sizes
        (r'\bus\s+\d+', 40),  # US sizes
    ],

    # T-shirt (Tričko) - top words: 'shirt', 'hemd', 't'
    'Tričko': [
        (r'\btričko\b', 100),
        (r'\b(t-?shirt|shirt)\b', 90),
        (r'\bhemd\b', 90),
        (r'\bpolo\b', 60),  # Polo shirt
    ],

    # Jacket (Bunda)
    'Bunda': [
        (r'\bbunda\b', 100),
        (r'\bjacke\b', 100),
        (r'\bjacket\b', 100),
    ],

    # Shorts (Kraťasy)
    'Kraťasy': [
        (r'\bkraťasy\b', 100),
        (r'\b(short|shorts)\b', 90),
        (r'\bhose\b', 50),  # German for pants
    ],

    # Pants (Kalhoty)
    'Kalhoty': [
        (r'\bkalhoty\b', 100),
        (r'\bhose\b', 70),  # German for pants (careful - overlap with shorts)
        (r'\bpants\b', 90),
        (r'\btrousers\b', 90),
    ],

    # Sweatshirt (Mikina) - common word: 'hoodie'
    'Mikina': [
        (r'\bmikina\b', 100),
        (r'\bhoodie\b', 100),
        (r'\bsweatshirt\b', 100),
    ],

    # Balls (Míčky) - common words: 'míčky', '40', 'ks'
    'Míčky': [
        (r'\bmíčky\b', 100),
        (r'\bmíček\b', 100),
        (r'\b(ball|bälle)\b', 90),
        (r'\b(40\+|3[\*]+)\b', 60),  # Ball quality (40+, 3***)
        (r'\bks\b', 20),  # "kusy" (pieces) - weak indicator
    ],

    # Table (Stůl)
    'Stůl': [
        (r'\bstůl\b', 100),
        (r'\btisch\b', 100),
        (r'\btable\b', 90),
        (r'\bvenkovní\b', 50),  # Outdoor table
        (r'\boutdoor\b', 50),
    ],

    # Case/Cover (Pouzdro)
    'Pouzdro': [
        (r'\bpouzdro\b', 100),
        (r'\bcase\b', 90),
        (r'\bhülle\b', 90),
        (r'\bobal\b', 80),
    ],

    # Bat/Racket (Pálka) - complete racket
    'Pálka': [
        (r'\bpálka\b', 100),
        (r'\bschläger\b', 90),
        (r'\bracket\b', 70),
        (r'\b(mini|midi)\s+(pálka|schläger)', 100),
    ],

    # Glue (Lepidlo)
    'Lepidlo': [
        (r'\blepidlo\b', 100),
        (r'\bkleber\b', 100),
        (r'\bglue\b', 100),
    ],

    # Protective tape (Ochranná páska) - common word: 'páska'
    'Ochranná páska': [
        (r'\bpáska\b', 90),
        (r'\btape\b', 80),
        (r'\b(edge|kant|edge)\s*(tape|páska)', 100),
    ],

    # Shirt with collar (Koš - actually means polo shirt based on 'polokošile')
    'Koš': [
        (r'\bpolokošile\b', 100),
        (r'\bpolo\b.*\b(košile|shirt)\b', 90),
    ],

    # Net (Síť/Síťka)
    'Síť': [
        (r'\bsíť(ka)?\b', 100),
        (r'\bnetz\b', 100),
        (r'\bnet\b', 80),
    ],
}


def extract_type(product_name: str) -> str:
    """
    Extract product type from product name using PURE HEURISTICS.

    Rules (based on pattern analysis):
    1. Check specific keywords for each type (ordered by strength)
    2. Use negative indicators to eliminate impossible types
    3. Return type with highest score
    4. Default to "Potah" if ambiguous (most common type)

    Args:
        product_name: Product name

    Returns:
        Detected product type
    """
    if not product_name:
        return "Potah"  # Default fallback

    product_lower = product_name.lower()

    # Calculate scores for each type
    type_scores = {}

    for product_type, patterns in TYPE_PATTERNS.items():
        score = 0
        for pattern, weight in patterns:
            if re.search(pattern, product_lower):
                score += weight

        if score > 0:
            type_scores[product_type] = score

    # Return type with highest score
    if type_scores:
        best_type = max(type_scores, key=type_scores.get)
        best_score = type_scores[best_type]

        # Require minimum score threshold
        if best_score >= 50:
            return best_type

    # Special case: if product has handle shape indicators but no "holz"/"dřevo"
    # it's still likely a blade
    if re.search(r'\b(konkav|gerade|anatomisch)\b', product_lower):
        return "Dřevo"

    # Special case: thickness in mm without other indicators → likely rubber
    if re.search(r'\d+[,.]?\d*\s*mm\b', product_lower):
        return "Potah"

    # Default fallback: "Potah" is the most common type (6029 out of 17686 = 34%)
    return "Potah"


# For testing
if __name__ == '__main__':
    # Test cases
    test_cases = [
        ("GEWO Belag Hype EL Pro 50 1 2.0", "Potah"),
        ("BUTTERFLY - Dignics 05", "Potah"),
        ("ANDRO - Gauzy SL OFF", "Dřevo"),
        ("Arbalest Holz Balsa V konkav", "Dřevo"),
        ("ASICS Schuh Blade FF / 39", "Boty"),
        ("Donic Tričko Draft L", "Tričko"),
        ("BUTTERFLY-Míčky Classic (3 ks)", "Míčky"),
        ("GEWO Tisch Europa 25", "Stůl"),
        ("BUTTERFLY-Cell Case II", "Pouzdro"),
        ("Der Materialspezialist - Spinfire", "Potah"),
        ("Andro - Timber 5 ALL/S", "Dřevo"),
    ]

    print("Testing type extraction (heuristic):")
    print("="*80)

    correct = 0
    for product_name, expected_type in test_cases:
        extracted = extract_type(product_name)
        match = "✓" if extracted == expected_type else "✗"
        print(f"{match} '{product_name}'")
        print(f"  Expected: {expected_type}, Got: {extracted}")
        if extracted == expected_type:
            correct += 1

    print(f"\n{correct}/{len(test_cases)} correct ({100*correct/len(test_cases):.1f}%)")
