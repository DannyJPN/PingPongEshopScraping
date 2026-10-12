"""Pincesobchod CZ vs SK — Vlastnost varianty 'weight'.

Spuštění: python check_variant_weight.py [--pullnewest] [--cs-json ...] [--sk-json ...] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("variant_weight"))
