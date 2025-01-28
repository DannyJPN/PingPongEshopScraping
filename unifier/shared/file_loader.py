import os
import logging
import json
from datetime import datetime
from unifierlib.constants import SUPPORTED_LANGUAGES_FILE
import pandas as pd
from typing import Optional, List, Dict, Any



def load_supported_languages(memory_dir):
    """Load the supported languages from the SupportedLanguagesList.txt file."""
    file_path = os.path.join(memory_dir, SUPPORTED_LANGUAGES_FILE)
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            supported_languages = [line.strip() for line in file.readlines()]
        logging.info(f"Supported languages loaded: {supported_languages}")
        return supported_languages
    except FileNotFoundError:
        logging.error(f"Supported languages file not found: {file_path}")
        return []





def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    try:
        if not os.path.exists(file_path):
            error_msg = f"JSON file not found: {file_path}"
            logging.error(error_msg)
            raise FileNotFoundError(error_msg)

        logging.info(f"Loading JSON file: {file_path}")
       

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Log data characteristics for debugging
        if isinstance(data, dict):
            logging.debug(f"Loaded JSON data type: dict with {len(data)} keys")
            logging.debug(f"Available keys: {list(data.keys())}")
        elif isinstance(data, list):
            logging.debug(f"Loaded JSON data type: list with {len(data)} items")
            if data:
                logging.debug(f"First item type: {type(data[0])}")

        logging.info(f"Successfully loaded JSON file: {file_path}")
        return data

    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON format in file {file_path}: {str(e)}"
        logging.error(error_msg, exc_info=True)
        raise

    except UnicodeDecodeError as e:
        error_msg = f"Error decoding file {file_path} with encoding {encoding}: {str(e)}"
        logging.error(error_msg, exc_info=True)
        raise

    except Exception as e:
        error_msg = f"Error loading JSON file {file_path}: {str(e)}"
        logging.error(error_msg, exc_info=True)
        raise
        
import pandas as pd
import logging
from datetime import datetime
import shutil
import csv
import sys
import os


def load_csv_file(filepath):
    """Load a CSV file and return its content as a list of dictionaries."""
    try:
        # Log the file being loaded
        logging.info(f"Attempting to load CSV file: {filepath}")
        logging.debug(f"Using UTF-8 encoding for reading: {filepath}")

        # Load the CSV file with UTF-8 encoding
        df = pd.read_csv(filepath, na_filter=False, encoding='utf-8')

        data = df.to_dict(orient='records')
        logging.info(f"CSV file loaded successfully: {filepath} ({len(data)})")
        logging.debug(f"First few records: {data[:5]}")
        return data

    except pd.errors.EmptyDataError:
        logging.error(f"CSV file is empty or missing headers: {filepath}")
        raise

    except UnicodeDecodeError as e:
        logging.error(f"Unicode decode error while reading {filepath}. File must be in UTF-8 format. Error: {str(e)}", exc_info=True)
        raise

    except Exception as e:
        logging.error(f"Error loading CSV file: {filepath}. Error: {str(e)}", exc_info=True)
        raise

def save_csv_file(csv_data, filepath):
    """Save data to a CSV file in UTF-8 format with backup creation."""
    try:
        # Create backup of existing file
        if os.path.exists(filepath):
            backup_filepath = f"{filepath}.{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv_old"
            shutil.copy(filepath, backup_filepath)
            logging.info(f"Backup of the original file created: {backup_filepath}")

        df = pd.DataFrame(csv_data)

        # Log the first few rows of the DataFrame to verify data integrity
        logging.debug(f"Data being saved: {df.head()}")
        logging.debug(f"Saving CSV with UTF-8 encoding to: {filepath}")

        # Save with UTF-8 encoding
        df.to_csv(filepath, index=False, quotechar='"', quoting=csv.QUOTE_ALL, encoding='utf-8')
        logging.info(f"CSV file saved successfully in UTF-8 format: {filepath}")

    except PermissionError as e:
        logging.error(f"Permission denied while saving file {filepath}. Error: {str(e)}", exc_info=True)
        sys.exit(1)
    except OSError as e:
        logging.error(f"OS error while saving file {filepath}. Error: {str(e)}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error saving CSV file {filepath}. Error: {str(e)}", exc_info=True)
        sys.exit(1)

