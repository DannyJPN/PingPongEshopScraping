import os
import sys
import argparse
import logging
import signal
from datetime import datetime
from tqdm import tqdm
from shared.logging_config import setup_logging
from shared.utils import get_log_filename
from unifierlib.validator import validate_language_support, validate_memory_files
from unifierlib.directory_manager import ensure_required_directories
from unifierlib.script_runner import ScriptRunner
from unifierlib.memory_manager import load_eshop_list, load_supported_languages
from unifierlib.result_loader import load_eshop_results
from unifierlib.repaired_product import RepairedProduct
from unifierlib.product_merger import ProductMerger

from unifierlib.constants import (
    DEFAULT_LANGUAGE,
    DEFAULT_RESULT_DIR,
    DEFAULT_MEMORY_DIR,
    DEFAULT_EXPORT_DIR,
    DEFAULT_CONFIRM_AI_RESULTS,
    DEFAULT_ENABLE_FINE_TUNING,
    DEFAULT_USE_FINE_TUNED_MODELS,
    LOG_DIR,
    WRONGS_FILE,
    ESHOP_LIST
)

# Global variable to hold script runner for signal handling
script_runner_instance = None


def signal_handler(signum, frame):
    """Handle Ctrl+C (SIGINT) signal to gracefully stop all running scripts."""
    global script_runner_instance

    logging.warning("Received interrupt signal (Ctrl+C). Stopping all running scripts...")

    if script_runner_instance:
        script_runner_instance.stop_all_scripts()
        logging.info("All scripts have been stopped.")

    logging.info("Exiting unifier...")
    sys.exit(0)


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
        dest="Language",
        type=validate_language,
        default=DEFAULT_LANGUAGE,
        help=f"ISO 639-1 language code (2 characters). Default: {DEFAULT_LANGUAGE}"
    )

    parser.add_argument(
        "--ResultDir",
        dest="ResultDir",
        type=str,
        default=DEFAULT_RESULT_DIR,
        help=f"Directory for results. Default: {DEFAULT_RESULT_DIR}"
    )

    # Update MemoryDir to be relative to script location
    default_memory_dir = os.path.join(script_dir, DEFAULT_MEMORY_DIR.lstrip("./"))
    parser.add_argument(
        "--MemoryDir",
        dest="MemoryDir",
        type=str,
        default=default_memory_dir,
        help=f"Directory for memory files. Default: {DEFAULT_MEMORY_DIR}"
    )

    parser.add_argument(
        "--ExportDir",
        dest="ExportDir",
        type=str,
        default=DEFAULT_EXPORT_DIR,
        help=f"Directory for exports. Default: {DEFAULT_EXPORT_DIR}"
    )

    parser.add_argument(
        "--ConfirmAIResults",
        dest="ConfirmAIResults",
        action="store_true",
        help="Automatically confirm AI results without user prompts (default: False)"
    )

    parser.add_argument(
        "--Debug",
        dest="Debug",
        action="store_true",
        help="Enable debug logging"
    )

    parser.add_argument(
        "--Overwrite",
        dest="Overwrite",
        action="store_true",
        help="Overwrite existing files"
    )

    parser.add_argument(
        "--SkipScripts",
        dest="SkipScripts",
        action="store_true",
        help="Skip running eshop scripts and only perform unification"
    )

    parser.add_argument(
        "--EnableFineTuning",
        dest="EnableFineTuning",
        action="store_true",
        default=DEFAULT_ENABLE_FINE_TUNING,
        help="Enable fine-tuning of OpenAI models (default: False)"
    )

    parser.add_argument(
        "--UseFineTunedModels",
        dest="UseFineTunedModels",
        action="store_true",
        default=DEFAULT_USE_FINE_TUNED_MODELS,
        help="Use fine-tuned models instead of generic ones when available (default: False)"
    )

    parser.add_argument(
        "--MaxParallel",
        dest="MaxParallel",
        type=int,
        default=3,
        help="Maximum number of eshop scripts to run in parallel (default: 3)"
    )

    parser.add_argument(
        "--SkipAI",
        dest="SkipAI",
        action="store_true",
        help="Skip using AI for property evaluation"
    )

    args = parser.parse_args()

    return args





