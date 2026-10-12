"""Pincesobchod CZ vs SK — Varianty: identita (kód + parametry).

Spuštění: python check_variants.py [--pullnewest] [--cs-json ...] [--sk-json ...] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("variants"))
