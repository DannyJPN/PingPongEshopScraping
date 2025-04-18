import os
from datetime import datetime
import chardet
import logging
import sys
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_script_name():
    script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    logging.debug(f"Script name determined as: {script_name}")
    return script_name

def get_log_filename(log_dir):
    script_name = get_script_name()
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"{script_name}_Log_{current_time}.log"
    log_full_path = os.path.join(log_dir, log_filename)
    logging.debug(f"Log filename generated as: {log_full_path}")
    return log_full_path




