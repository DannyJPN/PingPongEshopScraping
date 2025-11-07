"""
Yasaka E-shop Downloader

Downloads product data from Yasaka e-shop and exports to CSV.

Usage:
    python yasaka_downloader.py --result_folder H:/Desaka/Yasaka --debug --overwrite
"""

import os
import logging
from argparse import ArgumentParser

# Shared imports
from shared.directory_manager import ensure_directories
from shared.main_page_downloader import download_main_page
from shared.html_loader import load_html_as_dom_tree
from shared.category_firstpage_downloader import download_category_firstpages
from shared.category_pages_downloader import download_category_pages
from shared.product_detail_page_downloader import download_product_detail_pages
from shared.product_image_downloader import download_product_main_image, download_product_gallery_images
from shared.product_to_eshop_csv_saver import export_to_csv
from shared.logging_config import setup_logging
from shared.utils import get_full_day_folder, get_log_filename

# Site-specific imports
from yasakalib.constants import DEFAULT_RESULT_FOLDER, MAIN_URL, MAIN_PAGE_FILENAME, CSV_OUTPUT_NAME, LOG_DIR
from yasakalib.category_link_extractor import extract_category_links
from yasakalib.category_pages_link_extractor import extract_all_category_pages_links
from yasakalib.product_detail_link_extractor import extract_all_product_detail_links
from yasakalib.product_attribute_extractor import extract_products


def parse_arguments():
    """Parse command line arguments."""
    parser = ArgumentParser(description="Yasaka E-shop Downloader")

    parser.add_argument(
        "--result_folder",
        type=str,
        default=DEFAULT_RESULT_FOLDER,
        help="Root folder for the script's output"
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Whether to overwrite existing downloaded resources"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable console logging for non-errors"
    )

    return parser.parse_args()


def main():
    """
    Main execution function - MANDATORY 10-STEP PROCESS.

    DO NOT modify the order or structure of these steps!
    """
    # Parse arguments
    args = parse_arguments()

    # Setup logging
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    LOG_FILE = get_log_filename(LOG_DIR)
    setup_logging(args.debug, LOG_FILE)

    logging.info("=" * 80)
    logging.info("Yasaka Downloader Started")
    logging.info("=" * 80)

    root_folder = args.result_folder
    overwrite = args.overwrite

    # Ensure directory structure exists
    ensure_directories(root_folder)

    # ========== STEP 1: Download main webpage ==========
    logging.info("STEP 1: Downloading main page")
    main_page_path = download_main_page(root_folder, MAIN_URL, MAIN_PAGE_FILENAME, overwrite)

    if not main_page_path:
        logging.error("Failed to download main page. Exiting.")
        return

    # ========== STEP 2: Extract category links from main page ==========
    logging.info("STEP 2: Extracting category links from main page")
    main_page_dom = load_html_as_dom_tree(main_page_path)
    category_links = extract_category_links(main_page_dom)

    if not category_links:
        logging.error("No category links found. Exiting.")
        return

    # ========== STEP 3: Download category first pages ==========
    logging.info("STEP 3: Downloading category first pages")
    category_firstpage_paths = download_category_firstpages(category_links, root_folder, overwrite)

    # ========== STEP 4: Extract all category page links (with pagination) ==========
    logging.info("STEP 4: Extracting category page links (pagination)")
    category_page_links = extract_all_category_pages_links(category_firstpage_paths)

    # ========== STEP 5: Download all category pages ==========
    logging.info("STEP 5: Downloading all category pages")
    category_pages_downloaded_paths = download_category_pages(category_page_links, root_folder, overwrite)

    # ========== STEP 6: Extract product detail links ==========
    logging.info("STEP 6: Extracting product detail links")
    product_detail_links = extract_all_product_detail_links(category_pages_downloaded_paths)

    if not product_detail_links:
        logging.error("No product links found. Exiting.")
        return

    # ========== STEP 7: Download product detail pages ==========
    logging.info("STEP 7: Downloading product detail pages")
    product_detail_page_paths = download_product_detail_pages(product_detail_links, root_folder, overwrite)

    # For most e-shops (without separate variant URLs):
    product_detail_all_page_paths = product_detail_page_paths

    # ========== STEP 8: Extract product attributes ==========
    logging.info("STEP 8: Extracting product attributes")
    products = extract_products(product_detail_all_page_paths)

    if not products:
        logging.warning("No products extracted. Check extraction logic.")

    # ========== STEP 9: Download product images ==========
    logging.info("STEP 9: Downloading product images")
    download_product_main_image(products, root_folder, overwrite)
    download_product_gallery_images(products, root_folder, overwrite)

    # ========== STEP 10: Export to CSV ==========
    logging.info("STEP 10: Exporting to CSV")
    csv_output_path = f"{get_full_day_folder(root_folder)}/{CSV_OUTPUT_NAME}"
    export_to_csv(csv_output_path, products)

    logging.info("=" * 80)
    logging.info(f"Download complete! Results saved to: {csv_output_path}")
    logging.info("=" * 80)


if __name__ == "__main__":
    main()
