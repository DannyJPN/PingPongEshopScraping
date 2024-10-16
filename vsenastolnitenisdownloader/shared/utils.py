import re
from urllib.parse import quote
from vsenastolnitenislib.constants import CURRENT_DATE ,CSV_OUTPUT_NAME 
import html

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

def get_csv_outfile(root_folder):
    return f"{get_full_day_folder(root_folder)}/{CSV_OUTPUT_NAME}"