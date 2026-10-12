"""Pincesobchod CZ vs SK — Sazba DPH (CZ 21 %, SK 23 %).

Spuštění: python check_vat.py [--pullnewest] [--cs-json ...] [--sk-json ...] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("vat"))
