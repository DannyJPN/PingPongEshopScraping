import os
import logging
from datetime import datetime
from shared.webpage_downloader import download_webpage



def download_main_page(root_folder,MAIN_URL,MAIN_PAGE_FILENAME, overwrite=False):
    try:
        current_date = datetime.now().strftime("%d.%m.%Y")
        full_day_folder = os.path.join(root_folder, f"Full_{current_date}")
        main_page_path = os.path.join(full_day_folder, MAIN_PAGE_FILENAME)

        logging.info(f"Downloading main page from URL: {MAIN_URL}")
        download_webpage(MAIN_URL, main_page_path, overwrite=overwrite)
        return os.path.abspath(main_page_path)
    except Exception as e:
        logging.error(f"Error downloading main page: {e}", exc_info=True)
        return None