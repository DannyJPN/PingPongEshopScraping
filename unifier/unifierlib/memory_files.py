import os
import pandas as pd
import logging
from typing import List
import sys

from unifierlib.constants import (
    NAME_MEMORY_PREFIX,
    DESC_MEMORY_PREFIX,
    SHORT_DESC_MEMORY_PREFIX,
    VARIANT_NAME_MEMORY_PREFIX,
    VARIANT_VALUE_MEMORY_PREFIX,
    PRODUCT_MODEL_MEMORY_PREFIX,
    PRODUCT_BRAND_MEMORY_PREFIX,
    PRODUCT_TYPE_MEMORY_PREFIX,
    CATEGORY_MEMORY_PREFIX,
    SUPPORTED_LANGUAGES_LIST
)

def read_supported_languages(memory_dir: str) -> List[str]:
    """
    Read supported languages from SupportedLanguagesList.txt

    Args:
        memory_dir (str): Path to the memory directory

    Returns:
        List[str]: List of language codes

    Raises:
        FileNotFoundError: If the languages file doesn't exist
        IOError: If there are issues reading the file
    """
    languages_file = os.path.join(memory_dir, SUPPORTED_LANGUAGES_LIST)
    logging.debug(f"Starting to read languages from: {languages_file}")

    try:
        if not os.path.exists(languages_file):
            error_msg = f"Supported languages file not found: {languages_file}"
            logging.error(error_msg)
            raise FileNotFoundError(error_msg)

        with open(languages_file, 'r', encoding='utf-8') as f:
            content = f.read()
            logging.debug(f"Raw file content: {content}")
            languages = [lang.strip().upper() for lang in content.splitlines() if lang.strip()]

        if not languages:
            error_msg = f"No languages found in {languages_file}"
            logging.error(error_msg)
            raise ValueError(error_msg)

        logging.debug(f"Processed languages list: {languages}")
        logging.info(f"Loaded {len(languages)} supported languages: {languages}")
        return languages

    except Exception as e:
        logging.error(f"Error reading supported languages file: {str(e)}", exc_info=True)
        raise

def create_empty_memory_file(memory_dir: str, prefix: str, language: str) -> None:
    """
    Create empty CSV file with KEY,VALUE columns for given prefix and language

    Args:
        memory_dir (str): Path to the memory directory
        prefix (str): Memory file prefix
        language (str): Language code

    Raises:
        IOError: If there are issues creating the file
    """
    filename = f"{prefix}_{language}.csv"
    filepath = os.path.join(memory_dir, filename)

    try:
        if not os.path.exists(filepath):
            logging.info(f"Creating new memory file: {filename}")
            df = pd.DataFrame(columns=['KEY', 'VALUE'])
            df.to_csv(filepath, index=False, encoding='utf-8')
            logging.info(f"Successfully created memory file: {filename}")
        else:
            logging.debug(f"Memory file already exists: {filename}")

    except Exception as e:
        logging.error(f"Error creating memory file {filename}: {str(e)}", exc_info=True)
        raise

def create_memory_files(memory_dir: str) -> None:
    """
    Create all required memory files for each supported language

    Args:
        memory_dir (str): Path to the memory directory

    Raises:
        Exception: If there are any errors during the process
    """
    logging.info(f"Starting memory files creation in directory: {memory_dir}")

    try:
        memory_prefixes = [
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
        
        # Ensure memory directory exists
        if not os.path.exists(memory_dir):
            logging.info(f"Creating memory directory: {memory_dir}")
            os.makedirs(memory_dir)
            
        languages = read_supported_languages(memory_dir)
        total_files = len(languages) * len(memory_prefixes)
        logging.info(f"Preparing to create {total_files} memory files")
        
        created_count = 0
        for language in languages:
            for prefix in memory_prefixes:
                create_empty_memory_file(memory_dir, prefix, language)
                created_count += 1
                
        logging.info(f"Memory files creation completed. Created/checked {created_count} files")
        
    except Exception as e:
        logging.error(f"Failed to create memory files: {str(e)}", exc_info=True)
        raise
