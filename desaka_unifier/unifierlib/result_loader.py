"""
Result loader module for desaka_unifier project.
Contains logic for loading results from eshop downloader scripts.
Updated to handle files in dated subdirectories (Full_DD.MM.YYYY format).
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from shared.file_ops import load_csv_file
from unifierlib.export_product import ExportProduct
from unifierlib.downloaded_product import DownloadedProduct
from unifierlib.file_finder import find_output_files


def load_eshop_results(result_dir: str, eshop_list: List[Dict[str, Any]], language: str) -> Dict[str, Any]:
    """
    Load results from all eshop downloader scripts.
    Updated to handle files in dated subdirectories.

    Args:
        result_dir (str): Path to the results directory
        eshop_list (List[Dict[str, Any]]): List of eshops that were processed
        language (str): Language code for language-dependent results

    Returns:
        Dict[str, Any]: Dictionary containing loaded results
    """
    logging.info("Loading eshop downloader results...")

    results = {
        'export_products': [],  # Products from JSON (pincesobchod)
        'downloaded_products': [],  # Products from CSV (other eshops)
        'failed_eshops': [],
        'summary': {}
    }

    for eshop in eshop_list:
        eshop_name = eshop.get('Name', '')

        try:
            if eshop_name.lower() in ['pincesobchod', 'pincesobchod_cs', 'pincesobchod_sk'] or 'pincesobchod' in eshop_name.lower():
                # Load JSON results for pincesobchod (language-dependent)
                products = load_pincesobchod_results(result_dir, eshop_name, language)
                if products:
                    results['export_products'].extend(products)
                    logging.debug(f"Loaded {len(products)} products from {eshop_name} (JSON)")
                else:
                    results['failed_eshops'].append(eshop_name)
                    logging.warning(f"No products loaded from {eshop_name}")
            else:
                # Load CSV results for other eshops
                products = load_csv_results(result_dir, eshop_name)
                if products:
                    results['downloaded_products'].extend(products)
                    logging.debug(f"Loaded {len(products)} products from {eshop_name} (CSV)")
                else:
                    results['failed_eshops'].append(eshop_name)
                    logging.warning(f"No products loaded from {eshop_name}")

        except Exception as e:
            logging.error(f"Error loading results from {eshop_name}: {str(e)}", exc_info=True)
            results['failed_eshops'].append(eshop_name)

    # Generate summary
    results['summary'] = {
        'total_export_products': len(results['export_products']),
        'total_downloaded_products': len(results['downloaded_products']),
        'total_products': len(results['export_products']) + len(results['downloaded_products']),
        'successful_eshops': len(eshop_list) - len(results['failed_eshops']),
        'failed_eshops': len(results['failed_eshops']),
        'total_eshops': len(eshop_list)
    }

    logging.info(f"Results loading summary:")
    logging.info(f"  - Total products: {results['summary']['total_products']}")
    logging.info(f"  - Export products (JSON): {results['summary']['total_export_products']}")
    logging.info(f"  - Downloaded products (CSV): {results['summary']['total_downloaded_products']}")
    logging.info(f"  - Successful eshops: {results['summary']['successful_eshops']}/{results['summary']['total_eshops']}")

    if results['failed_eshops']:
        logging.warning(f"Failed to load results from: {', '.join(results['failed_eshops'])}")

    return results


def load_pincesobchod_results(result_dir: str, eshop_name: str, language: str) -> List[ExportProduct]:
    """
    Load JSON results from pincesobchod using the file finder.

    Args:
        result_dir (str): Path to the results directory
        eshop_name (str): Eshop name
        language (str): Language code

    Returns:
        List[ExportProduct]: List of products from JSON
    """
    # Look for eshop results directory
    eshop_dir = os.path.join(result_dir, f"{eshop_name.lower()}_{language.lower()}")
    if not os.path.exists(eshop_dir):
        # Try original case
        eshop_dir = os.path.join(result_dir, eshop_name)
        if not os.path.exists(eshop_dir):
            logging.error(f"Eshop results directory not found for {eshop_name} in {result_dir}")
            return []

    # Use file finder to locate JSON file
    csv_path, json_path = find_output_files(eshop_dir, eshop_name, language)

    if not json_path:
        logging.error(f"No JSON file found for {eshop_name} in {eshop_dir}")
        return []

    try:
        logging.debug(f"Loading JSON file: {json_path}")

        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        products = []

        # Handle different JSON structures
        if isinstance(json_data, list):
            # Direct list of products
            product_list = json_data
        elif isinstance(json_data, dict):
            # Check for common container keys
            if 'products' in json_data:
                product_list = json_data['products']
            elif 'items' in json_data:
                product_list = json_data['items']
            elif 'data' in json_data:
                product_list = json_data['data']
            else:
                # Assume the dict itself is a single product
                product_list = [json_data]
        else:
            logging.error(f"Unexpected JSON structure in {json_path}")
            return []

        # Convert to ExportProduct objects using parser
        from unifierlib.parser import ProductParser
        parser = ProductParser()

        for item in product_list:
            if isinstance(item, dict):
                # Use parser to create array of ExportProducts (main + variants)
                export_products = parser.json_to_export_products(item)
                products.extend(export_products)
            else:
                logging.warning(f"Skipping non-dict item in JSON: {type(item)}")

        logging.info(f"Successfully loaded {len(products)} products from {eshop_name} JSON")
        return products

    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error in {json_path}: {str(e)}")
        return []
    except Exception as e:
        logging.error(f"Error loading JSON {json_path}: {str(e)}", exc_info=True)
        return []


def load_csv_results(result_dir: str, eshop_name: str) -> List[DownloadedProduct]:
    """
    Load CSV results from an eshop using the file finder.

    Args:
        result_dir (str): Path to the results directory
        eshop_name (str): Name of the eshop

    Returns:
        List[DownloadedProduct]: List of products from CSV
    """
    # Look for eshop results directory
    eshop_dir = os.path.join(result_dir, eshop_name.lower())
    if not os.path.exists(eshop_dir):
        # Try original case
        eshop_dir = os.path.join(result_dir, eshop_name)
        if not os.path.exists(eshop_dir):
            logging.error(f"Eshop results directory not found for {eshop_name} in {result_dir}")
            return []

    # Use file finder to locate CSV file
    csv_path, json_path = find_output_files(eshop_dir, eshop_name)

    if not csv_path:
        logging.error(f"No CSV file found for {eshop_name} in {eshop_dir}")
        return []

    try:
        logging.debug(f"Loading CSV file: {csv_path}")

        csv_data = load_csv_file(csv_path)

        # Use parser to convert CSV data to DownloadedProduct objects
        from unifierlib.parser import ProductParser
        parser = ProductParser()
        products = parser.csv_to_downloaded_products(csv_data)

        logging.info(f"Successfully loaded {len(products)} products from {eshop_name} CSV")
        return products

    except Exception as e:
        logging.error(f"Error loading CSV file {csv_path}: {str(e)}", exc_info=True)
        return []



