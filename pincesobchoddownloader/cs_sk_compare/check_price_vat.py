"""Pincesobchod CZ vs SK — Cena běžná = cena × (1 + DPH) v CZ i SK.

Spuštění: python check_price_vat.py [--pullnewest] [--cs-json ...] [--sk-json ...] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("price_vat"))
