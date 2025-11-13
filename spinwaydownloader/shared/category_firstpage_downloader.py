import os
import logging
from tqdm import tqdm
from urllib.parse import urlparse
from datetime import datetime
from shared.webpage_downloader import download_webpage
from shared.utils import sanitize_filename, get_pages_folder
from shared.download_constants import BASE_RETRY_DELAY

def download_category_firstpages(category_urls, root_folder, overwrite=False, debug=False, stats=None):
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
                filename = (parsed_url.path+parsed_url.query).strip("/").replace('/', '_') + '.html'
                logging.debug(f"Original filename: {filename}")
                sanitized_filename = sanitize_filename(filename)
                logging.debug(f"Sanitized filename: {sanitized_filename}")
                file_path = os.path.join(pages_folder, sanitized_filename)

                # Download the webpage
                if download_webpage(url, file_path, overwrite=overwrite, stats=stats):
                    # Add the absolute path to the list of downloaded files
                    downloaded_files.append(os.path.abspath(file_path))

                # Update progress bar with statistics
                if stats:
                    total_req, failed_req = stats.get_stats(url)
                    if total_req > 0:
                        success_rate = ((total_req - failed_req) / total_req) * 100
                        failure_rate = stats.get_failure_rate(url)
                        current_delay = BASE_RETRY_DELAY * (1 + failure_rate)
                        pbar.set_postfix({
                            'OK': f'{success_rate:.1f}%',
                            'delay': f'{current_delay:.3f}s'
                        })
                pbar.update(1)

            except Exception as e:
                logging.error(f"Error downloading category first page {url}: {e}", exc_info=True)
                continue

    # Ensure the returned list is sorted and unique
    unique_sorted_files = sorted(set(downloaded_files))
    logging.debug(f"Unique sorted downloaded category first pages: {len(unique_sorted_files)}")
    return unique_sorted_files










