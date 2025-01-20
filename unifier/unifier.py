import os
import sys
import argparse
import logging
from pathlib import Path
from shared.logging_config import setup_logging
from shared.csv_handler import load_csv, save_csv
from shared.utils import get_log_filename
from unifierlib.file_validator import validate_file_system
from unifierlib.memory_files import create_memory_files
from unifierlib.eshop_handler import process_eshop_list, generate_script_name
from unifierlib.script_executor import execute_scripts_parallel
from unifierlib.eshop_scanner import scan_eshop_folders
from unifierlib.json_handler import load_pinces_json
from unifierlib.product_transformer import ProductTransformer
from unifierlib.constants import (
    DEFAULT_LANGUAGE,
    DEFAULT_RESULT_DIR,
    DEFAULT_MEMORY_DIR,
    DEFAULT_EXPORT_DIR,
    DEFAULT_CONFIRM_AI_RESULTS,
    DEFAULT_UNIFIED_PRODUCT_VALUES,
    LOG_DIR
)

def validate_language(value):
    """Validate that language is 2 characters and convert to uppercase."""
    value = value.upper()
    if len(value) != 2:
        raise argparse.ArgumentTypeError(
            f"Language must be exactly 2 characters long, got {len(value)}"
        )
    return value

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
    try:
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

        # Log script location and working directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logging.debug(f"Script location: {script_dir}")
        logging.debug(f"Current working directory: {os.getcwd()}")

        # Log all arguments after logging is configured
        logging.debug("Application started with arguments:")
        for arg, value in vars(args).items():
            logging.debug(f"{arg}: {value}")

        # Validate and create necessary directories and files
        logging.debug("Starting file system validation...")
        validate_file_system(args.ResultDir, args.MemoryDir, args.ExportDir)
        logging.debug("File system validation completed successfully")

        # Create memory files for all supported languages
        logging.debug("Starting memory files creation...")
        create_memory_files(args.MemoryDir)
        logging.debug("Memory files creation completed successfully")

        # Create download scripts for eshops
        logging.debug("Starting eshop scripts creation...")
        process_eshop_list(args.MemoryDir, script_dir)
        logging.debug("Eshop scripts creation completed successfully")

        # Load eshop list for parallel execution
        eshop_list_path = os.path.join(args.MemoryDir, "EshopList.csv")
        logging.debug(f"Loading eshop list from {eshop_list_path}")
        eshops, _ = load_csv(eshop_list_path)
        logging.debug(f"Loaded {len(eshops)} eshops from EshopList.csv")

        # Execute download scripts in parallel
        logging.debug("Starting parallel execution of download scripts...")
        script_paths = [
            os.path.join(script_dir, generate_script_name(eshop['Name']))
            for eshop in eshops
        ]
        execution_results = execute_scripts_parallel(script_paths)

        # Log execution results
        successful = sum(1 for r in execution_results if r['status'] == 'completed' and r['returncode'] == 0)
        failed = len(execution_results) - successful
        logging.debug(f"Script execution completed: {successful} successful, {failed} failed")

        # Log detailed results for each script
        for result in execution_results:
            if result['status'] == 'completed' and result['returncode'] == 0:
                logging.debug(f"Script {result['script']} completed successfully")
            else:
                logging.error(
                    f"Script {result['script']} failed with status {result['status']}"
                    f"{f', error: {result['error']}' if result['error'] else ''}"
                )

        # Scan for newest CSV files in eshop folders
        logging.info("Starting to scan for newest CSV files in eshop folders...")
        result_dir = Path(args.ResultDir)
        valid_eshops = [eshop['Name'] for eshop in eshops]
        logging.debug(f"Valid eshop names: {valid_eshops}")
        csv_files = scan_eshop_folders(result_dir, valid_eshops)

        if not csv_files:
            logging.error("No CSV files found in eshop folders")
            return

        logging.info(f"Found {len(csv_files)} CSV files to process")
        for csv_file in csv_files:
            logging.debug(f"Found CSV: {csv_file}")

        # Load PincesObchod JSON data
        logging.info("Loading PincesObchod JSON data...")
        json_data = load_pinces_json(result_dir, args.Language.upper())
        if not json_data:
            logging.error("Failed to load PincesObchod JSON data")
            return

        logging.info(f"Successfully loaded PincesObchod JSON with {len(json_data)} items")

        # Transform JSON data into UnifiedExportProduct objects
        try:
            default_values_path = Path(args.MemoryDir) / DEFAULT_UNIFIED_PRODUCT_VALUES
            transformer = ProductTransformer(default_values_path)
            logging.info("Created ProductTransformer instance")

            # Get list of products from JSON
            products_list = next((v for v in json_data.values() if isinstance(v, list)), [])
            logging.info(f"Found {len(products_list)} products to transform")

            transformed_products = transformer.transform_products(products_list)
            logging.info(f"Successfully transformed {len(transformed_products)} products")

            # Log some statistics about transformed products
            total_variants = sum(len(product_group) - 1 for product_group in transformed_products)
            logging.info(f"Total number of variants: {total_variants}")
            logging.info(f"Average variants per product: {total_variants / len(transformed_products):.2f}")

        except Exception as e:
            logging.error(f"Error transforming products: {str(e)}", exc_info=True)
            return 1

        logging.debug("Desaka Unifier completed successfully")

    except Exception as e:
        logging.error(f"Error during initialization: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
