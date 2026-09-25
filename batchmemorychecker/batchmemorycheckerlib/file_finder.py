"""Result file discovery utilities."""
from __future__ import annotations

import os
import re
import logging
from datetime import datetime
from typing import Optional, Tuple

from batchmemorycheckerlib.constants import RESULT_DATE_PREFIX, RESULT_DATE_FORMAT


def find_latest_dated_directory(base_dir: str) -> Optional[str]:
    if not os.path.exists(base_dir):
        logging.warning("Base directory does not exist: %s", base_dir)
        return None

    date_pattern = re.compile(r"^" + re.escape(RESULT_DATE_PREFIX) + r"(\d{2}\.\d{2}\.\d{4})$")
    dated_dirs = []

    try:
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if not os.path.isdir(item_path):
                continue
            match = date_pattern.match(item)
            if not match:
                continue
            date_str = match.group(1)
            try:
                date_obj = datetime.strptime(date_str, RESULT_DATE_FORMAT)
            except ValueError:
                logging.warning("Invalid date in directory name: %s", item)
                continue
            dated_dirs.append((date_obj, item_path))
    except Exception as exc:
        logging.error("Error scanning %s: %s", base_dir, exc)
        return None

    if not dated_dirs:
        logging.warning("No dated directories found in %s", base_dir)
        return None

    dated_dirs.sort(key=lambda entry: entry[0], reverse=True)
    return dated_dirs[0][1]


def find_output_files(eshop_dir: str, eshop_name: str, language: Optional[str] = None) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    latest_dir = find_latest_dated_directory(eshop_dir)
    if not latest_dir:
        logging.warning("No dated directory found for %s", eshop_name)
        return None, None, None

    if language:
        base_name = f"{eshop_name}Output_{language.upper()}"
    else:
        base_name = f"{eshop_name}Output"

    csv_filename = f"{base_name}.csv"
    json_filename = f"{base_name}.json"

    csv_path = os.path.join(latest_dir, csv_filename)
    json_path = os.path.join(latest_dir, json_filename)

    if not os.path.exists(csv_path) and not os.path.exists(json_path):
        csv_path, json_path = _try_alternative_names(latest_dir, eshop_name, language)

    final_csv = csv_path if csv_path and os.path.exists(csv_path) else None
    final_json = json_path if json_path and os.path.exists(json_path) else None

    return final_csv, final_json, latest_dir


def _try_alternative_names(directory: str, eshop_name: str, language: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    try:
        files_in_dir = os.listdir(directory)
    except Exception as exc:
        logging.error("Error listing files in %s: %s", directory, exc)
        return None, None

    patterns = [
        f"{eshop_name.lower()}output",
        f"{eshop_name.upper()}output",
        f"{eshop_name}output",
        f"output_{eshop_name.lower()}",
        f"results_{eshop_name.lower()}",
        f"export_{eshop_name.lower()}",
        f"{eshop_name.lower()}",
        f"{eshop_name.upper()}",
        f"{eshop_name}",
        "products",
        "results",
        "export",
        "output"
    ]

    if language:
        lang_patterns = [
            f"{eshop_name.lower()}output_{language.lower()}",
            f"{eshop_name.lower()}output_{language.upper()}",
            f"{eshop_name}output_{language}",
            f"{eshop_name.lower()}_{language.lower()}",
            f"{eshop_name.lower()}_{language.upper()}",
            f"{eshop_name}_{language}",
            f"products_{language.lower()}",
            f"results_{language.lower()}",
            f"export_{language.lower()}"
        ]
        patterns = lang_patterns + patterns

    csv_path = None
    json_path = None

    lower_files = {f.lower(): f for f in files_in_dir}

    for pattern in patterns:
        candidate = f"{pattern}.csv"
        match = lower_files.get(candidate.lower())
        if match:
            csv_path = os.path.join(directory, match)
            break

    for pattern in patterns:
        candidate = f"{pattern}.json"
        match = lower_files.get(candidate.lower())
        if match:
            json_path = os.path.join(directory, match)
            break

    return csv_path, json_path
