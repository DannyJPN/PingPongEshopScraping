"""Pincesobchod CZ vs SK — Vlastnost produktu 'deliveryDateAuto'.

Spuštění: python check_deliveryDateAuto.py [--pullnewest] [--cs-json ...] [--sk-json ...] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("deliveryDateAuto"))
