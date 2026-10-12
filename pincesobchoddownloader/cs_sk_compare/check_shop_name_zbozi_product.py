"""Pincesobchod — Jeden e-shop: název produktu = feeds.zbozi.product (Zboží product).

Spuštění: python check_shop_name_zbozi_product.py [--pullnewest] [--sides cs|sk|both] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("shop_name_zbozi_product"))
