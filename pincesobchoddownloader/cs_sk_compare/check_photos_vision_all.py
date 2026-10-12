"""OpenAI vizuální kontrola fotek všech produktů (drahé — použijte --limit, --brands, --dry-run).

Výsledky se ukládají do cache (JSONL), přerušený běh lze spustit znovu a pokračuje se.
"""
import sys

from cssklib.cli import run_vision

if __name__ == "__main__":
    sys.exit(run_vision())
