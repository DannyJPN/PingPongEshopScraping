"""Pincesobchod CZ vs SK — Vlastnost produktu 'purchasePrice'.

Spuštění: python check_purchasePrice.py [--pullnewest] [--cs-json ...] [--sk-json ...] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("purchasePrice"))
