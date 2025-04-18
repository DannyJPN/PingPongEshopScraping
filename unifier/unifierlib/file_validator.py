import os
import logging
import sys
from shared.file_loader import load_csv_file
from pathlib import Path
from unifierlib.constants import SUPPORTED_LANGUAGES_FILE
from unifierlib.constants import (
    BRAND_CODE_LIST,
    CATEGORY_CODE_LIST,
    CATEGORY_SUB_CODE_LIST,
    CATEGORY_LIST,
    CATEGORY_ID_LIST,
    DEFAULT_UNIFIED_PRODUCT_VALUES,
    CATEGORY_MAPPING_HEUREKA_PREFIX,
    CATEGORY_MAPPING_ZBOZI_PREFIX,
    CATEGORY_MAPPING_GLAMI_PREFIX,
    CATEGORY_MAPPING_GOOGLE_PREFIX
)



def ensure_directory_exists(directory_path: str) -> None:
    """
    Ensure that the specified directory exists, create if it doesn't.

    Args:
        directory_path: Path to the directory to check/create
    """
    try:
        path = Path(directory_path)
        if not path.exists():
            path.mkdir(parents=True)
            logging.info(f"Created directory: {directory_path}")
        else:
            logging.debug(f"Directory already exists: {directory_path}")
    except Exception as e:
        logging.error(f"Failed to create directory {directory_path}: {str(e)}", exc_info=True)
        raise

def create_supported_languages_list(memory_dir: str) -> None:
    """
    Create SupportedLanguagesList.txt with default 'CS' content if it doesn't exist or is empty.

    Args:
        memory_dir: Path to the memory directory
    """
    try:
        languages_file = Path(memory_dir) / SUPPORTED_LANGUAGES_FILE
        if not languages_file.exists() or languages_file.stat().st_size == 0:
            languages_file.write_text("CS")
            if not languages_file.exists():
                logging.info(f"Created {SUPPORTED_LANGUAGES_FILE} with default content 'CS'")
            else:
                logging.info(f"Updated {SUPPORTED_LANGUAGES_FILE} with default content 'CS' as it was empty")
        else:
            logging.debug(f"{SUPPORTED_LANGUAGES_FILE} already exists and is not empty at {languages_file}")
    except Exception as e:
        logging.error(f"Failed to create or update {SUPPORTED_LANGUAGES_FILE}: {str(e)}", exc_info=True)
        raise

def validate_file_system(result_dir: str, memory_dir: str, export_dir: str) -> None:
    """
    Validate and create necessary directories and files.

    Args:
        result_dir: Path to results directory
        memory_dir: Path to memory directory
        export_dir: Path to export directory
    """
    try:
        logging.info("Starting file system validation...")

        # Ensure all required directories exist
        directories = {
            "Results": result_dir,
            "Memory": memory_dir,
            "Export": export_dir
        }

        for dir_name, directory in directories.items():
            logging.debug(f"Validating {dir_name} directory: {directory}")
            ensure_directory_exists(directory)

        # Create SupportedLanguagesList.txt if it doesn't exist or is empty
        create_supported_languages_list(memory_dir)

        logging.info("File system validation completed successfully")
    except Exception as e:
        logging.error(f"File system validation failed: {str(e)}", exc_info=True)
        raise

def validate_required_files(memory_dir):
    required_files = [
        BRAND_CODE_LIST,
        CATEGORY_CODE_LIST,
        CATEGORY_SUB_CODE_LIST,
        CATEGORY_LIST,
        CATEGORY_ID_LIST,
        DEFAULT_UNIFIED_PRODUCT_VALUES
    ]

    # Add category mapping files
    category_mapping_files = [
        f"{CATEGORY_MAPPING_HEUREKA_PREFIX}.csv",
        f"{CATEGORY_MAPPING_ZBOZI_PREFIX}.csv",
        f"{CATEGORY_MAPPING_GLAMI_PREFIX}.csv",
        f"{CATEGORY_MAPPING_GOOGLE_PREFIX}.csv"
    ]

    required_files.extend(category_mapping_files)

    missing_files = []

    for file_name in required_files:
        file_path = os.path.join(memory_dir, file_name)
        if not os.path.exists(file_path):
            missing_files.append(file_name)
            logging.warning(f"Missing required file: {file_name}")
        else:
            try:
                if file_name.endswith('.csv'):
                    data = load_csv_file(file_path)
                    logging.info(f"Loaded {len(data)} entries from {file_name}")
                elif file_name.endswith('.txt'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        logging.info(f"Loaded {len(lines)} entries from {file_name}")
            except Exception as e:
                logging.error(f"Error loading file: {file_name}. Error: {e}", exc_info=True)
                sys.exit(1)

    if missing_files:
        missing_files_str = ', '.join(missing_files)
        logging.error(f"Missing required files: {missing_files_str}. Terminating the script.")
        sys.exit(1)
