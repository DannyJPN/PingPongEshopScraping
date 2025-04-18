import logging
import os
import sys
import signal
import threading
from datetime import datetime
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from shared.file_loader import load_csv_file, load_json_file
from typing import Optional, List, Dict, Any
from unifierlib.product_mapper import json_to_unified, csv_to_downloaded
from unifierlib.unified_export_product import UnifiedExportProduct, UnifiedExportProductMain, UnifiedExportProductVariant
from unifierlib.downloaded_product import DownloadedProduct

# Global flag for thread control
shutdown_flag = threading.Event()

def handle_interrupt(signum, frame):
    logging.info("Interrupt received, shutting down threads...")
    shutdown_flag.set()
    sys.exit(1)

signal.signal(signal.SIGINT, handle_interrupt)

def find_newest_csv_file(base_dir: str, eshop_name: str) -> Optional[str]:
    eshop_dir = os.path.join(base_dir, eshop_name)
    try:
        logging.info(f"Searching for newest CSV file in {eshop_dir} for eshop {eshop_name}")

        if not os.path.exists(eshop_dir):
            logging.error(f"Base directory does not exist: {eshop_dir}")
            return None

        # Find all Full_{date} folders
        full_folders = [d for d in os.listdir(eshop_dir) if d.startswith('Full_')]
        if not full_folders:
            logging.warning(f"No Full_ folders found in {eshop_dir}")
            return None

        try:
            # Sort folders by date in name (Full_DD.MM.YYYY)
            full_folders.sort(key=lambda x: datetime.strptime(x.split('_')[1], '%d.%m.%Y'), reverse=True)
        except (IndexError, ValueError) as e:
            logging.error(f"Error parsing date from folder names: {str(e)}", exc_info=True)
            return None

        newest_folder = full_folders[0]
        folder_path = os.path.join(eshop_dir, newest_folder)
        logging.debug(f"Found newest folder: {folder_path}")

        # Find CSV files matching pattern
        csv_pattern = f"{eshop_name}Output.csv"
        matching_files = [f for f in os.listdir(folder_path) if f.endswith(csv_pattern)]

        if not matching_files:
            logging.warning(f"No matching CSV files found in {folder_path}")
            return None

        # Get newest by modification time
        newest_file = max(matching_files, key=lambda f: os.path.getmtime(os.path.join(folder_path, f)))
        file_path = os.path.join(folder_path, newest_file)

        logging.info(f"Found newest CSV file: {file_path}")
        return file_path

    except Exception as e:
        logging.error(f"Error finding newest CSV file: {str(e)}", exc_info=True)
        return None

def load_eshop_csv_files(csv_paths: List[str]):
    """Load all eShop CSV files and convert to DownloadedProduct instances."""
    products = []

    for csv_path in tqdm(csv_paths, desc="Loading eShop CSV files"):
        if shutdown_flag.is_set():
            logging.info("Shutdown requested, stopping CSV file loading")
            break
            
        logging.info(f"Loading products from {csv_path}({type(csv_path)})")
        csv_data = load_csv_file(csv_path)
        products.extend(csv_data)
        logging.info(f"Loaded {len(csv_data)} products from {csv_path}")

    return products

def find_newest_eshop_csv_files(result_dir: str, eshop_names: List[str]):
    csv_paths = []

    for eshop_name in tqdm(eshop_names, desc="Finding eShop CSV files"):
        if shutdown_flag.is_set():
            logging.info("Shutdown requested, stopping CSV file search")
            break
            
        try:
            csv_path = find_newest_csv_file(result_dir, eshop_name)
            if csv_path:
                csv_paths.append(csv_path)
            else:
                logging.warning(f"No CSV file found for eShop: {eshop_name}")
        except Exception as e:
            logging.error(f"Error processing eShop {eshop_name}: {e}", exc_info=True)
            continue

    return csv_paths

def process_json_item(item):
    try:
        if shutdown_flag.is_set():
            return None
            
        transformed_items = json_to_unified(item)

        unified_products = []
        for mapping in transformed_items:
            if mapping['typ'] == 'produkt':
                product = UnifiedExportProductMain()
            else:
                product = UnifiedExportProductVariant()
            product.fill(mapping)
            unified_products.append(product)

        return unified_products
    except Exception as e:
        logging.error(f"Error processing JSON item {item}: {str(e)}", exc_info=True)
        return None

