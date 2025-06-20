import os
import logging
import requests
from shared.utils import sanitize_filename

def download_webpage(url, filepath, overwrite=False, debug=False):
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

        # Download the webpage
        logging.debug(f"Making HTTP request to URL: {url}")
        response = requests.get(url)

        if response.status_code == 404:
            logging.debug(f"404 Not Found for URL: {url}")
            return False
        
        # Comment out raise_for_status to avoid exceptions for non-404 errors
        # response.raise_for_status()  # Raise an HTTPError for other bad responses

        logging.debug(f"Downloading webpage from URL: {url} to filepath: {sanitized_filepath}")

        # Write the content to a file in binary mode to preserve encoding
        with open(sanitized_filepath, 'wb') as file:
            file.write(response.content)

        return True

    except Exception as e:
        logging.error(f"Error downloading {url} to {filepath}: {e}", exc_info=True)
        return False
