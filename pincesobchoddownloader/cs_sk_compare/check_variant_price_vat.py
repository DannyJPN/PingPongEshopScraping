"""Pincesobchod CZ vs SK — Cena běžná varianty = cena × (1 + DPH).

Spuštění: python check_variant_price_vat.py [--pullnewest] [--cs-json ...] [--sk-json ...] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("variant_price_vat"))
