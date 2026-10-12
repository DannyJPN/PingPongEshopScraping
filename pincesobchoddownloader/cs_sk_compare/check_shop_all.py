"""Pincesobchod — všechny kontroly v rámci jednoho e-shopu (CZ i SK zvlášť, souhrnný report).

Spuštění: python check_shop_all.py [--pullnewest] [--sides cs|sk|both] [--no-<id>] (viz --help)
"""
import sys

from cssklib.cli import run_all

if __name__ == "__main__":
    sys.exit(run_all(default_groups=["shop"], report_name="shop_all"))
