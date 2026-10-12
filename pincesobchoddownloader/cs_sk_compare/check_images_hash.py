"""Pincesobchod CZ vs SK — Fotky: shoda obsahu (SHA-256 hash).

Spuštění: python check_images_hash.py [--pullnewest] [--cs-json ...] [--sk-json ...] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("images_hash"))
