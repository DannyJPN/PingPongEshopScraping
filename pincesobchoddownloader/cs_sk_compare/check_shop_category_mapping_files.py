"""Pincesobchod — Jeden e-shop: mapovací soubory kategorií proti JSONu a proti sobě navzájem.

Spuštění: python check_shop_category_mapping_files.py [--pullnewest] [--sides cs|sk|both] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("shop_category_mapping_files"))
