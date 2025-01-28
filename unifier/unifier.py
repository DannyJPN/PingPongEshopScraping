import os
import sys
import argparse
import logging
from datetime import datetime
from tqdm import tqdm
from shared.logging_config import setup_logging
from shared.utils import get_log_filename
from unifierlib.file_validator import validate_file_system,validate_required_files
from shared.file_loader import load_supported_languages,load_json_file
from unifierlib.memory_loader import load_memory_files
from unifierlib.eshop_handler import load_eshop_names
from unifierlib.script_generator import generate_eshop_scripts
from unifierlib.parallel_executor import execute_scripts_in_parallel
from unifierlib.eshop_data_handler import load_eshop_csv_files,find_newest_eshop_csv_files,transform_csv_data,transform_json_data,find_newest_json_file
from unifierlib.downloaded_product import DownloadedProduct

from unifierlib.constants import (
    DEFAULT_LANGUAGE,
    DEFAULT_RESULT_DIR,
    DEFAULT_MEMORY_DIR,
    DEFAULT_EXPORT_DIR,
    DEFAULT_CONFIRM_AI_RESULTS,
    LOG_DIR
)

def validate_language(value):
    """Validate that language is a 2-character ISO 639-1 code and convert to uppercase."""
    try:
        value = value.upper()  # Convert to uppercase immediately
        if len(value) != 2:
            raise argparse.ArgumentTypeError(
                f"Language must be exactly 2 characters long, got {len(value)}"
            )
        return value
    except Exception as e:
        logging.error(f"Error validating language: {e}", exc_info=True)
        raise

def parse_arguments():
    """Parse and validate command line arguments."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(description="Desaka Unifier")

    parser.add_argument(
        "--Language",
        type=validate_language,
        default=DEFAULT_LANGUAGE,
        help=f"ISO 639-1 language code (2 characters). Default: {DEFAULT_LANGUAGE}"
    )

    parser.add_argument(
        "--ResultDir",
        type=str,
        default=DEFAULT_RESULT_DIR,
        help=f"Directory for results. Default: {DEFAULT_RESULT_DIR}"
    )

    # Update MemoryDir to be relative to script location
    default_memory_dir = os.path.join(script_dir, DEFAULT_MEMORY_DIR.lstrip("./"))
    parser.add_argument(
        "--MemoryDir",
        type=str,
        default=default_memory_dir,
        help=f"Directory for memory files. Default: {DEFAULT_MEMORY_DIR}"
    )

    parser.add_argument(
        "--ExportDir",
        type=str,
        default=DEFAULT_EXPORT_DIR,
        help=f"Directory for exports. Default: {DEFAULT_EXPORT_DIR}"
    )

    parser.add_argument(
        "--ConfirmAIResults",
        type=lambda x: x.lower() == 'true',
        default=DEFAULT_CONFIRM_AI_RESULTS,
        help=f"Whether to confirm AI results. Default: {DEFAULT_CONFIRM_AI_RESULTS}"
    )

    parser.add_argument(
        "--Debug",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    # Log the parsed arguments
    logging.debug(f"Parsed arguments: {vars(args)}")

    return args

def main():

    # Ensure the log directory exists
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        logging.debug(f"Created log directory: {LOG_DIR}")

    # Parse arguments first to get debug flag
    args = parse_arguments()

    # Generate the log filename
    log_file = get_log_filename(LOG_DIR)
    logging.debug(f"Generated log filename: {log_file}")

    # Setup logging with the log file path
    setup_logging(args.Debug, log_file)

    # Log script start time
    start_time = datetime.now()
    logging.info(f"Script started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Log script location and working directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logging.debug(f"Script location: {script_dir}")
    logging.debug(f"Current working directory: {os.getcwd()}")

    # Validate and ensure necessary directories exist
    validate_file_system(args.ResultDir, args.MemoryDir, args.ExportDir)

    # Load supported languages
    supported_languages = load_supported_languages(args.MemoryDir)

    # Validate the provided language argument against the supported languages
    if args.Language not in supported_languages:
        logging.error(f"Unsupported language: {args.Language}. Supported languages are: {supported_languages}")
        sys.exit(1)  # Exit the script with a non-zero status

    logging.info(f"Language '{args.Language}' is supported and validated successfully.")

    # Validate required files
    validate_required_files(args.MemoryDir)

    # Load memory files
    try:
        memory_files_data = load_memory_files(args.MemoryDir, args.Language)
        logging.info("All memory files loaded successfully.")
    except Exception as e:
        logging.error(f"Error loading or rewriting memory files: {e}", exc_info=True)
        sys.exit(1)

    # Load e-shop names and generate script names
    try:
        eshop_names = load_eshop_names(args.MemoryDir)
        logging.debug(f"Loaded e-shop names: {eshop_names}")
        script_names = generate_eshop_scripts(eshop_names)
    except Exception as e:
        logging.error(f"Error generating script names: {e}", exc_info=True)
        sys.exit(1)

    # Execute scripts in parallel using the encapsulated function
    execute_scripts_in_parallel(script_names)

    # Load eShop CSV files
    
    eshop_csv_paths = find_newest_eshop_csv_files(args.ResultDir,eshop_names)
    logging.debug(f"{type(eshop_csv_paths)} = {eshop_csv_paths}")
    csv_data=load_eshop_csv_files(eshop_csv_paths)
    downloaded_products = transform_csv_data(csv_data)
    logging.info(f"Downloaded products {len(downloaded_products)} items")
    # Load and transform JSON files
    pinces_json_path = find_newest_json_file(args.ResultDir, args.Language)
    json_data = load_json_file(pinces_json_path)['data']
    existing_products = transform_json_data(json_data)
    logging.info(f"Unified products {len(existing_products)} items.")

    # Log script end time
    end_time = datetime.now()
    logging.info(f"Script ended at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"Total execution time: {end_time - start_time}")

if __name__ == "__main__":
    main()