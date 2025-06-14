"""
Directory manager module for desaka_unifier project.
Contains logic for ensuring required directories exist.
"""

import logging
import sys
from typing import List
from shared.file_ops import ensure_directory_exists


def ensure_required_directories(directories: List[str]) -> bool:
    """
    Ensure all required directories exist by calling ensure_directory_exists for each one.
    
    Args:
        directories (List[str]): List of directory paths to check/create
        
    Returns:
        bool: True if all directories exist or were created successfully, False otherwise
    """
    logging.info("Checking and creating required directories...")

    success = True
    for directory in directories:
        if not ensure_directory_exists(directory):
            logging.error(f"Failed to ensure directory exists: {directory}")
            success = False
        else:
            logging.debug(f"Directory verified: {directory}")

    if success:
        logging.info("All required directories are available.")
    else:
        logging.error("Some directories could not be created.")
        
    return success
