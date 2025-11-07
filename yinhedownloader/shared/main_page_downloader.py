import os
import logging
from datetime import datetime
from shared.webpage_downloader import download_webpage
from shared.utils import get_full_day_folder
from shared.html_loader import load_html_as_dom_tree
from gewolib.category_link_extractor import extract_category_links

def download_main_page(root_folder,MAIN_URL,MAIN_PAGE_FILENAME, overwrite=False):
    try:
        current_date = datetime.now().strftime("%d.%m.%Y")
        full_day_folder = os.path.join(root_folder, f"Full_{current_date}")
        main_page_path = os.path.join(full_day_folder, MAIN_PAGE_FILENAME)

        logging.info(f"Downloading main page from URL: {MAIN_URL}")
        if download_webpage(MAIN_URL, main_page_path, overwrite=overwrite):
            return os.path.abspath(main_page_path)
        else:
            return None
    except Exception as e:
        logging.error(f"Error downloading main page: {e}", exc_info=True)
        return None