def main():
    global script_runner_instance

    # Parse arguments first to get debug flag
    args = parse_arguments()

    # Generate the log filename
    log_file = get_log_filename(LOG_DIR)
    logging.debug(f"Generated log filename: {log_file}")

    # Setup logging with the log file path
    setup_logging(args.Debug, log_file)

    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Log script start time
    start_time = datetime.now()
    logging.info(f"Script started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    try:
        # Step 1: Ensure required directories exist
        directories_to_check = [
            LOG_DIR,
            args.ResultDir,
            args.MemoryDir,
            args.ExportDir
        ]
        if not ensure_required_directories(directories_to_check):
            logging.error("Failed to create required directories")
            sys.exit(1)

        # Step 2: Load supported languages once and validate language support
        config_dir = os.path.join(script_dir, "Config")
        supported_languages = load_supported_languages(config_dir)
        if not supported_languages:
            logging.error("Failed to load supported languages")
            sys.exit(1)

        if not validate_language_support(args.Language, script_dir, supported_languages):
            logging.error("Language validation failed")
            sys.exit(1)

        # Step 3: Validate Memory files (always runs)
        if not validate_memory_files(args.MemoryDir, args.Language):
            logging.error("Memory files validation failed")
            sys.exit(1)

        logging.info("Initialization completed successfully. Ready to proceed with unification process.")

        # Load the eshop list (must exist - created manually)
        logging.info("Loading eshop list...")
        eshop_list_path = os.path.join(args.MemoryDir, ESHOP_LIST)
        if not os.path.exists(eshop_list_path):
            logging.error(f"{ESHOP_LIST} not found. This file must be created manually.")
            logging.error(f"Please create {ESHOP_LIST} in the Memory directory with eshop configuration.")
            sys.exit(1)

        eshop_list = load_eshop_list(args.MemoryDir)

        if not eshop_list:
            logging.error(f"Failed to load eshop list or {ESHOP_LIST} is empty")
            sys.exit(1)

        logging.debug(f"Loaded {len(eshop_list)} eshops for processing")

        # Step 4: Run eshop scripts (conditional)
        if not args.SkipScripts:
            logging.info("Running eshop downloader scripts...")

            # Run the scripts in parallel
            script_runner_instance = ScriptRunner()
            try:
                success = script_runner_instance.run_scripts_parallel(
                    eshop_list, args.Language, args.ResultDir,
                    debug=args.Debug, overwrite=args.Overwrite, max_workers=args.MaxParallel
                )

                if success:
                    logging.info("All eshop scripts completed successfully")
                else:
                    logging.warning("Some eshop scripts failed")
            except KeyboardInterrupt:
                logging.warning("Script execution was interrupted by user")
                # The signal handler will take care of cleanup and exit
                return
        else:
            logging.info("Skipping eshop script execution (--SkipScripts flag set)")

        # Step 5: Load results from eshop scripts
        logging.info("Loading results from eshop downloader scripts...")
        results = load_eshop_results(args.ResultDir, eshop_list, args.Language)

        if results['summary']['total_products'] == 0:
            logging.error("No products were loaded from any eshop scripts")
            sys.exit(1)

        logging.debug(f"Successfully loaded {results['summary']['total_products']} products total")
        logging.debug(f"  - Export products (JSON): {results['summary']['total_export_products']}")
        logging.debug(f"  - Downloaded products (CSV): {results['summary']['total_downloaded_products']}")

        # Convert DownloadedProduct to RepairedProduct using parser method
        logging.info("Converting DownloadedProduct objects to RepairedProduct objects...")
        from unifierlib.parser import ProductParser
        from unifierlib.memory_manager import load_all_memory_files

        # Load memory files for parser (optimized loading)
        from unifierlib.memory_manager import load_frequently_used_memory_files
        frequent_memory_data = load_frequently_used_memory_files(args.MemoryDir, args.Language)
        memory_data = load_all_memory_files(args.MemoryDir, args.Language)

        # Load fine-tuned models if requested
        fine_tuned_models = {}
        if args.UseFineTunedModels:
            from unifierlib.fine_tuning import FineTuningManager
            fine_tuning_manager = FineTuningManager()
            fine_tuned_models = fine_tuning_manager.load_fine_tuned_models(script_dir)
            if fine_tuned_models:
                logging.debug(f"Loaded {len(fine_tuned_models)} fine-tuned models")
            else:
                logging.debug("No fine-tuned models found, using generic models")

        # Load supported languages data for parser
        config_dir = os.path.join(script_dir, "Config")
        from shared.file_ops import load_csv_file
        supported_languages_path = os.path.join(config_dir, "SupportedLanguages.csv")
        supported_languages_data = []
        if os.path.exists(supported_languages_path):
            supported_languages_data = load_csv_file(supported_languages_path)

        # Initialize parser with memory data and export products
        parser = ProductParser(
            memory_data=memory_data,
            language=args.Language,
            export_products=results.get('export_products', []),
            repaired_products=results.get('repaired_products', []),
            confirm_ai_results=args.ConfirmAIResults,
            use_fine_tuned_models=args.UseFineTunedModels,
            fine_tuned_models=fine_tuned_models,
            supported_languages_data=supported_languages_data,
            skip_ai=args.SkipAI
        )

        # Sort downloaded products by name before conversion
        logging.debug("Sorting downloaded products by name...")
        results['downloaded_products'].sort(key=lambda x: x.name.lower() if x.name else '')

        repaired_products = []
        with tqdm(total=len(results['downloaded_products']), desc="Converting to RepairedProducts", unit="product", miniters=1, mininterval=0.01) as pbar:
            for dp in results['downloaded_products']:
                try:
                    repaired = parser.downloaded_to_repaired_product(dp)
                    repaired_products.append(repaired)
                    logging.debug(f"Successfully converted product: {dp.name}")
                except Exception as e:
                    logging.error(f"Failed to convert product '{dp.name}': {str(e)}", exc_info=True)
                pbar.update(1)

        # Add repaired products to results
        results['repaired_products'] = repaired_products
        logging.debug(f"Successfully converted {len(repaired_products)} DownloadedProduct objects to RepairedProduct objects")

        # Step 5.5: Merge duplicate products
        logging.info("Merging duplicate products...")
        product_merger = ProductMerger()
        merged_products = product_merger.merge_products(repaired_products)

        logging.info(f"Product merging completed:")
        logging.info(f"  - Original products: {len(repaired_products)}")
        logging.info(f"  - Merged products: {len(merged_products)}")

        # Update results with merged products
        results['repaired_products'] = merged_products

        # Step 6: Filter products using ProductFilter
        logging.info("Filtering products...")
        from unifierlib.product_filter import ProductFilter

        product_filter = ProductFilter(memory_data)
        filtered_products, rejected_products = product_filter.process_products_with_filtering(merged_products)

        logging.debug(f"Product filtering completed:")
        logging.debug(f"  - Merged products: {len(merged_products)}")
        logging.debug(f"  - Filtered products: {len(filtered_products)}")
        logging.debug(f"  - Rejected products: {len(rejected_products)}")

        if rejected_products:
            logging.debug(f"Rejected products saved to {WRONGS_FILE}")

        # Step 7: Convert filtered RepairedProducts to ExportProducts
        logging.info("Converting filtered RepairedProducts to ExportProducts...")

        # Sort repaired products by name before conversion
        logging.debug("Sorting repaired products by name...")
        filtered_products.sort(key=lambda x: x.name.lower() if x.name else '')

        export_products = []
        for repaired_product in tqdm(filtered_products, desc="Converting to ExportProducts", unit="product"):
            try:
                export_product_array = parser.repaired_to_export_product(repaired_product)
                export_products.extend(export_product_array)
                logging.debug(f"Successfully converted product: {repaired_product.name}")
            except Exception as e:
                logging.error(f"Failed to convert product '{repaired_product.name}': {str(e)}", exc_info=True)
                # Continue with other products

        logging.debug(f"Successfully converted {len(filtered_products)} RepairedProducts to {len(export_products)} ExportProducts")

        # Add export products to results
        results['final_export_products'] = export_products

        # Step 8: Combine ExportProducts from JSON and RepairedProducts
        logging.info("Combining ExportProducts from JSON and RepairedProducts...")
        from unifierlib.product_combiner import ProductCombiner

        product_combiner = ProductCombiner(args.ExportDir)
        json_export_products = results.get('export_products', [])

        combined_products, combination_reports = product_combiner.combine_products(
            json_export_products, export_products
        )

        logging.info(f"Product combination completed:")
        logging.info(f"  - Combined products: {len(combined_products)}")
        logging.info(f"  - New products: {len(combination_reports['new_products'])}")
        logging.info(f"  - Old products: {len(combination_reports['old_products'])}")
        logging.info(f"  - Code changes: {len(combination_reports['code_changes'])}")
        logging.info(f"  - Price changes: {len(combination_reports['price_increases']) + len(combination_reports['price_decreases'])}")

        # Step 9: Export comprehensive reports
        logging.info("Generating comprehensive export reports...")
        from unifierlib.export_manager import ExportManager

        export_manager = ExportManager(args.ExportDir)
        created_files = export_manager.export_comprehensive_reports(
            combined_products, combination_reports['new_products']
        )

        logging.info(f"Comprehensive export completed. Created {len(created_files)} files.")

        # Step 10: Save simple unified products file (backward compatibility)
        logging.info("Saving unified products file for backward compatibility...")
        export_file_path = os.path.join(args.ExportDir, f"UnifiedProducts_{args.Language}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

        try:
            # Save combined products as CSV using file_ops
            from shared.file_ops import save_csv_file

            if combined_products:
                # Convert export products to list of dictionaries
                csv_data = []
                for product in tqdm(combined_products, desc="Preparing CSV data", unit="product"):
                    row = {}
                    # Get all field names from the export product
                    fieldnames = [attr for attr in dir(product) if not attr.startswith('_') and not callable(getattr(product, attr))]
                    for field in fieldnames:
                        value = getattr(product, field, '')
                        row[field] = value
                    csv_data.append(row)

                save_csv_file(csv_data, export_file_path)
                logging.info(f"Unified products saved to: {export_file_path}")
            else:
                logging.warning("No combined products to save")

        except Exception as e:
            logging.error(f"Failed to save unified products: {str(e)}", exc_info=True)

        # Step 11: Generate summary report
        logging.info("Generating summary report...")
        logging.info("=" * 60)
        logging.info("UNIFICATION SUMMARY")
        logging.info("=" * 60)
        logging.info(f"Language: {args.Language}")
        logging.info(f"Eshops processed: {len(eshop_list)}")
        logging.info(f"Total downloaded products: {results['summary']['total_downloaded_products']}")
        logging.info(f"Total export products (JSON): {results['summary']['total_export_products']}")
        logging.info(f"Converted to repaired products: {len(repaired_products)}")
        logging.info(f"Merged products: {len(merged_products)}")
        logging.info(f"Filtered products: {len(filtered_products)}")
        logging.info(f"Rejected products: {len(rejected_products)}")
        logging.info(f"Final export products: {len(export_products)}")
        logging.info(f"Combined products: {len(combined_products)}")
        logging.info(f"New products: {len(combination_reports['new_products'])}")
        logging.info(f"Old products: {len(combination_reports['old_products'])}")
        logging.info(f"Code changes: {len(combination_reports['code_changes'])}")
        logging.info(f"Price changes: {len(combination_reports['price_increases']) + len(combination_reports['price_decreases'])}")
        logging.info(f"Export files created: {len(created_files)}")
        if combined_products:
            logging.info(f"Unified products file: {export_file_path}")
        logging.info("=" * 60)

        # Step 12: Fine-tuning (if enabled)
        if args.EnableFineTuning:
            logging.info("Starting fine-tuning process...")
            try:
                from unifierlib.fine_tuning import FineTuningManager

                fine_tuning_manager = FineTuningManager(memory_data, args.Language)
                job_ids = fine_tuning_manager.fine_tune_all_tasks(min_examples=10)

                logging.info("Fine-tuning jobs started:")
                for task_type, job_id in job_ids.items():
                    if job_id:
                        logging.info(f"  - {task_type}: {job_id}")
                    else:
                        logging.warning(f"  - {task_type}: Failed to start")

                # Check status and save any completed models
                status_report = fine_tuning_manager.check_fine_tuning_status(job_ids, script_dir)
                logging.info("Fine-tuning status:")
                for task_type, status in status_report.items():
                    logging.info(f"  - {task_type}: {status}")

            except Exception as e:
                logging.error(f"Error during fine-tuning: {str(e)}", exc_info=True)
        else:
            logging.info("Fine-tuning skipped (--EnableFineTuning not set)")

    except Exception as e:
        logging.error(f"Fatal error during initialization: {str(e)}", exc_info=True)
        sys.exit(1)

    end_time = datetime.now()
    logging.info(f"Script ended at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"Total execution time: {end_time - start_time}")


if __name__ == "__main__":
    main()
