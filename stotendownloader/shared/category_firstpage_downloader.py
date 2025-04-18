import os
import logging
from tqdm import tqdm
from urllib.parse import urlparse
from shared.webpage_downloader import download_webpage
from shared.utils import sanitize_filename, get_pages_folder

def download_category_firstpages(category_urls, root_folder, overwrite=False, debug=False):
    """
    Downloads the first pages of categories and displays a progress bar.

    :param category_urls: Set of absolute URLs of categories.
    :param root_folder: Root folder for saving the downloaded pages.
    :param overwrite: Boolean indicating whether to overwrite existing files.
    :param debug: Boolean indicating whether to enable debug logging.
    :return: List of paths to the downloaded files, relative to the root folder.
    """
    downloaded_files = []
    pages_folder = get_pages_folder(root_folder)

    # Progress bar setup
    with tqdm(total=len(category_urls), desc="Downloading category first pages") as pbar:
        for url in category_urls:
            try:
                # Parse URL to create a valid filename
                parsed_url = urlparse(url)
                filename = (parsed_url.path + parsed_url.query).strip("/").replace('/', '_') + '.html'
                logging.debug(f"Original filename: {filename}")
                sanitized_filename = sanitize_filename(filename)
                logging.debug(f"Sanitized filename: {sanitized_filename}")
                file_path = os.path.join(pages_folder, sanitized_filename)

                # Download the webpage
                download_successful = download_webpage(url, file_path, overwrite=overwrite, debug=debug)
                if download_successful:
                    # Add the absolute path to the list of downloaded files only if download is successful
                    downloaded_files.append(os.path.abspath(file_path))

                # Update progress bar
                pbar.update(1)

            except Exception as e:
                logging.error(f"Error downloading category first page {url}: {e}", exc_info=True)
                continue

    # Ensure the returned list is sorted and unique
    unique_sorted_files = sorted(set(downloaded_files))
    logging.debug(f"Unique sorted downloaded category first pages: {len(unique_sorted_files)}")
    return unique_sorted_files










