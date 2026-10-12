"""Pincesobchod CZ vs SK — Překlad 'slug' (translations.*.slug).

Spuštění: python check_translations_slug.py [--pullnewest] [--cs-json ...] [--sk-json ...] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("translations_slug"))
