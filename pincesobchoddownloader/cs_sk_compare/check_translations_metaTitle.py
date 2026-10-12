"""Pincesobchod CZ vs SK — Překlad 'metaTitle' (translations.*.metaTitle).

Spuštění: python check_translations_metaTitle.py [--pullnewest] [--cs-json ...] [--sk-json ...] (viz --help)
"""
import sys

from cssklib.cli import run_single_check

if __name__ == "__main__":
    sys.exit(run_single_check("translations_metaTitle"))
