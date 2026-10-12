"""Pincesobchod CZ vs SK — Vlastnost produktu 'deliveryFree'.

Spuštění: python check_deliveryFree.py [--pullnewest] [--cs-json ...] [--sk-json ...] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("deliveryFree"))
