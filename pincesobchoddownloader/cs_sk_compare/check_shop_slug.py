"""Pincesobchod — Jeden e-shop: URL (slug) odpovídá názvu.

Spuštění: python check_shop_slug.py [--pullnewest] [--sides cs|sk|both] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("shop_slug"))
