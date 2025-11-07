#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Heuristic extraction method for StockStatusMemory_CS.csv

Translates stock status messages from various languages to Czech.
"""

import re

# Stock status patterns and their Czech translations
STOCK_PATTERNS = {
    # In stock variations
    'skladem': 'skladem',
    'skladem,': 'skladem',
    'na skladě': 'skladem',
    'ihned': 'skladem',
    'ihned k odeslání': 'skladem',
    'sofort versandbereit': 'skladem',
    'sofort lieferbar': 'skladem',
    'in stock': 'skladem',
    'available': 'skladem',
    'auf lager': 'skladem',

    # Limited stock
    r'nur noch \d+ übrig': 'Pouze {} ks skladem, ihned k odeslání',
    r'pouze \d+ ks': 'Pouze {} ks skladem, ihned k odeslání',

    # Delivery time patterns
    r'dodání do (\d+) pracovních? dn': 'Dodání do {} pracovních dní',
    r'lieferzeit (\d+)-(\d+) werktage': 'Dodání do {}-{} pracovních dní',
    r'delivery (\d+)-(\d+) days': 'Dodání do {}-{} pracovních dní',

    # Specific delivery times from memory
    'dodání do 5 pracovních dní': 'Dodání do 5 pracovních dní',
    'dodání do 6 až 10 pracovních dní': 'Dodání do 6 až 10 pracovních dní',
}


def extract_stock_status(status_message: str) -> str:
    """
    Translate stock status message to Czech.

    Args:
        status_message: Stock status in any language (KEY from memory file)

    Returns:
        Czech stock status message
    """
    if not status_message:
        return ""

    status_lower = status_message.lower().strip()

    # Try exact matches first
    for pattern, czech in STOCK_PATTERNS.items():
        if not pattern.startswith('r\''):
            if status_lower == pattern:
                return czech

    # Try regex patterns
    # Limited stock pattern
    match = re.search(r'nur noch (\d+) übrig', status_lower)
    if match:
        count = match.group(1)
        return f'Pouze {count} ks skladem, ihned k odeslání'

    match = re.search(r'pouze (\d+) ks', status_lower)
    if match:
        count = match.group(1)
        return f'Pouze {count} ks skladem, ihned k odeslání'

    # If already Czech or unknown, return original
    return status_message


if __name__ == '__main__':
    # Test with sample status messages
    test_cases = [
        ("sofort versandbereit", "skladem"),
        ("Nur noch 1 übrig, sofort versandbereit", "Pouze 1 ks skladem, ihned k odeslání"),
        ("Dodání do 5 pracovních dní", "Dodání do 5 pracovních dní"),
    ]

    print("Testing extract_stock_status function:")
    print("=" * 80)
    for status, expected in test_cases:
        result = extract_stock_status(status)
        status_mark = "✓" if result == expected else "✗"
        print(f"{status_mark} Input:    {status}")
        print(f"  Expected: {expected}")
        print(f"  Got:      {result}")
        print()
