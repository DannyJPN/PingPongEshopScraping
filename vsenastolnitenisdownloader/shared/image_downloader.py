import os
import logging
import requests
from shared.utils import sanitize_filename  # Ensure updated import

def download_image(url, filepath, overwrite=False, debug=False):
    try:
        

        # Extract the directory and filename from the filepath
        directory, filename = os.path.split(filepath)

        # Sanitize the filename
        sanitized_filename = sanitize_filename(filename).split("%")[0]

        # Reconstruct the sanitized filepath
        sanitized_filepath = os.path.join(directory, sanitized_filename)
        logging.debug(f"Sanitized filepath: {sanitized_filepath}")

        # Check if file already exists
        if not overwrite and os.path.exists(sanitized_filepath):
            logging.debug(f"File already exists and overwrite is not set: {sanitized_filepath}")
            return True

        # Download the image
        logging.debug(f"Downloading image from URL: {url} to filepath: {sanitized_filepath}")
        response = requests.get(url)
        #response.raise_for_status()  # Raise an HTTPError for bad responses

        # Write the content to a file
        with open(sanitized_filepath, 'wb') as file:
            file.write(response.content)

        return True

    except Exception as e:
        logging.error(f"Error downloading {url} to {sanitized_filepath}: {e}", exc_info=True)
        return False
