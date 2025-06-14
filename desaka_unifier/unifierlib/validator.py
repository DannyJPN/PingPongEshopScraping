"""
Validator module for desaka_unifier project.
Contains validation logic for languages, memory files, and other resources.
"""

import os
import logging
import sys
from typing import List
from shared.file_ops import load_txt_file





def validate_language_support(language: str, script_dir: str, supported_languages: list = None) -> bool:
    """
    Validate that the specified language is supported.

    Args:
        language (str): Language code to validate
        script_dir (str): Script directory path
        supported_languages (list): Pre-loaded list of supported languages (optional)

    Returns:
        bool: True if language is supported, False otherwise
    """
    from shared.file_ops import ensure_directory_exists

    config_dir = os.path.join(script_dir, "Config")

    # Ensure Config directory exists
    if not ensure_directory_exists(config_dir):
        logging.error(f"Failed to create Config directory: {config_dir}")
        return False

    # Check if SupportedLanguages.csv exists in Config, create if missing
    supported_languages_file = os.path.join(config_dir, "SupportedLanguages.csv")
    if not os.path.exists(supported_languages_file):
        logging.warning("SupportedLanguages.csv not found in Config directory. Creating with default values...")
        try:
            with open(supported_languages_file, 'w', encoding='utf-8') as f:
                f.write("language_code,country_code\nCS,CZ\n")
            logging.info("Created SupportedLanguages.csv with default values (CS,CZ)")
        except Exception as e:
            logging.error(f"Failed to create SupportedLanguages.csv: {str(e)}")
            return False

    # Use provided supported_languages or load them
    if supported_languages is None:
        from unifierlib.memory_manager import load_supported_languages
        supported_languages = load_supported_languages(config_dir)

    if not supported_languages:
        logging.error("No supported languages found or failed to load supported languages file.")
        return False

    # Validate the language
    if language not in supported_languages:
        logging.error(f"Language '{language}' is not supported.")
        logging.error(f"Supported languages are: {', '.join(supported_languages)}")
        return False

    logging.info(f"Language '{language}' is supported.")
    return True


def validate_memory_files(memory_dir: str, language: str) -> bool:
    """
    Validate the presence of required memory files for the specified language.
    Creates missing files as empty files with appropriate headers.

    Args:
        memory_dir (str): Path to the Memory directory
        language (str): Language code to validate files for

    Returns:
        bool: True if all required memory files exist or were created successfully
    """
    logging.info("Validating Memory files...")

    if not os.path.exists(memory_dir):
        logging.warning(f"Memory directory does not exist: {memory_dir}")
        return False

    # Define required memory files for the language
    language_dependent_files = [
        f"NameMemory_{language}.csv",
        f"DescMemory_{language}.csv",
        f"ShortDescMemory_{language}.csv",
        f"VariantNameMemory_{language}.csv",
        f"VariantValueMemory_{language}.csv",
        f"ProductModelMemory_{language}.csv",
        f"ProductBrandMemory_{language}.csv",
        f"ProductTypeMemory_{language}.csv",
        f"CategoryMemory_{language}.csv",
        f"CategoryNameMemory_{language}.csv",
        f"CategoryMappingHeureka_{language}.csv",
        f"CategoryMappingZbozi_{language}.csv",
        f"CategoryMappingGlami_{language}.csv",
        f"CategoryMappingGoogle_{language}.csv",
        f"KeywordsGoogle_{language}.csv",
        f"KeywordsZbozi_{language}.csv",
        f"StockStatusMemory_{language}.csv"
    ]

    # Language independent files
    language_independent_files = [
    ]

    # Code and enumeration files
    code_files = [
        "BrandCodeList.csv",
        "CategoryCodeList.csv",
        "CategorySubCodeList.csv",
        "CategoryList.txt",
        "CategoryIDList.csv"
    ]

    # Working and output data files
    data_files = [
        "DefaultUnifiedProductValues.csv",
        "ItemFilter.csv",
        "EshopList.csv"
    ]

    # Special exclusion file
    special_files = [
        "Wrongs.txt"
    ]

    all_required_files = (language_dependent_files + language_independent_files +
                         code_files + data_files + special_files)

    missing_files = []
    existing_files = []
    created_files = []

    for filename in all_required_files:
        file_path = os.path.join(memory_dir, filename)
        if os.path.exists(file_path):
            existing_files.append(filename)
            logging.debug(f"Memory file exists: {filename}")
        else:
            missing_files.append(filename)
            logging.warning(f"Memory file missing: {filename}")

            # Create the missing file
            if _create_empty_memory_file(file_path, filename):
                created_files.append(filename)
                logging.info(f"Created empty memory file: {filename}")
            else:
                logging.error(f"Failed to create memory file: {filename}")
                return False

    # Log summary
    logging.info(f"Memory files validation summary:")
    logging.info(f"  - Existing files: {len(existing_files)}")
    logging.info(f"  - Missing files: {len(missing_files)}")
    logging.info(f"  - Created files: {len(created_files)}")

    if created_files:
        logging.info(f"Created memory files: {', '.join(created_files)}")

    logging.info("All required memory files are now present.")
    return True


def _create_empty_memory_file(file_path: str, filename: str) -> bool:
    """
    Create an empty memory file with appropriate headers.

    Args:
        file_path (str): Full path to the file to create
        filename (str): Name of the file (used to determine content type)

    Returns:
        bool: True if file was created successfully, False otherwise
    """
    try:
        if filename.endswith('.csv'):
            # CSV files get KEY,VALUE header
            content = "KEY,VALUE\n"
        elif filename.endswith('.txt'):
            # TXT files are created empty
            content = ""
        else:
            # Default to empty
            content = ""

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    except Exception as e:
        logging.error(f"Error creating file {file_path}: {str(e)}", exc_info=True)
        return False



