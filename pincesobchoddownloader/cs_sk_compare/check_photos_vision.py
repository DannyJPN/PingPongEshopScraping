"""OpenAI vizuální kontrola fotek vybraných produktů (--codes).

Zjistí, zda každá fotka zobrazuje produkt, k němuž je přiřazena, nebo s ním souvisí
(např. velikostní tabulka u textilu). Výsledky se ukládají do cache, opakované běhy neplatí znovu.
"""
import sys

from cssklib.cli import run_vision

if __name__ == "__main__":
    sys.exit(run_vision(require_codes=True))
