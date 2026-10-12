"""Pincesobchod CZ vs SK — Cena běžná: přepočet CZ → SK dle značky.

Spuštění: python check_standardPrice.py [--pullnewest] [--cs-json ...] [--sk-json ...] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("standardPrice"))
