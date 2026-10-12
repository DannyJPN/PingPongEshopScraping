"""Pincesobchod CZ vs SK — Vlastnost varianty 'id'.

Spuštění: python check_variant_id.py [--pullnewest] [--cs-json ...] [--sk-json ...] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("variant_id"))
