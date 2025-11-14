import os
import logging
import json
from datetime import datetime
from unifierlib.constants import SUPPORTED_LANGUAGES_FILE
import pandas as pd
from typing import Optional, List, Dict, Any


def ensure_directory_exists(directory_path: str) -> bool:
    """
    Ensure that a single directory exists. Create it if it doesn't exist.

    Args:
        directory_path (str): Path to the directory to check/create

    Returns:
        bool: True if directory exists or was created successfully, False otherwise
    """
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path, exist_ok=True)
            logging.info(f"Created directory: {directory_path}")
        else:
            logging.debug(f"Directory already exists: {directory_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to create directory {directory_path}: {str(e)}", exc_info=True)
        return False


def load_txt_file(file_path: str) -> List[str]:
    """
    Load a text file and return its content as a list of lines.

    Args:
        file_path (str): Path to the text file

    Returns:
        List[str]: List of lines from the file (stripped of whitespace)
    """
    try:
        if not os.path.exists(file_path):
            error_msg = f"Text file not found: {file_path}"
            logging.error(error_msg)
            raise FileNotFoundError(error_msg)

        logging.debug(f"Loading text file: {file_path}")

        # Try different encodings
        encodings_to_try = ['utf-8', 'utf-8-sig', 'utf-16', 'utf-16-le', 'utf-16-be', 'cp1252', 'iso-8859-1', 'windows-1252']

        for encoding in encodings_to_try:
            try:
                logging.debug(f"Trying {encoding} encoding for reading: {file_path}")
                with open(file_path, 'r', encoding=encoding) as f:
                    lines = [line.strip() for line in f.readlines() if line.strip()]

                logging.info(f"Successfully loaded text file: {file_path} ({len(lines)} lines) using {encoding} encoding")
                return lines

            except UnicodeDecodeError:
                logging.debug(f"Failed to read with {encoding} encoding, trying next...")
                continue

        # If all encodings failed
        error_msg = f"Failed to read {file_path} with any supported encoding"
        logging.error(error_msg)
        raise UnicodeDecodeError(error_msg)

    except Exception as e:
        error_msg = f"Error loading text file {file_path}: {str(e)}"
        logging.error(error_msg, exc_info=True)
        raise


