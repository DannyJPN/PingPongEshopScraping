"""Pincesobchod — Jeden e-shop: název obsahuje značku výrobce.

Spuštění: python check_shop_brand_in_name.py [--pullnewest] [--sides cs|sk|both] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("shop_brand_in_name"))
