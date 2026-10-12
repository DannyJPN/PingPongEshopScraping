"""Pincesobchod CZ vs SK — hromadná kontrola všech vlastností (souhrnný report).

Spuštění: python check_all.py [--pullnewest] [--only ID ...] [--skip ID ...] [--no-<id>] [--vision]
"""
import sys

from cssklib.cli import run_all

if __name__ == "__main__":
    sys.exit(run_all())
