import os
import logging
from shared.utils import sanitize_filename
from shared.http_downloader import download_with_retry

def download_webpage(url, filepath, overwrite=False, debug=False, stats=None):
    try:
        logging.debug(f"Starting download_webpage function for URL: {url}")

        # Extract the directory and filename from the filepath
        directory, filename = os.path.split(filepath)

        # Sanitize the filename
        sanitized_filename = sanitize_filename(filename)
        logging.debug(f"Original filename: {filename}, Sanitized filename: {sanitized_filename}")

        # Reconstruct the sanitized filepath
        sanitized_filepath = os.path.join(directory, sanitized_filename)
        logging.debug(f"Sanitized filepath: {sanitized_filepath}")

        # Check if file already exists
        if not overwrite and os.path.exists(sanitized_filepath):
            logging.debug(f"File already exists and overwrite is not set: {sanitized_filepath}")
            return True

        # Download the webpage with retry logic
        logging.debug(f"Making HTTP request to URL: {url}")
        response = download_with_retry(url, stats=stats)

        if response is None:
            logging.debug(f"Failed to download URL: {url}")
            return False

        logging.debug(f"Successfully downloaded webpage from URL: {url} to filepath: {sanitized_filepath}")

        # Write the content to a file
        with open(sanitized_filepath, 'w', encoding='utf-8') as file:
            file.write(response.text)

        return True

    except Exception as e:
        logging.error(f"Error downloading {url} to {sanitized_filepath}: {e}", exc_info=True)
        return False










