"""Pincesobchod CZ vs SK — Identita produktu (kód + název): chybějící / konfliktní produkty.

Spuštění: python check_identity.py [--pullnewest] [--cs-json ...] [--sk-json ...] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("identity"))
