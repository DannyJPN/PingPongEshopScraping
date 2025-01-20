import os
import logging
from pathlib import Path
from unifierlib.constants import SUPPORTED_LANGUAGES_LIST

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
    Create SupportedLanguagesList.txt with default 'CS' content if it doesn't exist.

    Args:
        memory_dir: Path to the memory directory
    """
    try:
        languages_file = Path(memory_dir) / SUPPORTED_LANGUAGES_LIST
        if not languages_file.exists():
            languages_file.write_text("CS")
            logging.info(f"Created {SUPPORTED_LANGUAGES_LIST} with default content 'CS'")
        else:
            logging.debug(f"{SUPPORTED_LANGUAGES_LIST} already exists at {languages_file}")
    except Exception as e:
        logging.error(f"Failed to create {SUPPORTED_LANGUAGES_LIST}: {str(e)}", exc_info=True)
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

        # Create SupportedLanguagesList.txt if it doesn't exist
        create_supported_languages_list(memory_dir)

        logging.info("File system validation completed successfully")
    except Exception as e:
        logging.error(f"File system validation failed: {str(e)}", exc_info=True)
        raise
