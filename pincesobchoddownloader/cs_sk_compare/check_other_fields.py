"""Pincesobchod CZ vs SK — Ostatní (neznámé) vlastnosti produktu.

Spuštění: python check_other_fields.py [--pullnewest] [--cs-json ...] [--sk-json ...] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("other_fields"))
