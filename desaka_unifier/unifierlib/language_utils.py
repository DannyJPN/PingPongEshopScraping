"""
Language utilities for converting between language codes and country codes.

This module provides utilities for converting ISO 639-1 language codes
to ISO 3166-1 country codes, which is needed for pincesobchod integration.
"""

import os
import csv
import logging
from typing import Optional, Dict
from .constants import SUPPORTED_LANGUAGES_FILE


def _load_language_country_mapping() -> Dict[str, str]:
    """
    Load language to country mapping from SupportedLanguages.txt CSV file.

    Returns:
        Dict[str, str]: Dictionary mapping language codes to country codes (both lowercase)
    """
    mapping = {}

    # Get the path to the Config directory
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_file = os.path.join(current_dir, "Config", SUPPORTED_LANGUAGES_FILE)

    try:
        with open(config_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                language = row['language_code'].strip().lower()
                country = row['country_code'].strip().lower()
                mapping[language] = country

        logging.debug(f"Loaded {len(mapping)} language-country mappings from {config_file}")
        return mapping

    except FileNotFoundError:
        logging.error(f"{SUPPORTED_LANGUAGES_FILE} not found at: {config_file}")
        return {}
    except Exception as e:
        logging.error(f"Error loading language-country mapping: {str(e)}", exc_info=True)
        return {}


def language_to_country_code(language_code: str) -> Optional[str]:
    """
    Convert ISO 639-1 language code to ISO 3166-1 country code.

    This function maps language codes (used by unifier) to country codes
    (expected by pincesobchod --country_code parameter) by reading from
    the SupportedLanguages.csv file.

    Args:
        language_code (str): ISO 639-1 language code (2 characters, case insensitive)

    Returns:
        Optional[str]: ISO 3166-1 country code (lowercase) or None if mapping not found

    Examples:
        >>> language_to_country_code("CS")
        "cz"
        >>> language_to_country_code("sk")
        "sk"
        >>> language_to_country_code("en")
        "gb"
    """
    if not language_code or len(language_code) != 2:
        logging.warning(f"Invalid language code format: {language_code}")
        return None

    # Load mapping from CSV file
    mapping = _load_language_country_mapping()
    if not mapping:
        logging.error("Failed to load language-country mapping")
        return None

    # Normalize to lowercase for consistent mapping
    lang = language_code.lower()

    country_code = mapping.get(lang)

    if country_code:
        logging.debug(f"Mapped language '{language_code}' to country '{country_code}'")
        return country_code
    else:
        logging.warning(f"No country mapping found for language: {language_code}")
        return None



