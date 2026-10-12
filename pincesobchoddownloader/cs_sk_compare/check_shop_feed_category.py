"""Pincesobchod — Jeden e-shop: kategorie ve feedech = nejhlubší kategorie produktu.

Spuštění: python check_shop_feed_category.py [--pullnewest] [--sides cs|sk|both] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("shop_feed_category"))
