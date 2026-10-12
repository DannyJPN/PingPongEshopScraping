"""Pincesobchod — Jeden e-shop: jedna hlavní fotka na 1. pozici, pozice 1..n, bez duplicit.

Spuštění: python check_shop_images.py [--pullnewest] [--sides cs|sk|both] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("shop_images"))
