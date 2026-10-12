"""Pincesobchod CZ vs SK — Vlastnost produktu 'mpn'.

Spuštění: python check_mpn.py [--pullnewest] [--cs-json ...] [--sk-json ...] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("mpn"))
