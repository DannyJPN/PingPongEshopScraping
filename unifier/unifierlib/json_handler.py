import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

def parse_folder_date(folder_name: str) -> Optional[datetime]:
    """Parse date from Full_{date} folder name format."""
    try:
        if not folder_name.startswith('Full_'):
            return None
        date_str = folder_name[5:]  # Skip 'Full_'
        return datetime.strptime(date_str, '%d.%m.%Y')
    except ValueError as e:
        logging.debug(f"Failed to parse date from folder {folder_name}: {str(e)}", exc_info=True)
        return None

def find_newest_full_folder(pinces_path: Path) -> Optional[Path]:
    """Find the newest Full_{date} folder in PincesObchod directory."""
    try:
        full_folders = [
            d for d in pinces_path.iterdir()
            if d.is_dir() and d.name.startswith('Full_')
        ]

        if not full_folders:
            logging.debug(f"No Full_ folders found in {pinces_path}")
            return None

        # Parse dates and filter out invalid ones
        dated_folders = [
            (f, parse_folder_date(f.name))
            for f in full_folders
        ]
        valid_folders = [(f, d) for f, d in dated_folders if d is not None]

        if not valid_folders:
            logging.debug(f"No valid dated folders found in {pinces_path}")
            return None

        # Return folder with newest date
        newest_folder = max(valid_folders, key=lambda x: x[1])[0]
        logging.debug(f"Found newest folder: {newest_folder}")
        return newest_folder
    except Exception as e:
        logging.error(f"Error finding newest Full folder in {pinces_path}: {str(e)}", exc_info=True)
        return None

def find_newest_json(folder_path: Path) -> Optional[Path]:
    """Find newest JSON file by write time in given folder."""
    try:
        json_files = [
            f for f in folder_path.iterdir()
            if f.is_file() and f.suffix.lower() == '.json'
        ]

        if not json_files:
            logging.debug(f"No JSON files found in {folder_path}")
            return None

        # Return file with newest write time
        newest_file = max(json_files, key=lambda f: f.stat().st_mtime)
        logging.debug(f"Found newest JSON: {newest_file}")
        return newest_file
    except Exception as e:
        logging.error(f"Error finding newest JSON in {folder_path}: {str(e)}", exc_info=True)
        return None

def load_pinces_json(result_dir: Path, language_code: str) -> Optional[Dict[str, Any]]:
    """
    Find and load the newest JSON file from PincesObchod directory.
    
    Args:
        result_dir: Path to the result directory
        language_code: Language code (e.g. 'CS')
    
    Returns:
        Loaded JSON data or None if not found/error
    """
    try:
        logging.info(f"Looking for PincesObchod JSON in {result_dir} for language {language_code}")
        
        # Construct PincesObchod path
        pinces_path = result_dir / f"PincesObchod_{language_code}"
        
        if not pinces_path.exists():
            logging.error(f"PincesObchod directory not found: {pinces_path}")
            return None
            
        if not pinces_path.is_dir():
            logging.error(f"Path {pinces_path} is not a directory")
            return None

        # Find newest Full_{date} folder
        newest_full = find_newest_full_folder(pinces_path)
        if not newest_full:
            logging.error(f"No valid Full_ folder found in {pinces_path}")
            return None

        # Find newest JSON file
        newest_json = find_newest_json(newest_full)
        if not newest_json:
            logging.error(f"No JSON file found in {newest_full}")
            return None

        # Load and parse JSON
        logging.info(f"Loading JSON file: {newest_json}")
        try:
            with newest_json.open('r', encoding='utf-8') as f:
                data = json.load(f)

            # Count items in the first list found in the JSON values
            item_count = 0
            for value in data.values():
                if isinstance(value, list):
                    item_count = len(value)
                    break

            logging.info(f"Successfully loaded JSON data with {item_count} items")
            return data

        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON file {newest_json}: {str(e)}", exc_info=True)
            return None
        except UnicodeDecodeError as e:
            logging.error(f"Failed to read JSON file {newest_json} - encoding error: {str(e)}", exc_info=True)
            return None

    except Exception as e:
        logging.error(f"Error loading PincesObchod JSON: {str(e)}", exc_info=True)
        return None
