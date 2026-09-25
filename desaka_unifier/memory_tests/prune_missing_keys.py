#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remove memory entries whose KEY is not present in any latest eshop output.

Moves removed rows into Trash/<MemoryName>_<LANG>_trash.csv (append, unique KEY+VALUE).
"""

from __future__ import annotations

import argparse
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.file_ops import load_csv_file, save_csv_file, append_to_csv_file
from unifierlib.file_finder import find_output_files


DEFAULT_LANGUAGE = "CS"
DEFAULT_RESULTS_DIR = "H:/Desaka"

PRODUCT_KEYED_PREFIXES = {
    "NameMemory",
    "DescMemory",
    "ShortDescMemory",
    "ProductBrandMemory",
    "ProductTypeMemory",
    "ProductModelMemory",
    "CategoryMemory",
    "KeywordsGoogle",
    "KeywordsZbozi",
}

SKIP_ESHOPS = {"pincesobchod"}


def _normalize(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prune memory keys missing from latest outputs")
    parser.add_argument("--memory-dir", default=str(Path(__file__).parent.parent / "Memory"))
    parser.add_argument("--results-dir", default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--language", default=DEFAULT_LANGUAGE)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--include-prefix", action="append", default=[],
                        help="Include additional memory prefix (can repeat)")
    parser.add_argument("--only-prefix", action="append", default=[],
                        help="Process only these prefixes (can repeat)")
    return parser.parse_args()


def _get_eshop_list(memory_dir: str) -> List[str]:
    eshop_path = os.path.join(memory_dir, "EshopList.csv")
    if not os.path.exists(eshop_path):
        logging.warning("EshopList.csv not found: %s", eshop_path)
        return []
    rows = load_csv_file(eshop_path)
    return [
        row.get("Name", "").strip()
        for row in rows
        if row.get("Name", "").strip() and row.get("Name", "").strip().lower() not in SKIP_ESHOPS
    ]


def _load_latest_output_keys(results_dir: str, memory_dir: str, language: str) -> Set[str]:
    keys: Set[str] = set()
    eshops = _get_eshop_list(memory_dir)

    for eshop_name in eshops:
        eshop_dir = os.path.join(results_dir, eshop_name.lower())
        if not os.path.exists(eshop_dir):
            eshop_dir = os.path.join(results_dir, eshop_name)
        if not os.path.exists(eshop_dir):
            logging.warning("Eshop results directory not found for %s", eshop_name)
            continue

        csv_path, json_path = find_output_files(
            eshop_dir,
            eshop_name,
            language if "pincesobchod" in eshop_name.lower() else None
        )

        if csv_path:
            keys.update(_load_csv_keys(csv_path))
        if json_path:
            keys.update(_load_json_keys(json_path, language))

    return keys


def _load_csv_keys(csv_path: str) -> Set[str]:
    keys = set()
    rows = load_csv_file(csv_path)
    for row in rows:
        name = (row.get("Name") or "").strip()
        if name:
            keys.add(_normalize(name))
    return keys


def _load_json_keys(json_path: str, language: str) -> Set[str]:
    import json
    keys = set()
    try:
        with open(json_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception as exc:
        logging.error("Failed to load JSON %s: %s", json_path, exc)
        return keys

    items = []
    if isinstance(data, list):
        items = [item for item in data if isinstance(item, dict)]
    elif isinstance(data, dict):
        for key in ("data", "products", "items"):
            if isinstance(data.get(key), list):
                items = [item for item in data.get(key, []) if isinstance(item, dict)]
                break
        if not items:
            items = [data]

    lang_key = language.lower()
    for item in items:
        translations = item.get("translations", {})
        translation = translations.get(lang_key, {}) if isinstance(translations, dict) else {}
        name = (translation.get("name") or "").strip()
        if name:
            keys.add(_normalize(name))
    return keys


def _list_memory_files(memory_dir: str, language: str) -> List[Path]:
    suffix = f"_{language.upper()}.csv"
    files = []
    for name in os.listdir(memory_dir):
        if name.endswith(suffix):
            files.append(Path(memory_dir) / name)
    return sorted(files)


def _extract_prefix(filename: str) -> str:
    base = os.path.basename(filename)
    if base.endswith(".csv"):
        base = base[:-4]
    parts = base.split("_", 1)
    return parts[0]


def _append_unique_trash(trash_path: Path, rows: List[Dict[str, str]]) -> None:
    existing = set()
    if trash_path.exists():
        existing_rows = load_csv_file(str(trash_path))
        for rec in existing_rows:
            existing.add((rec.get("KEY", ""), rec.get("VALUE", "")))

    unique_rows = []
    for row in rows:
        row_id = (row.get("KEY", ""), row.get("VALUE", ""))
        if row_id in existing:
            continue
        unique_rows.append(row)
        existing.add(row_id)

    if unique_rows:
        append_to_csv_file(str(trash_path), unique_rows)


def _prune_memory_file(path: Path, output_keys: Set[str], dry_run: bool) -> Tuple[int, int]:
    rows = load_csv_file(str(path))
    kept = []
    removed = []

    for row in rows:
        key = (row.get("KEY") or "").strip()
        if not key:
            kept.append(row)
            continue
        if _normalize(key) in output_keys:
            kept.append(row)
        else:
            removed.append(row)

    if removed and not dry_run:
        trash_dir = Path(path.parent.parent) / "Trash"
        trash_dir.mkdir(parents=True, exist_ok=True)
        trash_name = f"{_extract_prefix(path.name)}_{path.stem.split('_')[-1]}_trash.csv"
        trash_path = trash_dir / trash_name
        _append_unique_trash(trash_path, removed)
        if kept:
            save_csv_file(kept, str(path))
        else:
            _write_empty_memory_file(path)

    return len(kept), len(removed)


def _write_empty_memory_file(path: Path) -> None:
    import csv
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["KEY", "VALUE"], quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writeheader()


def main() -> None:
    args = _parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    output_keys = _load_latest_output_keys(args.results_dir, args.memory_dir, args.language)
    logging.info("Loaded %d unique output keys", len(output_keys))
    if not output_keys:
        logging.error("No output keys loaded. Aborting to avoid wiping memory.")
        return

    prefixes = set(PRODUCT_KEYED_PREFIXES)
    prefixes.update(args.include_prefix or [])
    only_prefixes = set(args.only_prefix or [])

    memory_files = _list_memory_files(args.memory_dir, args.language)
    if not memory_files:
        logging.warning("No memory files found in %s", args.memory_dir)
        return

    for path in memory_files:
        prefix = _extract_prefix(path.name)
        if only_prefixes and prefix not in only_prefixes:
            continue
        if prefix not in prefixes:
            continue
        kept, removed = _prune_memory_file(path, output_keys, args.dry_run)
        logging.info("%s: kept=%d removed=%d", path.name, kept, removed)

    if args.dry_run:
        logging.info("Dry run complete (no changes written).")


if __name__ == "__main__":
    main()
