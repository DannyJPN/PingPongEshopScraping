import os
import logging
from shared.file_loader import load_csv_file
from unifierlib.constants import ESHOP_LIST

def load_eshop_names(memory_dir):
    """Load e-shop names from EshopList.csv."""
    try:
        eshop_list_path = os.path.join(memory_dir, ESHOP_LIST)
        eshop_data = load_csv_file(eshop_list_path)
        eshop_names = [entry['Name'] for entry in eshop_data]
        logging.info(f"Loaded {len(eshop_names)} e-shop names from {ESHOP_LIST}")
        return eshop_names
    except Exception as e:
        logging.error(f"Error loading e-shop names: {e}", exc_info=True)
        raise