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
            return

        # Download the webpage
        logging.debug(f"Making HTTP request to URL: {url}")
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        logging.debug(f"Downloading webpage from URL: {url} to filepath: {sanitized_filepath}")

        # Write the content to a file
        with open(sanitized_filepath, 'w', encoding='utf-8') as file:
            file.write(response.text)

    except Exception as e:
        logging.error(f"Error downloading {url} to {sanitized_filepath}: {e}", exc_info=True)