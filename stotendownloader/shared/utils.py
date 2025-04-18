import re
from urllib.parse import quote
import html
from datetime import datetime
CURRENT_DATE  = datetime.now().strftime("%d.%m.%Y")
import os
import sys  # Import sys to access sys.argv
import logging

def sanitize_filename(filename):
    """
    Sanitize the filename by replacing illegal characters with their URL-encoded equivalents.
    """
    # Replace illegal characters with URL-encoded equivalents
    sanitized = re.sub(r'[<>:"/\|?*/]', lambda match: quote(match.group(0)), filename.replace("/","_"))
    return sanitized
    

def get_full_day_folder(root_folder):
    return f"{root_folder}/Full_{CURRENT_DATE}"

def get_pages_folder(root_folder):
    return f"{get_full_day_folder(root_folder)}/Pages"

def get_products_folder(root_folder):
    return f"{get_full_day_folder(root_folder)}/Products"

def get_photos_folder(root_folder):
    return f"{get_full_day_folder(root_folder)}/Photos"

def get_script_name():
    script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]  # Use sys.argv[0] to get the main script name
    logging.debug(f"Script name determined as: {script_name}")
    return script_name

def get_log_filename(log_dir):
    script_name = get_script_name()
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"{script_name}_Log_{current_time}.log"
    log_full_path = os.path.join(log_dir, log_filename)
    logging.debug(f"Log filename generated as: {log_full_path}")
    return log_full_path











