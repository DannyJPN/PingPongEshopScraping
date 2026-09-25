import os
import logging
from shared.utils import sanitize_filename
from shared.http_downloader import download_with_retry

def download_image(url, filepath, overwrite=False, debug=False, stats=None): 
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
 
        # Download the image with retry logic
        logging.debug(f"Downloading image from URL: {url} to filepath: {sanitized_filepath}")
        response = download_with_retry(url, stats=stats)

        if response is None:
            logging.debug(f"Failed to download image URL: {url}")
            return False

        # Write the content to a file 
        with open(sanitized_filepath, 'wb') as file: 
            file.write(response.content) 
 
        return True 
 
    except Exception as e: 
        logging.error(f"Error downloading {url} to {sanitized_filepath}: {e}", exc_info=True) 
        return False
