#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Repair memory values using the latest completed batch for the same memory file.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from tqdm import tqdm


ROOT_DIR = Path(__file__).resolve().parent
BATCH_STATE_DIR = ROOT_DIR / "batch_state"
BATCH_REGISTRY_PATH = BATCH_STATE_DIR / "batch_registry.json"
REPORTS_DIR = BATCH_STATE_DIR / "reports"
DEFAULT_MEMORY_DIR = ROOT_DIR.parent / "desaka_unifier" / "Memory"
REJECTIONS_PATH = REPORTS_DIR / "repair_rejections.json"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Repair memory values from batch results")
    parser.add_argument("--memory-dir", default=str(DEFAULT_MEMORY_DIR))
    parser.add_argument("--memory-file", action="append", default=[],
                        help="Memory filename to repair (repeatable)")
    parser.add_argument("--no-confirm", action="store_true")
    return parser.parse_args()


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_rejections() -> Dict[str, Dict[str, str]]:
    if not REJECTIONS_PATH.exists():
        return {}
    try:
        data = json.loads(REJECTIONS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _save_rejections(data: Dict[str, Dict[str, str]]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    REJECTIONS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_csv(path: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=",", quotechar='"')
        for row in reader:
            rows.append(row)
    return rows


def _save_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    if not rows:
        with open(path, "w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["KEY", "VALUE"], quotechar='"', quoting=csv.QUOTE_ALL)
            writer.writeheader()
        return
    fieldnames = list(rows[0].keys())
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def _normalize_memory_name(value: str) -> str:
    return Path(value).name.lower()


def _needs_capitalization(memory_file: str) -> bool:
    name = Path(memory_file).name
    return name.startswith("ProductTypeMemory") or name.startswith("ProductModelMemory") or name.startswith("ProductBrandMemory")


def _ensure_leading_capital(value: str) -> str:
    if not value:
        return value
    first = value[0]
    if first.isalpha() and first.islower():
        return first.upper() + value[1:]
    return value


def _find_latest_completed_batch(memory_name: str) -> Optional[Tuple[str, Path]]:
    registry = _load_json(BATCH_REGISTRY_PATH)
    completed = registry.get("completed_batches", [])
    if not completed:
        return None

    candidates: List[Tuple[str, str]] = []
    for item in completed:
        batch_id = item.get("batch_id")
        if not batch_id:
            continue
        batch_dir = BATCH_STATE_DIR / "batches" / batch_id
        state_path = batch_dir / "state.json"
        if not state_path.exists():
            continue
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        records = state.get("records", [])
        for record in records:
            payload = record.get("payload", {}) or {}
            mem_file = payload.get("memory_file", "")
            if _normalize_memory_name(mem_file) == memory_name:
                completed_at = item.get("completed_at") or state.get("created_at") or ""
                candidates.append((completed_at, batch_id))
                break

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0])
    latest_batch_id = candidates[-1][1]
    return latest_batch_id, BATCH_STATE_DIR / "batches" / latest_batch_id


def _load_batch_payloads(batch_dir: Path) -> Dict[str, Dict[str, object]]:
    state_path = batch_dir / "state.json"
    state = _load_json(state_path)
    payloads: Dict[str, Dict[str, object]] = {}
    for record in state.get("records", []):
        custom_id = record.get("custom_id")
        payload = record.get("payload")
        if custom_id and payload:
            payloads[custom_id] = payload
    return payloads


def _load_batch_results(batch_dir: Path) -> Dict[str, Dict[str, object]]:
    results_path = batch_dir / "results.json"
    raw = _load_json(results_path)
    results = {}
    for custom_id, entry in raw.items():
        result = entry.get("result") if isinstance(entry, dict) else None
        if isinstance(result, dict):
            results[custom_id] = result
    return results


def _confirm_change(key: str, old: str, new: str, url: str) -> str:
    if url:
        print(f"URL: {url}")
    print(f"KEY: {key}")
    print(f"OLD: {old}")
    print(f"NEW: {new}")
    choice = input("Apply change? [Y/n/e/s]: ").strip().lower()
    if choice in ("", "y", "yes"):
        return "apply"
    if choice in ("e", "edit", "manual"):
        return "manual"
    if choice in ("s", "skip"):
        return "skip"
    return "keep"


def _write_report(rows: List[Dict[str, str]]) -> None:
    if not rows:
        return
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"repair_report_{timestamp}.csv"
    fieldnames = list(rows[0].keys())
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Report saved: {path}")


def _repair_memory_file(memory_dir: Path, memory_file: str, no_confirm: bool) -> None:
    memory_path = memory_dir / memory_file
    if not memory_path.exists():
        logging.error("Memory file not found: %s", memory_path)
        return

    latest = _find_latest_completed_batch(memory_file.lower())
    if not latest:
        logging.warning("No completed batch found for %s", memory_file)
        return

    batch_id, batch_dir = latest
    print(f"Using batch: {batch_id}")

    payloads = _load_batch_payloads(batch_dir)
    results = _load_batch_results(batch_dir)

    if not results:
        logging.warning("No results found for batch %s", batch_id)
        return

    rows = _load_csv(memory_path)
    row_map = {str(row.get("KEY", "")).strip(): row for row in rows}

    changes: List[Dict[str, str]] = []
    applied = 0
    skipped = 0
    manual_applied = 0
    rejections = _load_rejections()
    memory_rejections = rejections.get(memory_file, {})
    handled_keys = set()

    total_results = len(results)
    if no_confirm:
        iterator = tqdm(results.keys(), desc=f"Applying {memory_file}", unit="rows", leave=False)
    else:
        iterator = results.keys()
    processed = 0

    def _persist_if_needed() -> None:
        if not no_confirm:
            _save_csv(memory_path, rows)

    for custom_id in iterator:
        result = results.get(custom_id, {})
        if result.get("is_correct") != "no":
            if not no_confirm:
                processed += 1
            continue
        correct_value = str(result.get("correct_value", "")).strip()
        if _needs_capitalization(memory_file):
            correct_value = _ensure_leading_capital(correct_value)
        if not correct_value and no_confirm:
            skipped += 1
            continue
        payload = payloads.get(custom_id, {})
        key = str(payload.get("key", "")).strip()
        if not key:
            skipped += 1
            if not no_confirm:
                processed += 1
            continue
        if key in handled_keys:
            skipped += 1
            if not no_confirm:
                processed += 1
            continue
        product_context = payload.get("product_context", {}) or {}
        url = str(product_context.get("url", "")).strip()
        row = row_map.get(key)
        if not row:
            skipped += 1
            if not no_confirm:
                processed += 1
            continue
        old_value = str(row.get("VALUE", ""))
        if not no_confirm and key in memory_rejections:
            skipped += 1
            processed += 1
            changes.append({
                "memory_file": memory_file,
                "key": key,
                "old_value": old_value,
                "new_value": "",
                "action": "previously_rejected"
            })
            continue
        if old_value.casefold() == correct_value.casefold():
            if not no_confirm:
                processed += 1
            continue

        if not no_confirm:
            processed += 1
            print(f"{processed}/{total_results}")
            action = _confirm_change(key, old_value, correct_value, url)
            if action == "skip":
                skipped += 1
                changes.append({
                    "memory_file": memory_file,
                    "key": key,
                    "old_value": old_value,
                    "new_value": "",
                    "action": "skipped"
                })
                continue
            if action == "keep":
                skipped += 1
                memory_rejections[key] = datetime.utcnow().isoformat()
                rejections[memory_file] = memory_rejections
                _save_rejections(rejections)
                changes.append({
                    "memory_file": memory_file,
                    "key": key,
                    "old_value": old_value,
                    "new_value": "",
                    "action": "kept_old"
                })
                continue
            if action == "manual":
                manual_value = input("Enter correct value: ").strip()
                if not manual_value:
                    skipped += 1
                    changes.append({
                        "memory_file": memory_file,
                        "key": key,
                        "old_value": old_value,
                        "new_value": "",
                        "action": "manual_empty"
                    })
                    continue
                row["VALUE"] = manual_value
                _persist_if_needed()
                manual_applied += 1
                handled_keys.add(key)
                changes.append({
                    "memory_file": memory_file,
                    "key": key,
                    "old_value": old_value,
                    "new_value": manual_value,
                    "action": "manual"
                })
                continue

        if correct_value:
            row["VALUE"] = correct_value
            _persist_if_needed()
            applied += 1
            handled_keys.add(key)
            changes.append({
                "memory_file": memory_file,
                "key": key,
                "old_value": old_value,
                "new_value": correct_value,
                "action": "auto" if no_confirm else "accepted"
            })
        else:
            skipped += 1
            if not no_confirm:
                changes.append({
                    "memory_file": memory_file,
                    "key": key,
                    "old_value": old_value,
                    "new_value": "",
                    "action": "no_suggestion"
                })

    if applied:
        _save_csv(memory_path, rows)
    _write_report(changes)

    print(
        f"Changed: {applied} | Manual: {manual_applied} | Skipped: {skipped} | Total results: {len(results)}"
    )


def main() -> None:
    args = _parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    memory_dir = Path(args.memory_dir)
    if args.memory_file:
        targets = args.memory_file
    else:
        targets = [p.name for p in memory_dir.iterdir() if p.is_file() and p.name.endswith("_CS.csv")]

    for memory_file in targets:
        _repair_memory_file(memory_dir, memory_file, args.no_confirm)


if __name__ == "__main__":
    main()
