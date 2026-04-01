"""Load latest result records for memory lookups."""
from __future__ import annotations

import csv
import json
import logging
import os
from datetime import datetime
from typing import Dict, Iterable, List, Optional

from batchmemorycheckerlib.constants import DEFAULT_LANGUAGE

SKIP_ESHOPS = {"pincesobchod"}
from batchmemorycheckerlib.file_finder import find_output_files


def _normalize_name(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def load_eshop_list(memory_dir: str) -> List[str]:
    eshop_path = os.path.join(memory_dir, "EshopList.csv")
    if not os.path.exists(eshop_path):
        logging.warning("EshopList.csv not found in %s", memory_dir)
        return []

    names = []
    with open(eshop_path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            name = (row.get("Name") or "").strip()
            if name and name.lower() not in SKIP_ESHOPS:
                names.append(name)
    return names


def load_latest_result_records(results_dir: str, memory_dir: str, language: str) -> List[Dict[str, object]]:
    eshops = load_eshop_list(memory_dir)
    records: List[Dict[str, object]] = []

    if not eshops:
        logging.warning("No eshops found in EshopList.csv")

    for eshop_name in eshops:
        eshop_dir = os.path.join(results_dir, eshop_name.lower())
        if not os.path.exists(eshop_dir):
            eshop_dir = os.path.join(results_dir, eshop_name)
        if not os.path.exists(eshop_dir):
            logging.warning("Eshop results directory not found for %s", eshop_name)
            continue

        csv_path, json_path, latest_dir = find_output_files(
            eshop_dir,
            eshop_name,
            language if _is_pincesobchod(eshop_name) else None
        )

        source_date = _extract_date_from_dir(latest_dir)

        if csv_path:
            records.extend(_load_csv_records(csv_path, eshop_name, latest_dir, source_date))
        if json_path:
            records.extend(_load_json_records(json_path, eshop_name, latest_dir, source_date, language))

    return records


def get_latest_outputs_summary(results_dir: str, memory_dir: str, language: str) -> List[Dict[str, object]]:
    eshops = load_eshop_list(memory_dir)
    summary: List[Dict[str, object]] = []

    for eshop_name in eshops:
        eshop_dir = os.path.join(results_dir, eshop_name.lower())
        if not os.path.exists(eshop_dir):
            eshop_dir = os.path.join(results_dir, eshop_name)
        if not os.path.exists(eshop_dir):
            summary.append({
                "eshop": eshop_name,
                "status": "missing_dir",
                "latest_dir": "",
                "csv_path": "",
                "json_path": "",
                "source_date": ""
            })
            continue

        csv_path, json_path, latest_dir = find_output_files(
            eshop_dir,
            eshop_name,
            language if _is_pincesobchod(eshop_name) else None
        )
        source_date = _extract_date_from_dir(latest_dir)
        summary.append({
            "eshop": eshop_name,
            "status": "ok" if (csv_path or json_path) else "missing_output",
            "latest_dir": latest_dir or "",
            "csv_path": csv_path or "",
            "json_path": json_path or "",
            "source_date": source_date.isoformat() if source_date else ""
        })

    return summary


def build_latest_record_index(records: Iterable[Dict[str, object]]) -> Dict[str, Dict[str, object]]:
    index: Dict[str, Dict[str, object]] = {}
    for record in records:
        name = str(record.get("name", ""))
        key = _normalize_name(name)
        if not key:
            continue
        existing = index.get(key)
        if not existing:
            index[key] = record
            continue
        if _record_is_newer(record, existing):
            index[key] = record
    return index


def _record_is_newer(candidate: Dict[str, object], existing: Dict[str, object]) -> bool:
    candidate_date = candidate.get("source_date")
    existing_date = existing.get("source_date")
    if isinstance(candidate_date, datetime) and isinstance(existing_date, datetime):
        return candidate_date > existing_date
    if isinstance(candidate_date, datetime) and not isinstance(existing_date, datetime):
        return True
    return False


def _load_csv_records(csv_path: str, eshop_name: str, latest_dir: Optional[str],
                      source_date: Optional[datetime]) -> List[Dict[str, object]]:
    records: List[Dict[str, object]] = []
    try:
        with open(csv_path, "r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=",", quotechar='"')
            for row in reader:
                name = (row.get("Name") or "").strip()
                if not name:
                    continue
                record = {
                    "name": name,
                    "short_description": row.get("Short Description", ""),
                    "description": row.get("Description", ""),
                    "main_photo": row.get("Main Photo Filepath", ""),
                    "gallery": row.get("Gallery Filepaths", ""),
                    "variants": row.get("Variants", ""),
                    "url": row.get("URL", ""),
                    "source_eshop": eshop_name,
                    "source_path": csv_path,
                    "source_dir": latest_dir,
                    "source_date": source_date,
                    "source_type": "csv"
                }
                records.append(record)
    except Exception as exc:
        logging.error("Failed to load CSV results %s: %s", csv_path, exc)
    return records


def _load_json_records(json_path: str, eshop_name: str, latest_dir: Optional[str],
                       source_date: Optional[datetime], language: str) -> List[Dict[str, object]]:
    records: List[Dict[str, object]] = []
    try:
        with open(json_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception as exc:
        logging.error("Failed to load JSON results %s: %s", json_path, exc)
        return records

    items = _extract_json_products(data)
    lang_key = language.lower()

    for item in items:
        translations = item.get("translations", {}) if isinstance(item, dict) else {}
        translation = translations.get(lang_key, {}) if isinstance(translations, dict) else {}
        name = (translation.get("name") or "").strip()
        if not name:
            continue

        record = {
            "name": name,
            "short_description": translation.get("annotation", ""),
            "description": translation.get("description", ""),
            "url": item.get("url") if isinstance(item, dict) else "",
            "catalog_number": item.get("catalogNumber") if isinstance(item, dict) else "",
            "manufacturer": (item.get("manufacturer", {}) or {}).get("name") if isinstance(item, dict) else "",
            "source_eshop": eshop_name,
            "source_path": json_path,
            "source_dir": latest_dir,
            "source_date": source_date,
            "source_type": "json"
        }
        records.append(record)

    return records


def _extract_json_products(data: object) -> List[Dict[str, object]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        if isinstance(data.get("data"), list):
            return [item for item in data.get("data", []) if isinstance(item, dict)]
        if isinstance(data.get("products"), list):
            return [item for item in data.get("products", []) if isinstance(item, dict)]
        if isinstance(data.get("items"), list):
            return [item for item in data.get("items", []) if isinstance(item, dict)]
        return [data]
    return []


def _extract_date_from_dir(directory: Optional[str]) -> Optional[datetime]:
    if not directory:
        return None
    base = os.path.basename(directory)
    if not base.startswith("Full_"):
        return None
    date_str = base.replace("Full_", "")
    try:
        return datetime.strptime(date_str, "%d.%m.%Y")
    except ValueError:
        return None


def _is_pincesobchod(eshop_name: str) -> bool:
    return "pincesobchod" in eshop_name.lower()


def normalize_key(value: str) -> str:
    return _normalize_name(value)
