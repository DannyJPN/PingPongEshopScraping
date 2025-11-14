"""
Memory manager module for desaka_unifier project.
Contains specific methods for loading and saving various memory files.
"""

import os
import logging
from typing import List, Dict, Any
from shared.file_ops import load_txt_file, load_csv_file, save_csv_file
from .constants import (
    BRAND_CODE_LIST, CATEGORY_CODE_LIST, CATEGORY_ID_LIST, CATEGORY_LIST,
    CATEGORY_SUB_CODE_LIST, DEFAULT_EXPORT_PRODUCT_VALUES,
    ESHOP_LIST, ITEM_FILTER, WRONGS_FILE, SUPPORTED_LANGUAGES_FILE,
    CATEGORY_MAPPING_GLAMI_PREFIX, CATEGORY_MAPPING_GOOGLE_PREFIX,
    CATEGORY_MAPPING_HEUREKA_PREFIX, CATEGORY_MAPPING_ZBOZI_PREFIX,
    KEYWORDS_GOOGLE_PREFIX, KEYWORDS_ZBOZI_PREFIX,
    NAME_MEMORY_PREFIX, DESC_MEMORY_PREFIX, SHORT_DESC_MEMORY_PREFIX,
    VARIANT_NAME_MEMORY_PREFIX, VARIANT_VALUE_MEMORY_PREFIX,
    PRODUCT_MODEL_MEMORY_PREFIX, PRODUCT_BRAND_MEMORY_PREFIX,
    PRODUCT_TYPE_MEMORY_PREFIX, CATEGORY_MEMORY_PREFIX,
    CATEGORY_NAME_MEMORY_PREFIX, STOCK_STATUS_MEMORY_PREFIX
)


def load_supported_languages(config_dir: str) -> List[str]:
    """
    Load the supported languages from the SupportedLanguages.csv file in Config directory.

    Args:
        config_dir (str): Path to the Config directory

    Returns:
        List[str]: List of supported language codes (uppercase)
    """
    file_path = os.path.join(config_dir, SUPPORTED_LANGUAGES_FILE)
    try:
        # Load as CSV and extract language codes
        csv_data = load_csv_file(file_path)
        supported_languages = [row['language_code'].upper() for row in csv_data]
        logging.info(f"Supported languages loaded: {supported_languages}")
        return supported_languages
    except FileNotFoundError:
        logging.error(f"Supported languages file not found: {file_path}")
        return []
    except Exception as e:
        logging.error(f"Error loading supported languages from {file_path}: {str(e)}", exc_info=True)
        return []


def load_eshop_list(memory_dir: str) -> List[Dict[str, Any]]:
    """
    Load eshop list from EshopList.csv file.

    Args:
        memory_dir (str): Path to the Memory directory

    Returns:
        List[Dict[str, Any]]: List of eshop information
    """
    eshop_list_path = os.path.join(memory_dir, ESHOP_LIST)

    try:
        eshop_data = load_csv_file(eshop_list_path)
        logging.info(f"Loaded {len(eshop_data)} eshops from {ESHOP_LIST}")

        # Validate required fields
        valid_eshops = []
        for eshop in eshop_data:
            if all(field in eshop for field in ['Name', 'URL', 'Script']):
                valid_eshops.append(eshop)
            else:
                logging.warning(f"Invalid eshop entry (missing required fields): {eshop}")

        logging.info(f"Found {len(valid_eshops)} valid eshops")
        return valid_eshops

    except Exception as e:
        logging.error(f"Error loading eshop list: {str(e)}", exc_info=True)
        return []





