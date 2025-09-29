import os
import argparse
import logging
import json
from shared.logging_config import setup_logging
from shared.country_to_language import get_language_code
from shared.directory_manager import ensure_directories
from shared.json_downloader import download_json_file
from shared.json_processor import process_json_file  # Import the new function
from pincesobchodlib.constants import DEFAULT_RESULT_FOLDER, LOG_DIR, API_URL_PATTERN, JSON_FILENAME_PATTERN
from shared.utils import get_full_day_folder
from shared.utils import get_log_filename

def parse_arguments():
    parser = argparse.ArgumentParser(description="Pincesobchod Downloader Script")
    parser.add_argument('--result_folder', type=str, default=DEFAULT_RESULT_FOLDER, help='Root folder for script output')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing resources')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--country_code', type=str, default='cz', help='Country code (e.g., cz, sk, gb)')
    return parser.parse_args()

def main():
    # Parse command-line arguments
    args = parse_arguments()

    # Setup logging
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    # Generate the log filename
    LOG_FILE = get_log_filename(LOG_DIR)

    # Setup logging with the log file path
    setup_logging(args.debug, LOG_FILE)

    # Map country code to language code
    lang_code = get_language_code(args.country_code).upper()

    # Append language code to result folder path
    result_folder = f"{args.result_folder}_{lang_code}"

    # Ensure necessary directories are created
    ensure_directories(result_folder)
    logging.info("Directory structure ensured successfully.")

    # Build the JSON URL using the pattern from constants
    json_url = API_URL_PATTERN.format(COUNTRY_CODE=args.country_code.lower())
    
    # Build the JSON filename using the pattern from constants
    json_filename = JSON_FILENAME_PATTERN.format(LANGUAGE_CODE=lang_code)
    json_filepath = os.path.join(get_full_day_folder(result_folder), json_filename)
    
    # Download the JSON file
    download_json_file(json_url, json_filepath, lang_code, overwrite=args.overwrite)

    # Process the downloaded JSON file
    process_json_file(json_filepath, result_folder, lang_code, args.overwrite)

if __name__ == '__main__':
    main()
