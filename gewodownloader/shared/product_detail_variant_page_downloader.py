import os
import logging
from tqdm import tqdm
from urllib.parse import urlparse
from shared.utils import get_products_folder
from shared.webpage_downloader import download_webpage

def download_product_detail_variant_pages(product_variant_detail_urls, root_folder, overwrite=False, debug=False):
    """
    Downloads all product detail variant pages from the given URLs and saves them to the specified root folder.

    :param product_variant_detail_urls: Set of product variant detail URLs.
    :param root_folder: Path to the root folder where the pages will be saved.
    :param overwrite: Whether to overwrite existing files.
    :param debug: Whether to enable debug logging.
    :return: List of paths to the downloaded files.
    """
    downloaded_files = []
    products_folder = get_products_folder(root_folder)

    # Progress bar setup
    with tqdm(total=len(product_variant_detail_urls), desc="Downloading product variant detail pages") as pbar:
        for url in product_variant_detail_urls:
            try:
                logging.debug(f"Processing URL: {url}")

                # Parse URL to create a valid filename
                parsed_url = urlparse(url)
                filename = (parsed_url.path+parsed_url.query).strip("/").replace('/', '_') + '.html'
                filepath = os.path.join(products_folder, filename)

                logging.debug(f"Downloading webpage from URL: {url} to filepath: {filepath}")

                # Download the webpage
                if download_webpage(url, filepath, overwrite=overwrite):
                    # Add the absolute path to the list of downloaded files
                    downloaded_files.append(os.path.abspath(filepath))

                # Update progress bar
                pbar.update(1)

            except Exception as e:
                logging.error(f"Error downloading product variant detail page {url}: {e}", exc_info=True)
                continue

    unique_sorted_files = sorted(set(downloaded_files))
    logging.debug(f"Unique sorted downloaded product detail variant pages: {len(unique_sorted_files)}")
    return unique_sorted_files
