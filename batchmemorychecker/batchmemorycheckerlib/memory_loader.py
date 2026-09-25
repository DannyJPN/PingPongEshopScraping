"""Memory file loader for batch processing."""
from __future__ import annotations

import csv
import logging
import os
from typing import Dict, Iterable, List

from batchmemorycheckerlib.constants import MEMORY_SUFFIX


def list_memory_files(memory_dir: str, allowed_files: List[str] | None = None) -> List[str]:
    if not os.path.exists(memory_dir):
        logging.warning("Memory directory not found: %s", memory_dir)
        return []

    allowed_set = None
    if allowed_files:
        allowed_set = {os.path.basename(item) for item in allowed_files}

    files = []
    for name in os.listdir(memory_dir):
        if not name.endswith(MEMORY_SUFFIX):
            continue
        if allowed_set is not None and name not in allowed_set:
            continue
        path = os.path.join(memory_dir, name)
        if os.path.isfile(path):
            files.append(path)
    files.sort()
    return files


def iter_memory_entries(memory_path: str) -> Iterable[Dict[str, object]]:
    with open(memory_path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=",", quotechar='"')
        row_index = 0
        for row in reader:
            row_index += 1
            key = (row.get("KEY") or "").strip()
            value = (row.get("VALUE") or "").strip()
            yield {
                "row_index": row_index,
                "key": key,
                "value": value,
                "raw_row": row
            }


def get_memory_row_count(memory_path: str) -> int:
    try:
        with open(memory_path, "r", encoding="utf-8-sig", newline="") as handle:
            return max(0, sum(1 for _ in handle) - 1)
    except Exception as exc:
        logging.warning("Failed to count rows for %s: %s", memory_path, exc)
        return 0
