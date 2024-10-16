# category_pages_downloader.py
import os
import logging
from tqdm import tqdm
from urllib.parse import urlparse
from datetime import datetime
from shared.webpage_downloader import download_webpage
from shared.html_loader import load_html_as_dom_tree
from sportspinlib.category_pages_link_extractor import extract_category_pages_links
from shared.utils import sanitize_filename, get_pages_folder

def download_category_pages(category_page_links, root_folder, overwrite=False, debug=False):
    """
    Downloads all category pages and displays a progress bar.

    :param category_first_page_paths: List of file paths to category first pages.
    :param root_folder: Root folder for saving the downloaded pages.
    :param overwrite: Boolean indicating whether to overwrite existing files.
    :param debug: Boolean indicating whether to enable debug logging.
    :return: List of paths to the downloaded files, relative to the root folder.
    """
    downloaded_files = []
    pages_folder = get_pages_folder(root_folder)


    # Progress bar setup
    with tqdm(total=len(category_page_links), desc="Downloading all category pages") as pbar:
        for url in category_page_links:
            try:
                # Parse URL to create a valid filename
                parsed_url = urlparse(url)
                filename = (parsed_url.path+parsed_url.query).strip("/").replace('/', '_') + '.html'
                logging.debug(f"Original filename: {filename}")
                sanitized_filename = sanitize_filename(filename)
                logging.debug(f"Sanitized filename: {sanitized_filename}")
                file_path = os.path.join(pages_folder, sanitized_filename)
                
                logging.debug(f"Downloading webpage from URL: {url} to filepath: {file_path}")
                # Download the webpage
                download_webpage(url, file_path, overwrite=overwrite)

                # Add the absolute path to the list of downloaded files
                downloaded_files.append(os.path.abspath(file_path))

                # Update progress bar
                pbar.update(1)

            except Exception as e:
                logging.error(f"Error downloading category page {url}: {e}", exc_info=True)
                continue

    # Ensure the returned list is sorted and unique
    unique_sorted_files = sorted(set(downloaded_files))
    logging.debug(f"Unique sorted downloaded category pages: {len(unique_sorted_files)}")
    return unique_sorted_files