"""Pincesobchod CZ vs SK — Cena varianty bez DPH: přepočet CZ → SK.

Spuštění: python check_variant_price.py [--pullnewest] [--cs-json ...] [--sk-json ...] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("variant_price"))
