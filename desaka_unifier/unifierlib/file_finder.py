"""
File finder utilities for desaka_unifier project.
Contains logic for finding files in dated subdirectories and determining latest versions.
"""

import os
import re
import logging
from datetime import datetime
from typing import List, Optional, Tuple


def find_latest_dated_directory(base_dir: str) -> Optional[str]:
    """
    Find the directory with the latest date in format Full_DD.MM.YYYY.

    Args:
        base_dir (str): Base directory to search in

    Returns:
        Optional[str]: Path to the latest dated directory or None if not found
    """
    if not os.path.exists(base_dir):
        logging.warning(f"Base directory does not exist: {base_dir}")
        return None

    dated_dirs = []
    date_pattern = re.compile(r'^Full_(\d{2})\.(\d{2})\.(\d{4})$')

    try:
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path):
                match = date_pattern.match(item)
                if match:
                    day, month, year = match.groups()
                    try:
                        # Parse date to validate and for sorting
                        date_obj = datetime(int(year), int(month), int(day))
                        dated_dirs.append((date_obj, item_path, item))
                    except ValueError:
                        logging.warning(f"Invalid date in directory name: {item}")
                        continue

        if not dated_dirs:
            logging.warning(f"No dated directories found in {base_dir}")
            return None

        # Sort by date and return the latest
        dated_dirs.sort(key=lambda x: x[0], reverse=True)
        latest_dir = dated_dirs[0][1]
        latest_name = dated_dirs[0][2]

        logging.debug(f"Found latest dated directory: {latest_name} in {base_dir}")
        return latest_dir

    except Exception as e:
        logging.error(f"Error finding dated directories in {base_dir}: {str(e)}")
        return None


