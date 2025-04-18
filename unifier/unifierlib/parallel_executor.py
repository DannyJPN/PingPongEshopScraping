import subprocess
import logging
import platform
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

def execute_scripts_in_parallel(script_names):
    """Execute a list of e-shop scripts in parallel, each in a separate window if possible."""
    try:
        logging.info("Starting parallel execution of e-shop scripts.")

        # Initialize the progress bar
        with tqdm(total=len(script_names), desc="Executing scripts") as progress_bar:
            # Use ThreadPoolExecutor to manage parallel execution
            with ThreadPoolExecutor() as executor:
                # Submit all script execution tasks
                future_to_script = {executor.submit(execute_eshop_script, script_name): script_name for script_name in script_names}

                # Wait for all scripts to complete
                for future in as_completed(future_to_script):
                    script_name = future_to_script[future]
                    try:
                        # Result is not used, but calling result() ensures exceptions are raised
                        future.result()
                        logging.info(f"Script {script_name} completed successfully.")
                    except Exception as e:
                        logging.error(f"Script {script_name} failed: {e}", exc_info=True)
                    finally:
                        progress_bar.update(1)  # Update the progress bar after each script execution

        logging.info("All e-shop scripts have been launched and completed.")
    except Exception as e:
        logging.error(f"Failed during parallel script execution: {e}", exc_info=True)

def execute_eshop_script(script_name):
    """Execute an e-shop Python script, ensuring it runs in a separate window on Windows."""
    try:
        logging.info(f"Starting execution of e-shop script: {script_name}")

        if platform.system().lower() == 'windows':
            command = ['cmd', '/c', 'start', '/wait', 'python', script_name]
        else:
            command = ['python', script_name]

        # Use subprocess.run to wait for the script to complete
        subprocess.run(command, check=True)
        logging.info(f"E-shop script {script_name} has completed.")
    except Exception as e:
        logging.error(f"Failed to execute e-shop script {script_name}: {e}", exc_info=True)