def save_memory_file(memory_key: str, memory_data: Dict[str, Any], language: str, memory_dir: str = None):
    """
    Save memory data to appropriate file using generic file operations.

    Args:
        memory_key (str): Key identifying the memory type (e.g., 'CategoryMemory_CS')
        memory_data (Dict[str, Any]): Memory data to save
        language (str): Language code
        memory_dir (str): Memory directory path (optional, will use default if not provided)
    """
    if not memory_dir:
        # Get default memory directory from script location
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        memory_dir = os.path.join(script_dir, "Memory")

    try:
        # Determine file name based on memory key
        if memory_key.endswith(f"_{language}"):
            file_name = f"{memory_key}.csv"
        else:
            file_name = f"{memory_key}.csv"

        file_path = os.path.join(memory_dir, file_name)

        # Convert dictionary to list of dictionaries for CSV format
        if isinstance(memory_data, dict):
            csv_data = [{"KEY": key, "VALUE": value} for key, value in memory_data.items()]
        else:
            csv_data = memory_data

        # Use generic save_csv_file from file_ops
        save_csv_file(csv_data, file_path)
        logging.debug(f"Successfully saved memory file: {file_path}")

    except Exception as e:
        logging.error(f"Error saving memory file {memory_key}: {str(e)}", exc_info=True)


def load_all_memory_files(memory_dir: str, language: str) -> Dict[str, Any]:
    """
    Load all memory files into a dictionary.

    Args:
        memory_dir (str): Path to the Memory directory
        language (str): Language code (e.g., 'CS', 'SK')

    Returns:
        Dict[str, Any]: Dictionary containing all loaded memory data
    """
    memory_data = {}

    try:
        # Define memory files to load using constants
        memory_files = {
            # Language-independent files
            'BrandCodeList': BRAND_CODE_LIST,
            'CategoryCodeList': CATEGORY_CODE_LIST,
            'CategoryIDList': CATEGORY_ID_LIST,
            'CategoryList': CATEGORY_LIST,
            'CategorySubCodeList': CATEGORY_SUB_CODE_LIST,
            'DefaultExportProductValues': DEFAULT_EXPORT_PRODUCT_VALUES,
            'EshopList': ESHOP_LIST,
            'ItemFilter': ITEM_FILTER,
            'Wrongs': WRONGS_FILE,

            # Language-dependent files
            f'{CATEGORY_MAPPING_GLAMI_PREFIX}_{language}': f'{CATEGORY_MAPPING_GLAMI_PREFIX}_{language}.csv',
            f'{CATEGORY_MAPPING_GOOGLE_PREFIX}_{language}': f'{CATEGORY_MAPPING_GOOGLE_PREFIX}_{language}.csv',
            f'{CATEGORY_MAPPING_HEUREKA_PREFIX}_{language}': f'{CATEGORY_MAPPING_HEUREKA_PREFIX}_{language}.csv',
            f'{CATEGORY_MAPPING_ZBOZI_PREFIX}_{language}': f'{CATEGORY_MAPPING_ZBOZI_PREFIX}_{language}.csv',
            f'{CATEGORY_MEMORY_PREFIX}_{language}': f'{CATEGORY_MEMORY_PREFIX}_{language}.csv',
            f'{CATEGORY_NAME_MEMORY_PREFIX}_{language}': f'{CATEGORY_NAME_MEMORY_PREFIX}_{language}.csv',
            f'{DESC_MEMORY_PREFIX}_{language}': f'{DESC_MEMORY_PREFIX}_{language}.csv',
            f'{KEYWORDS_GOOGLE_PREFIX}_{language}': f'{KEYWORDS_GOOGLE_PREFIX}_{language}.csv',
            f'{KEYWORDS_ZBOZI_PREFIX}_{language}': f'{KEYWORDS_ZBOZI_PREFIX}_{language}.csv',
            f'{NAME_MEMORY_PREFIX}_{language}': f'{NAME_MEMORY_PREFIX}_{language}.csv',
            f'{PRODUCT_BRAND_MEMORY_PREFIX}_{language}': f'{PRODUCT_BRAND_MEMORY_PREFIX}_{language}.csv',
            f'{PRODUCT_MODEL_MEMORY_PREFIX}_{language}': f'{PRODUCT_MODEL_MEMORY_PREFIX}_{language}.csv',
            f'{PRODUCT_TYPE_MEMORY_PREFIX}_{language}': f'{PRODUCT_TYPE_MEMORY_PREFIX}_{language}.csv',
            f'{SHORT_DESC_MEMORY_PREFIX}_{language}': f'{SHORT_DESC_MEMORY_PREFIX}_{language}.csv',
            f'{VARIANT_NAME_MEMORY_PREFIX}_{language}': f'{VARIANT_NAME_MEMORY_PREFIX}_{language}.csv',
            f'{VARIANT_VALUE_MEMORY_PREFIX}_{language}': f'{VARIANT_VALUE_MEMORY_PREFIX}_{language}.csv',
            f'{STOCK_STATUS_MEMORY_PREFIX}_{language}': f'{STOCK_STATUS_MEMORY_PREFIX}_{language}.csv',
        }

        for memory_key, filename in memory_files.items():
            file_path = os.path.join(memory_dir, filename)

            try:
                if filename.endswith('.csv'):
                    # Load CSV file
                    csv_data = load_csv_file(file_path)

                    # Check if CSV has KEY/VALUE structure
                    if csv_data and len(csv_data) > 0:
                        first_row = csv_data[0]
                        if 'KEY' in first_row and 'VALUE' in first_row:
                            # Convert list of dicts to simple dict for KEY/VALUE files
                            memory_dict = {}
                            for row in csv_data:
                                if 'KEY' in row and 'VALUE' in row:
                                    memory_dict[row['KEY']] = row['VALUE']
                            memory_data[memory_key] = memory_dict
                        else:
                            # Keep as list for other CSV files
                            memory_data[memory_key] = csv_data
                    else:
                        # Empty file
                        memory_data[memory_key] = {}

                elif filename.endswith('.txt'):
                    # Load TXT file
                    txt_data = load_txt_file(file_path)
                    memory_data[memory_key] = txt_data

                logging.debug(f"Loaded memory file: {filename}")

            except FileNotFoundError:
                logging.debug(f"Memory file not found (will be created if needed): {file_path}")
                memory_data[memory_key] = {} if filename.endswith('.csv') else []
            except Exception as e:
                logging.warning(f"Error loading memory file {filename}: {str(e)}")
                memory_data[memory_key] = {} if filename.endswith('.csv') else []

        logging.info(f"Loaded {len(memory_data)} memory files for language {language}")
        return memory_data

    except Exception as e:
        logging.error(f"Error loading memory files: {str(e)}", exc_info=True)
        return {}