def process_csv_item(item):
    """Process a single CSV item and return transformed products."""
    try:
        if shutdown_flag.is_set():
            return None
            
        transformed_items = csv_to_downloaded(item)
        logging.debug(f"Processing CSV item with name: {item.get('name', 'unknown')} : {len(transformed_items)}")
        downloaded_products = []
        for mapping in transformed_items:
            product = DownloadedProduct()
            product.fill(mapping)
            downloaded_products.append(product)

        logging.debug(f"Successfully transformed item name: {item.get('name', 'unknown')} into {len(downloaded_products)} products")
        return downloaded_products
    except Exception as e:
        logging.error(f"Error processing CSV item {item}: {str(e)}", exc_info=True)
        return None

def transform_json_data(json_data, max_threads=32):
    """Transform JSON data into UnifiedExportProduct objects using parallel processing."""
    if not json_data:
        logging.warning("No JSON data to transform")
        return []

    try:
        unified_products = []
        max_workers = min(max_threads, len(json_data))
        logging.info(f"Starting parallel processing with {max_workers} threads for {len(json_data)}")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_item = {
                executor.submit(process_json_item, item): item
                for item in json_data
            }

            with tqdm(total=len(future_to_item), desc="Processing products") as pbar:
                for future in as_completed(future_to_item):
                    if shutdown_flag.is_set():
                        logging.info("Shutdown requested, stopping JSON transformation")
                        executor.shutdown(wait=False)
                        break
                    try:
                        result = future.result()
                        if result:
                            unified_products.extend(result)
                    except Exception as e:
                        logging.error(f"Thread execution failed: {str(e)}", exc_info=True)
                    finally:
                        pbar.update(1)

        logging.info(f"Transformed JSON data into {len(unified_products)} UnifiedExportProduct objects")
        return unified_products

    except Exception as e:
        logging.error(f"Error during JSON data transformation: {e}", exc_info=True)
        return []

def find_newest_json_file(base_dir: str, language_code: str) -> Optional[str]:
    """Find the newest JSON file in PincesObchod_{language}/Full_{date} structure."""
    try:
        pinces_dir = os.path.join(base_dir, f"PincesObchod_{language_code}")
        if not os.path.exists(pinces_dir):
            logging.warning(f"Directory not found: {pinces_dir}")
            return None

        # Find all Full_{date} folders
        full_folders = [d for d in os.listdir(pinces_dir) if d.startswith('Full_')]
        if not full_folders:
            logging.warning(f"No Full_ folders found in {pinces_dir}")
            return None

        # Sort folders by date
        full_folders.sort(key=lambda x: datetime.strptime(x.split('_')[1], '%d.%m.%Y'), reverse=True)
        newest_folder = full_folders[0]
        folder_path = os.path.join(pinces_dir, newest_folder)

        # Find JSON files
        json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
        if not json_files:
            logging.warning(f"No JSON files found in {folder_path}")
            return None

        # Get newest by modification time
        newest_file = max(json_files, key=lambda f: os.path.getmtime(os.path.join(folder_path, f)))
        newest_path = os.path.join(folder_path, newest_file)
        logging.info(f"Found newest JSON file: {newest_path}")
        return newest_path

    except Exception as e:
        logging.error(f"Error finding newest JSON file: {str(e)}", exc_info=True)
        return None

def transform_csv_data(csv_data, max_threads=32):
    """Transform CSV data into DownloadedProduct objects using parallel processing."""
    if not csv_data:
        logging.warning("No CSV data to transform")
        return []

    try:
        downloaded_products = []
        max_workers = min(max_threads, len(csv_data))
        logging.info(f"Starting parallel processing with {max_workers} threads for {len(csv_data)}")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_item = {
                executor.submit(process_csv_item, item): item
                for item in csv_data
            }

            with tqdm(total=len(future_to_item), desc="Processing products") as pbar:
                for future in as_completed(future_to_item):
                    if shutdown_flag.is_set():
                        logging.info("Shutdown requested, stopping CSV transformation")
                        executor.shutdown(wait=False)
                        break
                    try:
                        result = future.result()
                        if result:
                            downloaded_products.extend(result)
                    except Exception as e:
                        logging.error(f"Thread execution failed: {str(e)}", exc_info=True)
                    finally:
                        pbar.update(1)

        logging.info(f"Transformed CSV data into {len(downloaded_products)} DownloadedProduct objects")
        return downloaded_products

    except Exception as e:
        logging.error(f"Error during CSV data transformation: {e}", exc_info=True)
        return []

