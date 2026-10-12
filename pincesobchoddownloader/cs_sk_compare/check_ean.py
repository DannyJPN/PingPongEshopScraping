"""Pincesobchod CZ vs SK — Vlastnost produktu 'ean'.

Spuštění: python check_ean.py [--pullnewest] [--cs-json ...] [--sk-json ...] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("ean"))
