"""Pincesobchod — Jeden e-shop: stejné CPC ve všech feedech.

Spuštění: python check_shop_feed_cpc.py [--pullnewest] [--sides cs|sk|both] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("shop_feed_cpc"))