def append_to_txt_file(file_path: str, lines: List[str]) -> None:
    """
    Append lines to a text file in UTF-8 format.

    Args:
        file_path (str): Path to the text file
        lines (List[str]): Lines to append to the file
    """
    try:
        logging.debug(f"Appending {len(lines)} lines to text file: {file_path}")

        # Ensure the parent directory exists
        parent_dir = os.path.dirname(file_path)
        if parent_dir and not os.path.exists(parent_dir):
            ensure_directory_exists(parent_dir)

        # Append with UTF-8 encoding
        with open(file_path, 'a', encoding='utf-8') as f:
            for line in lines:
                f.write(f"{line}\n")

        logging.debug(f"Successfully appended {len(lines)} lines to: {file_path}")

    except PermissionError as e:
        logging.error(f"Permission denied while appending to file {file_path}. Error: {str(e)}", exc_info=True)
        raise
    except OSError as e:
        if e.errno == 28:  # ENOSPC - No space left on device
            logging.error(f"Disk full while appending to file {file_path}. Error: {str(e)}", exc_info=True)
        else:
            logging.error(f"OS error while appending to file {file_path}. Error: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logging.error(f"Error appending to text file {file_path}. Error: {str(e)}", exc_info=True)
        raise


def append_to_csv_file(file_path: str, data: Any) -> None:
    """
    Append data to a CSV file in UTF-8 format.
    Creates file with header if it doesn't exist.

    Args:
        file_path (str): Path to the CSV file
        data: Dictionary or list of dictionaries to append
    """
    import csv

    try:
        # Normalize data to list of dicts
        if isinstance(data, dict):
            rows = [data]
        elif isinstance(data, list):
            rows = data
        else:
            raise ValueError(f"Data must be dict or list of dicts, got {type(data)}")

        if not rows:
            return

        # Ensure the parent directory exists
        parent_dir = os.path.dirname(file_path)
        if parent_dir and not os.path.exists(parent_dir):
            ensure_directory_exists(parent_dir)

        # Get fieldnames from first row
        fieldnames = list(rows[0].keys())

        # Check if file exists to determine if we need to write header
        file_exists = os.path.exists(file_path)

        logging.debug(f"Appending {len(rows)} row(s) to CSV file: {file_path}")

        # Append with UTF-8 encoding
        with open(file_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, quotechar='"', quoting=csv.QUOTE_ALL)

            # Write header only if file is new
            if not file_exists:
                writer.writeheader()
                logging.debug(f"Created new CSV file with header: {file_path}")

            # Write data rows
            writer.writerows(rows)

        logging.debug(f"Successfully appended {len(rows)} row(s) to: {file_path}")

    except PermissionError as e:
        logging.error(f"Permission denied while appending to CSV file {file_path}. Error: {str(e)}", exc_info=True)
        raise
    except OSError as e:
        if e.errno == 28:  # ENOSPC - No space left on device
            logging.error(f"Disk full while appending to CSV file {file_path}. Error: {str(e)}", exc_info=True)
        else:
            logging.error(f"OS error while appending to CSV file {file_path}. Error: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logging.error(f"Error appending to CSV file {file_path}. Error: {str(e)}", exc_info=True)
        raise





def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    try:
        if not os.path.exists(file_path):
            error_msg = f"JSON file not found: {file_path}"
            logging.error(error_msg)
            raise FileNotFoundError(error_msg)

        logging.debug(f"Loading JSON file: {file_path}")

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
        error_msg = f"Error decoding file {file_path} with encoding utf-8: {str(e)}"
        logging.error(error_msg, exc_info=True)
        raise

    except Exception as e:
        error_msg = f"Error loading JSON file {file_path}: {str(e)}"
        logging.error(error_msg, exc_info=True)
        raise


def load_csv_file(filepath):
    """Load a CSV file and return its content as a list of dictionaries."""
    try:
        # Log the file being loaded
        logging.debug(f"Attempting to load CSV file: {filepath}")
        logging.debug(f"Using UTF-8 encoding for reading: {filepath}")

        # Try different encodings
        encodings_to_try = ['utf-8', 'utf-8-sig', 'utf-16', 'utf-16-le', 'utf-16-be', 'cp1252', 'iso-8859-1', 'windows-1252']

        for encoding in encodings_to_try:
            try:
                logging.debug(f"Trying {encoding} encoding for reading: {filepath}")
                df = pd.read_csv(filepath, na_filter=False, encoding=encoding)

                data = df.to_dict(orient='records')
                logging.debug(f"CSV file loaded successfully: {filepath} ({len(data)} records) using {encoding} encoding")
                logging.debug(f"First few records: {data[:5]}")
                return data

            except UnicodeDecodeError:
                logging.debug(f"Failed to read with {encoding} encoding, trying next...")
                continue

        # If all encodings failed
        logging.error(f"Failed to read {filepath} with any supported encoding")
        raise UnicodeDecodeError("Failed to decode file with any supported encoding")

    except pd.errors.EmptyDataError:
        logging.error(f"CSV file is empty or missing headers: {filepath}")
        raise

    except Exception as e:
        logging.error(f"Error loading CSV file: {filepath}. Error: {str(e)}", exc_info=True)
        raise


def save_csv_file(csv_data, filepath):
    """
    Save data to a CSV file in UTF-8 format with atomic write and backup creation.

    Uses atomic write pattern: write to temp file, then rename.
    This prevents corruption if the write fails partway through.
    Backup provides additional safety in case of errors.
    """
    import csv
    import shutil
    import tempfile

    temp_fd = None
    temp_path = None

    try:
        # Create backup of existing file
        if os.path.exists(filepath):
            backup_filepath = f"{filepath}.{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv_old"
            shutil.copy(filepath, backup_filepath)
            logging.debug(f"Backup of the original file created: {backup_filepath}")

        # Ensure parent directory exists
        parent_dir = os.path.dirname(filepath)
        if parent_dir and not os.path.exists(parent_dir):
            ensure_directory_exists(parent_dir)

        df = pd.DataFrame(csv_data)

        # Log the first few rows of the DataFrame to verify data integrity
        logging.debug(f"Data being saved: {df.head()}")
        logging.debug(f"Saving CSV with UTF-8 encoding to: {filepath}")

        # Atomic write: write to temporary file first
        temp_fd, temp_path = tempfile.mkstemp(
            dir=parent_dir if parent_dir else '.',
            prefix='.tmp_',
            suffix='.csv'
        )

        try:
            # Write to temp file via pandas
            df.to_csv(temp_path, index=False, quotechar='"', quoting=csv.QUOTE_ALL, encoding='utf-8')

            # Ensure data is written to disk
            os.fsync(temp_fd)

        finally:
            os.close(temp_fd)
            temp_fd = None

        # Atomic rename: replace original file with temp file
        # This is atomic on POSIX systems and safe on Windows
        shutil.move(temp_path, filepath)
        temp_path = None

        logging.debug(f"CSV file saved successfully in UTF-8 format: {filepath}")

    except PermissionError as e:
        logging.error(f"Permission denied while saving file {filepath}. Error: {str(e)}", exc_info=True)
        raise
    except OSError as e:
        if e.errno == 28:  # ENOSPC - No space left on device
            logging.error(f"Disk full while saving file {filepath}. Error: {str(e)}", exc_info=True)
        else:
            logging.error(f"OS error while saving file {filepath}. Error: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logging.error(f"Error saving CSV file {filepath}. Error: {str(e)}", exc_info=True)
        raise
    finally:
        # Cleanup: remove temp file if it exists
        if temp_fd is not None:
            try:
                os.close(temp_fd)
            except:
                pass
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logging.debug(f"Cleaned up temp file: {temp_path}")
            except:
                pass


def save_json_file(data: Dict[str, Any], filepath: str) -> None:
    """Save data to a JSON file in UTF-8 format with backup creation."""
    try:
        # Create backup of existing file
        if os.path.exists(filepath):
            backup_filepath = f"{filepath}.{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json_old"
            import shutil
            shutil.copy(filepath, backup_filepath)
            logging.debug(f"Backup of the original file created: {backup_filepath}")

        logging.debug(f"Saving JSON with UTF-8 encoding to: {filepath}")

        # Save with UTF-8 encoding
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"JSON file saved successfully in UTF-8 format: {filepath}")

    except PermissionError as e:
        logging.error(f"Permission denied while saving file {filepath}. Error: {str(e)}", exc_info=True)
        raise
    except OSError as e:
        if e.errno == 28:  # ENOSPC - No space left on device
            logging.error(f"Disk full while saving file {filepath}. Error: {str(e)}", exc_info=True)
        else:
            logging.error(f"OS error while saving file {filepath}. Error: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logging.error(f"Error saving JSON file {filepath}. Error: {str(e)}", exc_info=True)
        raise


def save_jsonl_file(data: List[Dict[str, Any]], filepath: str) -> None:
    """Save data to a JSONL file (JSON Lines format) in UTF-8 format."""
    try:
        # Create backup of existing file
        if os.path.exists(filepath):
            backup_filepath = f"{filepath}.{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jsonl_old"
            import shutil
            shutil.copy(filepath, backup_filepath)
            logging.debug(f"Backup of the original file created: {backup_filepath}")

        logging.debug(f"Saving JSONL with UTF-8 encoding to: {filepath}")

        # Save with UTF-8 encoding - each line is a separate JSON object
        with open(filepath, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        logging.info(f"JSONL file saved successfully in UTF-8 format: {filepath}")

    except PermissionError as e:
        logging.error(f"Permission denied while saving file {filepath}. Error: {str(e)}", exc_info=True)
        raise
    except OSError as e:
        if e.errno == 28:  # ENOSPC - No space left on device
            logging.error(f"Disk full while saving file {filepath}. Error: {str(e)}", exc_info=True)
        else:
            logging.error(f"OS error while saving file {filepath}. Error: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logging.error(f"Error saving JSONL file {filepath}. Error: {str(e)}", exc_info=True)
        raise
