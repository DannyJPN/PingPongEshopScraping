import os
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

def parse_folder_date(folder_name: str) -> Optional[datetime]:
    """Parse date from Full_{date} folder name format."""
    try:
        # Extract date part after Full_
        if not folder_name.startswith('Full_'):
            return None
        date_str = folder_name[5:]  # Skip 'Full_'
        return datetime.strptime(date_str, '%d.%m.%Y')
    except ValueError as e:
        logging.debug(f"Failed to parse date from folder {folder_name}: {str(e)}", exc_info=True)
        return None

def find_newest_full_folder(eshop_path: Path) -> Optional[Path]:
    """Find the newest Full_{date} folder in given eshop directory."""
    try:
        full_folders = [
            d for d in eshop_path.iterdir()
            if d.is_dir() and d.name.startswith('Full_')
        ]

        if not full_folders:
            logging.debug(f"No Full_ folders found in {eshop_path}")
            return None

        # Parse dates and filter out invalid ones
        dated_folders = [
            (f, parse_folder_date(f.name))
            for f in full_folders
        ]
        valid_folders = [(f, d) for f, d in dated_folders if d is not None]

        if not valid_folders:
            logging.debug(f"No valid dated folders found in {eshop_path}")
            return None

        # Return folder with newest date
        newest_folder = max(valid_folders, key=lambda x: x[1])[0]
        logging.debug(f"Found newest folder: {newest_folder}")
        return newest_folder
    except Exception as e:
        logging.error(f"Error finding newest Full folder in {eshop_path}: {str(e)}", exc_info=True)
        return None

def find_newest_csv(folder_path: Path, eshop_name: str) -> Optional[Path]:
    """Find newest CSV file by write time in given folder."""
    try:
        expected_name = f"{eshop_name}Output.csv"
        csv_files = [
            f for f in folder_path.iterdir()
            if f.is_file() and f.name == expected_name
        ]

        if not csv_files:
            logging.debug(f"No matching CSV files found in {folder_path}")
            return None

        # Return file with newest write time
        newest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
        logging.debug(f"Found newest CSV: {newest_file}")
        return newest_file
    except Exception as e:
        logging.error(f"Error finding newest CSV in {folder_path}: {str(e)}", exc_info=True)
        return None

def scan_eshop_folders(result_dir: Path, valid_eshops: List[str]) -> List[Path]:
    """
    Scan ResultDir for eshop folders and find newest CSV files.
    Only processes folders whose names match the provided valid_eshops list.
    
    Args:
        result_dir: Path to the result directory
        valid_eshops: List of valid eshop names from EshopList.csv
    
    Returns:
        List of paths to newest CSV files
    """
    logging.info(f"Starting scan for eshop folders in {result_dir}")
    logging.debug(f"Valid eshops to scan: {valid_eshops}")
    csv_paths = []

    try:
        # Ensure result_dir exists
        if not result_dir.exists():
            logging.error(f"Result directory {result_dir} does not exist")
            return []

        if not result_dir.is_dir():
            logging.error(f"Path {result_dir} is not a directory")
            return []

        # Scan for eshop folders
        for eshop_dir in result_dir.iterdir():
            if not eshop_dir.is_dir():
                logging.debug(f"Skipping non-directory: {eshop_dir}")
                continue

            # Skip folders that don't match valid eshop names
            if eshop_dir.name not in valid_eshops:
                logging.debug(f"Skipping directory not in EshopList: {eshop_dir}")
                continue

            logging.debug(f"Processing valid eshop directory: {eshop_dir}")

            try:
                # Find newest Full_{date} folder
                newest_full = find_newest_full_folder(eshop_dir)
                if not newest_full:
                    logging.warning(f"No valid Full_ folder found in {eshop_dir}")
                    continue

                # Find newest CSV in that folder
                newest_csv = find_newest_csv(newest_full, eshop_dir.name)
                if newest_csv:
                    csv_paths.append(newest_csv)
                else:
                    logging.warning(f"No valid CSV file found in {newest_full}")

            except Exception as e:
                logging.error(f"Error processing eshop directory {eshop_dir}: {str(e)}", exc_info=True)
                continue

        logging.info(f"Scan complete. Found {len(csv_paths)} CSV files")
        for csv_path in csv_paths:
            logging.debug(f"Found CSV: {csv_path}")

        return csv_paths

    except Exception as e:
        logging.error(f"Error scanning eshop folders: {str(e)}", exc_info=True)
        return []