def load_all_trash_files(memory_dir: str, language: str) -> Dict[str, Any]:
    """
    Load all trash files (negative examples for fine-tuning) into a dictionary.

    Trash files have the same structure as Memory files but contain rejected/incorrect examples.
    File naming convention: {MemoryPrefix}Trash_{language}.csv

    Args:
        memory_dir (str): Path to the Memory directory
        language (str): Language code (e.g., 'CS', 'SK')

    Returns:
        Dict[str, Any]: Dictionary containing all loaded trash data
    """
    trash_data = {}

    try:
        # Define trash files to load (parallel to memory files)
        # Trash files are optional - they may not exist
        trash_files = {
            # Language-dependent trash files
            f'{CATEGORY_MAPPING_GLAMI_PREFIX}Trash_{language}': f'{CATEGORY_MAPPING_GLAMI_PREFIX}Trash_{language}.csv',
            f'{CATEGORY_MAPPING_GOOGLE_PREFIX}Trash_{language}': f'{CATEGORY_MAPPING_GOOGLE_PREFIX}Trash_{language}.csv',
            f'{CATEGORY_MAPPING_HEUREKA_PREFIX}Trash_{language}': f'{CATEGORY_MAPPING_HEUREKA_PREFIX}Trash_{language}.csv',
            f'{CATEGORY_MAPPING_ZBOZI_PREFIX}Trash_{language}': f'{CATEGORY_MAPPING_ZBOZI_PREFIX}Trash_{language}.csv',
            f'{CATEGORY_MEMORY_PREFIX}Trash_{language}': f'{CATEGORY_MEMORY_PREFIX}Trash_{language}.csv',
            f'{CATEGORY_NAME_MEMORY_PREFIX}Trash_{language}': f'{CATEGORY_NAME_MEMORY_PREFIX}Trash_{language}.csv',
            f'{DESC_MEMORY_PREFIX}Trash_{language}': f'{DESC_MEMORY_PREFIX}Trash_{language}.csv',
            f'{KEYWORDS_GOOGLE_PREFIX}Trash_{language}': f'{KEYWORDS_GOOGLE_PREFIX}Trash_{language}.csv',
            f'{KEYWORDS_ZBOZI_PREFIX}Trash_{language}': f'{KEYWORDS_ZBOZI_PREFIX}Trash_{language}.csv',
            f'{NAME_MEMORY_PREFIX}Trash_{language}': f'{NAME_MEMORY_PREFIX}Trash_{language}.csv',
            f'{PRODUCT_BRAND_MEMORY_PREFIX}Trash_{language}': f'{PRODUCT_BRAND_MEMORY_PREFIX}Trash_{language}.csv',
            f'{PRODUCT_MODEL_MEMORY_PREFIX}Trash_{language}': f'{PRODUCT_MODEL_MEMORY_PREFIX}Trash_{language}.csv',
            f'{PRODUCT_TYPE_MEMORY_PREFIX}Trash_{language}': f'{PRODUCT_TYPE_MEMORY_PREFIX}Trash_{language}.csv',
            f'{SHORT_DESC_MEMORY_PREFIX}Trash_{language}': f'{SHORT_DESC_MEMORY_PREFIX}Trash_{language}.csv',
            f'{VARIANT_NAME_MEMORY_PREFIX}Trash_{language}': f'{VARIANT_NAME_MEMORY_PREFIX}Trash_{language}.csv',
            f'{VARIANT_VALUE_MEMORY_PREFIX}Trash_{language}': f'{VARIANT_VALUE_MEMORY_PREFIX}Trash_{language}.csv',
            f'{STOCK_STATUS_MEMORY_PREFIX}Trash_{language}': f'{STOCK_STATUS_MEMORY_PREFIX}Trash_{language}.csv',
        }

        trash_files_found = 0
        for trash_key, filename in trash_files.items():
            file_path = os.path.join(memory_dir, filename)

            try:
                if filename.endswith('.csv'):
                    # Load CSV file
                    csv_data = load_csv_file(file_path)

                    # Check if CSV has KEY/VALUE structure
                    if csv_data and len(csv_data) > 0:
                        first_row = csv_data[0]
                        if 'KEY' in first_row and 'VALUE' in first_row:
                            # Convert list of dicts to simple dict for KEY/VALUE files
                            trash_dict = {}
                            for row in csv_data:
                                if 'KEY' in row and 'VALUE' in row:
                                    trash_dict[row['KEY']] = row['VALUE']
                            trash_data[trash_key] = trash_dict
                            trash_files_found += 1
                        else:
                            # Keep as list for other CSV files
                            trash_data[trash_key] = csv_data
                            trash_files_found += 1
                    else:
                        # Empty file
                        trash_data[trash_key] = {}

                logging.debug(f"Loaded trash file: {filename}")

            except FileNotFoundError:
                # Trash files are optional - don't log as warning
                logging.debug(f"Trash file not found (optional): {file_path}")
                trash_data[trash_key] = {}
            except Exception as e:
                logging.warning(f"Error loading trash file {filename}: {str(e)}")
                trash_data[trash_key] = {}

        if trash_files_found > 0:
            logging.info(f"Loaded {trash_files_found} trash files for language {language} (for fine-tuning negative examples)")
        else:
            logging.info(f"No trash files found for language {language} (fine-tuning will use only positive examples)")

        return trash_data

    except Exception as e:
        logging.error(f"Error loading trash files: {str(e)}", exc_info=True)
        return {}


