"""Pincesobchod — Jeden e-shop: popisy bez odkazů (povolen jen odkaz na jiný produkt téhož e-shopu).

Spuštění: python check_shop_description_links.py [--pullnewest] [--sides cs|sk|both] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("shop_description_links"))
