import os
import logging
import re
from typing import List, Dict
from shared.csv_handler import load_csv

def generate_script_name(eshop_name: str) -> str:
    """
    Convert eshop name to script name following the pattern.

    Args:
        eshop_name (str): Name of the eshop

    Returns:
        str: Generated script name in the format 'eshop_name_download.py'
    """
    try:
        # Replace uppercase letters with underscore and lowercase
        # Example: "SportSpin" -> "sport_spin"
        script_name = re.sub(r'(?<!^)(?=[A-Z])', '_', eshop_name).lower()
        return f"{script_name}_download.py"
    except Exception as e:
        logging.error(f"Failed to generate script name for {eshop_name}: {str(e)}", exc_info=True)
        raise

def validate_eshop_data(eshops: List[Dict[str, str]]) -> None:
    """
    Validate the eshop data from CSV.

    Args:
        eshops (List[Dict[str, str]]): List of eshop dictionaries

    Raises:
        ValueError: If validation fails
    """
    if not eshops:
        raise ValueError("EshopList.csv is empty")

    required_fields = {'Name', 'URL'}
    for idx, eshop in enumerate(eshops, 1):
        missing_fields = required_fields - set(eshop.keys())
        if missing_fields:
            raise ValueError(f"Row {idx} is missing required fields: {missing_fields}")

        if not eshop['Name'] or not eshop['URL']:
            raise ValueError(f"Row {idx} contains empty Name or URL")

def validate_download_script_exists(script_path: str, eshop_name: str) -> None:
    """
    Validate that the download script exists for the given eshop.

    Args:
        script_path (str): Full path where the script should exist
        eshop_name (str): Name of the eshop for error reporting

    Raises:
        FileNotFoundError: If the script file doesn't exist
    """
    if not os.path.exists(script_path):
        error_msg = (f"Download script for eshop '{eshop_name}' not found at {script_path}. "
                    "The script should be manually created and included in the codebase.")
        logging.error(error_msg)
        raise FileNotFoundError(error_msg)

def process_eshop_list(memory_dir: str, script_dir: str) -> None:
    """
    Process EshopList.csv and validate that required download scripts exist.

    Args:
        memory_dir (str): Directory containing EshopList.csv
        script_dir (str): Directory where scripts should exist
    """
    try:
        eshop_list_path = os.path.join(memory_dir, "EshopList.csv")

        if not os.path.exists(eshop_list_path):
            logging.error(f"EshopList.csv not found at {eshop_list_path}")
            raise FileNotFoundError(f"EshopList.csv not found at {eshop_list_path}")

        # Load eshop list
        logging.info(f"Loading eshop list from {eshop_list_path}")
        eshops, _ = load_csv(eshop_list_path)

        # Validate the loaded data
        validate_eshop_data(eshops)
        logging.info(f"Successfully loaded and validated {len(eshops)} eshops from EshopList.csv")

        # Validate that download scripts exist
        for eshop in eshops:
            try:
                script_name = generate_script_name(eshop['Name'])
                script_path = os.path.join(script_dir, script_name)
                validate_download_script_exists(script_path, eshop['Name'])
                logging.info(f"Verified download script exists: {script_path}")
            except Exception as e:
                logging.error(f"Failed to validate script for eshop {eshop['Name']}: {str(e)}", exc_info=True)
                raise

        logging.info(f"Successfully verified existence of {len(eshops)} download scripts")

    except Exception as e:
        logging.error(f"Error processing eshop list: {str(e)}", exc_info=True)
        raise

