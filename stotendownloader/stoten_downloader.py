import os
import logging
import csv
from argparse import ArgumentParser
from datetime import datetime
from shared.directory_manager import ensure_directories
from shared.main_page_downloader import download_main_page
from shared.html_loader import load_html_as_dom_tree
from stotenlib.category_link_extractor import extract_category_links
from shared.category_firstpage_downloader import download_category_firstpages
from shared.category_pages_downloader import download_category_pages
from stotenlib.product_detail_link_extractor import extract_all_product_detail_links
from shared.product_detail_page_downloader import download_product_detail_pages
from stotenlib.product_attribute_extractor import extract_products
from stotenlib.category_pages_link_extractor import extract_all_category_pages_links
from shared.product_image_downloader import download_product_main_image
from shared.product_image_downloader import download_product_gallery_images
from stotenlib.constants import DEFAULT_RESULT_FOLDER  
from shared.logging_config import setup_logging
from shared.utils import get_csv_outfile
from shared.product_to_eshop_csv_saver import export_to_csv
from tqdm import tqdm
# Constants


def parse_arguments():
    parser = ArgumentParser(description="StotenDownloader")
    parser.add_argument("--result_folder", type=str, default=DEFAULT_RESULT_FOLDER, help="Root folder for the script's output")
    parser.add_argument("--overwrite", action="store_true", help="Whether to overwrite existing downloaded resources")
    parser.add_argument("--debug", action="store_true", help="Enable console logging for non-errors")
    return parser.parse_args()

def main():
    args = parse_arguments()
    setup_logging(args.debug)

    root_folder = args.result_folder
    overwrite = args.overwrite
    debug = args.debug

    # Ensure directories
    ensure_directories(root_folder)

    # Step 1: Download main webpage
    main_page_path = download_main_page(root_folder, overwrite)
    if not main_page_path:
        logging.error("Failed to download main page.")
        return

    # Step 2: Scrape main webpage for category first pages
    main_page_dom = load_html_as_dom_tree(main_page_path)
    category_links = extract_category_links(main_page_dom)

    # Step 3: Download all the category first pages
    category_firstpage_paths = download_category_firstpages(category_links, root_folder, overwrite)
    
    # Step 4: Make a list of all the category pages and download them
    category_page_links = extract_all_category_pages_links(category_firstpage_paths)

    
    # Step 5: Download all category pages with "strana" URLs
    category_pages_downloaded_paths = download_category_pages(category_page_links, root_folder, overwrite)
    
    # Step 6: Scrape all of the category pages for their next pages (those with strana-NUMBER)
    product_detail_links=extract_all_product_detail_links(category_pages_downloaded_paths)

    
    # Step 7: Download all the product detail pages
    product_detail_page_paths = download_product_detail_pages(product_detail_links, root_folder, overwrite)
    
    # Step 8: Make a list of product class instances using the extraction methods
    products = extract_products(product_detail_page_paths)


    # Step 9: Iterate through all the products and create folders for images
    
    download_product_main_image(products,root_folder, overwrite)
    download_product_gallery_images(products,root_folder, overwrite)
    
    # Step 10: Generate the final CSV output
    csv_output_path = get_csv_outfile(root_folder)
    export_to_csv(csv_output_path,products)
    
if __name__ == "__main__":
    main()