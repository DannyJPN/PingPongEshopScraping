import os
import logging
from shared.file_loader import load_csv_file, save_csv_file
from unifierlib.constants import (
    NAME_MEMORY_PREFIX,
    DESC_MEMORY_PREFIX,
    SHORT_DESC_MEMORY_PREFIX,
    VARIANT_NAME_MEMORY_PREFIX,
    VARIANT_VALUE_MEMORY_PREFIX,
    PRODUCT_MODEL_MEMORY_PREFIX,
    PRODUCT_BRAND_MEMORY_PREFIX,
    PRODUCT_TYPE_MEMORY_PREFIX,
    CATEGORY_MEMORY_PREFIX
)

MEMORY_FILE_PREFIXES = [
    NAME_MEMORY_PREFIX,
    DESC_MEMORY_PREFIX,
    SHORT_DESC_MEMORY_PREFIX,
    VARIANT_NAME_MEMORY_PREFIX,
    VARIANT_VALUE_MEMORY_PREFIX,
    PRODUCT_MODEL_MEMORY_PREFIX,
    PRODUCT_BRAND_MEMORY_PREFIX,
    PRODUCT_TYPE_MEMORY_PREFIX,
    CATEGORY_MEMORY_PREFIX
]

def load_memory_files(memory_dir, language):
    memory_files_data = {}
    for prefix in MEMORY_FILE_PREFIXES:
        file_name = f"{prefix}_{language}.csv"
        file_path = os.path.join(memory_dir, file_name)

        logging.info(f"Loading memory file: {file_name}")

        try:
            data = load_csv_file(file_path)
            memory_files_data[prefix] = data
            logging.info(f"Loaded {len(data)} entries from {file_name}")
        except Exception as e:
            logging.error(f"Failed to load memory file: {file_name}. Error: {e}", exc_info=True)
            raise

    return memory_files_data

