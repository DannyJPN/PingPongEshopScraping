import os
import logging
import requests

def download_json_file(url, filepath, lang_code, overwrite=False):
    try:
        logging.debug(f"Starting download_json_file function for URL: {url} with overwrite={overwrite}")

        # Extract the directory and filename from the filepath
        directory, filename = os.path.split(filepath)

        # Ensure the directory exists
        if not os.path.exists(directory):
            os.makedirs(directory)
            logging.debug(f"Created directory: {directory}")

        # Check if file already exists
        if not overwrite and os.path.exists(filepath):
            logging.debug(f"JSON file already exists and overwrite is not set: {filepath}")
            return

        # Get the bearer token from the environment variable
        token_env_var = f"JZ_BEARER_TOKEN_{lang_code}"
        logging.info(f"Looking for bearer token in environment variable: {token_env_var}")
        bearer_token = os.getenv(token_env_var)

        if bearer_token:
            logging.info(f"Bearer token successfully obtained from environment variable: {token_env_var}")
        else:
            logging.error(f"Bearer token NOT found in environment variable: {token_env_var}")
            logging.error("No fallback bearer token available. Please set the environment variable.")
            raise Exception(f"Bearer token not found in environment variable: {token_env_var}")

        headers = {
            "Authorization": f"bearer {bearer_token}"
        }

        logging.debug(f"Making a request to {url} with headers: {headers}")

        # Make the HTTP GET request
        response = requests.get(url, headers=headers)

        # Check if the request was successful
        if response.status_code != 200:
            logging.error(f"Error downloading JSON file: {response.text}")
            raise Exception(f"Failed to download JSON file: {response.text}")

        # Write the response content to the file
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(response.text)

        logging.info(f"Downloaded JSON file to {filepath}")

    except Exception as e:
        logging.error(f"Error downloading JSON file from {url} to {filepath}: {e}", exc_info=True)
        raise