def find_output_files(eshop_dir: str, eshop_name: str, language: str = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Find CSV and JSON output files for an eshop in the latest dated directory.
    Files should be named NázevEshopuOutput[_JAZYK].csv/json

    Args:
        eshop_dir (str): Eshop directory path
        eshop_name (str): Name of the eshop
        language (str, optional): Language code for pincesobchod files

    Returns:
        Tuple[Optional[str], Optional[str]]: (csv_path, json_path) or (None, None) if not found
    """
    # First find the latest dated directory
    latest_dir = find_latest_dated_directory(eshop_dir)
    if not latest_dir:
        logging.warning(f"No dated directory found for {eshop_name}")
        return None, None

    # Determine expected file names
    if eshop_name.lower() in ['pincesobchod', 'pincesobchod_cs', 'pincesobchod_sk'] or 'pincesobchod' in eshop_name.lower():
        # For pincesobchod, include language in filename
        if language:
            base_name = f"{eshop_name}Output_{language.upper()}"
        else:
            base_name = f"{eshop_name}Output"
    else:
        base_name = f"{eshop_name}Output"

    csv_filename = f"{base_name}.csv"
    json_filename = f"{base_name}.json"

    csv_path = os.path.join(latest_dir, csv_filename)
    json_path = os.path.join(latest_dir, json_filename)

    # Check if files exist
    csv_exists = os.path.exists(csv_path)
    json_exists = os.path.exists(json_path)

    if not csv_exists and not json_exists:
        # Try alternative naming patterns
        csv_path, json_path = _try_alternative_names(latest_dir, eshop_name, language)

    # Return paths (None if file doesn't exist)
    final_csv = csv_path if csv_path and os.path.exists(csv_path) else None
    final_json = json_path if json_path and os.path.exists(json_path) else None

    if final_csv:
        logging.debug(f"Found CSV file: {final_csv}")
    if final_json:
        logging.debug(f"Found JSON file: {final_json}")

    if not final_csv and not final_json:
        logging.warning(f"No output files found for {eshop_name} in {latest_dir}")

    return final_csv, final_json


def _try_alternative_names(directory: str, eshop_name: str, language: str = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Try alternative naming patterns for output files.

    Args:
        directory (str): Directory to search in
        eshop_name (str): Eshop name
        language (str, optional): Language code

    Returns:
        Tuple[Optional[str], Optional[str]]: (csv_path, json_path) or (None, None)
    """
    try:
        files_in_dir = os.listdir(directory)
    except Exception as e:
        logging.error(f"Error listing files in {directory}: {str(e)}")
        return None, None

    # Alternative patterns to try
    patterns = [
        f"{eshop_name.lower()}output",
        f"{eshop_name.upper()}output",
        f"{eshop_name}output",
        f"output_{eshop_name.lower()}",
        f"results_{eshop_name.lower()}",
        f"export_{eshop_name.lower()}",
        f"{eshop_name.lower()}",  # Just the eshop name
        f"{eshop_name.upper()}",  # Just the eshop name uppercase
        f"{eshop_name}",          # Just the eshop name as-is
        "products",
        "results",
        "export",
        "output"
    ]

    if language:
        # Add language-specific patterns
        lang_patterns = [
            f"{eshop_name.lower()}output_{language.lower()}",
            f"{eshop_name.lower()}output_{language.upper()}",
            f"{eshop_name}output_{language}",
            f"{eshop_name.lower()}_{language.lower()}",  # eshop_language format
            f"{eshop_name.lower()}_{language.upper()}",  # eshop_LANGUAGE format
            f"{eshop_name}_{language}",                  # EshopName_LANGUAGE format
            f"products_{language.lower()}",
            f"results_{language.lower()}",
            f"export_{language.lower()}"
        ]
        patterns = lang_patterns + patterns

    csv_path = None
    json_path = None

    # Look for CSV files
    for pattern in patterns:
        csv_filename = f"{pattern}.csv"
        if csv_filename.lower() in [f.lower() for f in files_in_dir]:
            # Find the actual filename with correct case
            for f in files_in_dir:
                if f.lower() == csv_filename.lower():
                    csv_path = os.path.join(directory, f)
                    break
            if csv_path:
                break

    # Look for JSON files
    for pattern in patterns:
        json_filename = f"{pattern}.json"
        if json_filename.lower() in [f.lower() for f in files_in_dir]:
            # Find the actual filename with correct case
            for f in files_in_dir:
                if f.lower() == json_filename.lower():
                    json_path = os.path.join(directory, f)
                    break
            if json_path:
                break

    return csv_path, json_path


def list_all_dated_directories(base_dir: str) -> List[Tuple[datetime, str]]:
    """
    List all dated directories in format Full_DD.MM.YYYY with their dates.

    Args:
        base_dir (str): Base directory to search in

    Returns:
        List[Tuple[datetime, str]]: List of (date, directory_path) tuples sorted by date (newest first)
    """
    if not os.path.exists(base_dir):
        logging.warning(f"Base directory does not exist: {base_dir}")
        return []

    dated_dirs = []
    date_pattern = re.compile(r'^Full_(\d{2})\.(\d{2})\.(\d{4})$')

    try:
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path):
                match = date_pattern.match(item)
                if match:
                    day, month, year = match.groups()
                    try:
                        date_obj = datetime(int(year), int(month), int(day))
                        dated_dirs.append((date_obj, item_path))
                    except ValueError:
                        logging.warning(f"Invalid date in directory name: {item}")
                        continue

        # Sort by date (newest first)
        dated_dirs.sort(key=lambda x: x[0], reverse=True)
        return dated_dirs

    except Exception as e:
        logging.error(f"Error listing dated directories in {base_dir}: {str(e)}")
        return []


def find_files_by_pattern(directory: str, pattern: str) -> List[str]:
    """
    Find files matching a pattern in a directory.

    Args:
        directory (str): Directory to search in
        pattern (str): Pattern to match (supports wildcards)

    Returns:
        List[str]: List of matching file paths
    """
    import glob

    if not os.path.exists(directory):
        return []

    search_pattern = os.path.join(directory, pattern)
    try:
        matching_files = glob.glob(search_pattern)
        return matching_files
    except Exception as e:
        logging.error(f"Error finding files with pattern '{pattern}' in {directory}: {str(e)}")
        return []
