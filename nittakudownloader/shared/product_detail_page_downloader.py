import os
import logging
from tqdm import tqdm
from urllib.parse import urlparse
from datetime import datetime
from shared.webpage_downloader import download_webpage
from shared.utils import get_products_folder

def download_product_detail_pages(product_detail_urls, root_folder, overwrite=False, debug=False):
    """
    Downloads all product detail pages and displays a progress bar.

    :param product_detail_urls: Set of absolute URLs of product detail pages.
    :param root_folder: Root folder for saving the downloaded pages.
    :param overwrite: Boolean indicating whether to overwrite existing files.
    :param debug: Boolean indicating whether to enable debug logging.
    :return: List of paths to the downloaded files, relative to the root folder.
    """
    downloaded_files = []
    products_folder = get_products_folder(root_folder)

    # Progress bar setup
    with tqdm(total=len(product_detail_urls), desc="Downloading product detail pages") as pbar:
        for url in product_detail_urls:
            try:
                logging.debug(f"Processing URL: {url}")

                # Parse URL to create a valid filename
                parsed_url = urlparse(url)
                filename = (parsed_url.path+parsed_url.query).strip("/").replace('/', '_') + '.html'
                file_path = os.path.join(products_folder, filename)

                logging.debug(f"Downloading webpage from URL: {url} to filepath: {file_path}")

                # Download the webpage
                download_webpage(url, file_path, overwrite=overwrite)

                # Add the absolute path to the list of downloaded files if download was successful
                if os.path.exists(file_path):
                    downloaded_files.append(os.path.abspath(file_path))

                # Update progress bar
                pbar.update(1)

            except Exception as e:
                logging.error(f"Error downloading product detail page {url}: {e}", exc_info=True)
                continue

    # Ensure the returned list is sorted and unique
    unique_sorted_files = sorted(set(downloaded_files))
    logging.debug(f"Unique sorted downloaded product detail pages: {len(unique_sorted_files)}")
    return unique_sorted_files










