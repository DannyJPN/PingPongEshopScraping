import os
from datetime import datetime
import logging
from shared.utils import get_full_day_folder
from shared.utils import get_pages_folder
from shared.utils import get_products_folder
from shared.utils import get_photos_folder

def ensure_directories(root_folder):
    try:
        
        # Define the required subfolders
        full_day_folder = get_full_day_folder(root_folder)
        pages_folder    = get_pages_folder(root_folder)
        products_folder = get_products_folder(root_folder)
        photos_folder   = get_photos_folder(root_folder)

        # Create the required directories if they don't exist
        for folder in [full_day_folder, pages_folder, products_folder, photos_folder]:
            if not os.path.exists(folder):
                os.makedirs(folder)
                logging.debug(f"Created folder: {folder}")
    except Exception as e:
        logging.error(f"Error ensuring directories: {e}", exc_info=True)










