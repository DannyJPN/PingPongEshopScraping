"""Pincesobchod — Jeden e-shop: SEO popis (metaDescription) = anotace.

Spuštění: python check_shop_metaDescription.py [--pullnewest] [--sides cs|sk|both] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("shop_metaDescription"))