def load_frequently_used_memory_files(memory_dir: str, language: str) -> Dict[str, Any]:
    """
    Load frequently used memory files that should be cached for performance.
    These files are loaded once at script start and passed as parameters.

    Args:
        memory_dir (str): Path to the Memory directory
        language (str): Language code (e.g., 'CS', 'SK')

    Returns:
        Dict[str, Any]: Dictionary containing frequently used memory data
    """
    memory_data = {}

    try:
        # Define frequently used files (read-only or rarely changing)
        frequent_files = {
            # Language-independent files (read-only)
            'BrandCodeList': BRAND_CODE_LIST,
            'CategoryCodeList': CATEGORY_CODE_LIST,
            'CategoryIDList': CATEGORY_ID_LIST,
            'CategoryList': CATEGORY_LIST,
            'CategorySubCodeList': CATEGORY_SUB_CODE_LIST,
            'DefaultExportProductValues': DEFAULT_EXPORT_PRODUCT_VALUES,
            'EshopList': ESHOP_LIST,
            'ItemFilter': ITEM_FILTER,
        }

        for memory_key, filename in frequent_files.items():
            file_path = os.path.join(memory_dir, filename)

            try:
                if filename.endswith('.csv'):
                    # Load CSV file
                    csv_data = load_csv_file(file_path)

                    # Check if CSV has KEY/VALUE structure
                    if csv_data and len(csv_data) > 0:
                        first_row = csv_data[0]
                        if 'KEY' in first_row and 'VALUE' in first_row:
                            # Convert list of dicts to simple dict for KEY/VALUE files
                            memory_dict = {}
                            for row in csv_data:
                                if 'KEY' in row and 'VALUE' in row:
                                    memory_dict[row['KEY']] = row['VALUE']
                            memory_data[memory_key] = memory_dict
                        else:
                            # Keep as list for other CSV files
                            memory_data[memory_key] = csv_data
                    else:
                        # Empty file - request data politely for read-only files
                        if 'memory' not in filename.lower():
                            logging.warning(f"Read-only file {filename} is empty. Please provide data for proper functionality.")
                        memory_data[memory_key] = {}

                elif filename.endswith('.txt'):
                    # Load TXT file
                    txt_data = load_txt_file(file_path)
                    memory_data[memory_key] = txt_data

                logging.debug(f"Loaded frequent memory file: {filename}")

            except FileNotFoundError:
                if 'memory' not in filename.lower():
                    logging.warning(f"Read-only file not found: {file_path}. Please create this file for proper functionality.")
                else:
                    logging.debug(f"Memory file not found (will be created if needed): {file_path}")
                memory_data[memory_key] = {} if filename.endswith('.csv') else []
            except Exception as e:
                logging.warning(f"Error loading frequent memory file {filename}: {str(e)}")
                memory_data[memory_key] = {} if filename.endswith('.csv') else []

        logging.info(f"Loaded {len(memory_data)} frequently used memory files for language {language}")
        return memory_data

    except Exception as e:
        logging.error(f"Error loading frequent memory files: {str(e)}", exc_info=True)
        return {}


def get_language_name(language_code: str, supported_languages_data: list = None) -> str:
    """
    Get language name from language code using SupportedLanguages.csv.

    Args:
        language_code (str): Language code (e.g., 'CS', 'SK')
        supported_languages_data (list): Pre-loaded supported languages data (optional)

    Returns:
        str: Language name (e.g., 'Czech', 'Slovak')
    """
    try:
        # Use provided data or load from file
        if supported_languages_data is None:
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_dir = os.path.join(script_dir, "Config")
            supported_languages_path = os.path.join(config_dir, SUPPORTED_LANGUAGES_FILE)

            if os.path.exists(supported_languages_path):
                supported_languages_data = load_csv_file(supported_languages_path)
            else:
                logging.warning(f"SupportedLanguages file not found: {supported_languages_path}")
                return 'English'

        # Find language name
        for lang_data in supported_languages_data:
            if lang_data.get('language_code', '').upper() == language_code.upper():
                return lang_data.get('language_name', 'English')

        # Fallback if language not found
        logging.warning(f"Language {language_code} not found in supported languages data")
        return 'English'

    except Exception as e:
        logging.warning(f"Error getting language name for {language_code}: {str(e)}")
        return 'English'


