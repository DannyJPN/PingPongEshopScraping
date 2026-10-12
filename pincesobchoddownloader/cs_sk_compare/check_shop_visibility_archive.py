"""Pincesobchod — Jeden e-shop: produkt není viditelný a archivovaný zároveň.

Spuštění: python check_shop_visibility_archive.py [--pullnewest] [--sides cs|sk|both] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("shop_visibility_archive"))
