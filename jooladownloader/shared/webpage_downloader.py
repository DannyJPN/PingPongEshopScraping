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

        # Download the webpage with comprehensive headers to avoid anti-scraping blocks
        logging.debug(f"Making HTTP request to URL: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,cs;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)

        if response.status_code == 404:
            logging.debug(f"404 Not Found for URL: {url}")
            return False
        else:
            response.raise_for_status()  # Raise an HTTPError for other bad responses

        logging.debug(f"Downloading webpage from URL: {url} to filepath: {sanitized_filepath}")

        # Write the content to a file
        with open(sanitized_filepath, 'w', encoding='utf-8') as file:
            file.write(response.text)

        return True

    except Exception as e:
        logging.error(f"Error downloading {url} to {sanitized_filepath}: {e}", exc_info=True)
        return False










