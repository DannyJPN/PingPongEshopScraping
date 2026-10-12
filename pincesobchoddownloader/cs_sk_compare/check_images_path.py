"""Pincesobchod CZ vs SK — Fotky: počet, pořadí a cesty.

Spuštění: python check_images_path.py [--pullnewest] [--cs-json ...] [--sk-json ...] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("images_path"))
