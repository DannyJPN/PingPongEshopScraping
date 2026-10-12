"""Pincesobchod CZ vs SK — Vlastnost varianty 'deliveryDate'.

Spuštění: python check_variant_deliveryDate.py [--pullnewest] [--cs-json ...] [--sk-json ...] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("variant_deliveryDate"))
