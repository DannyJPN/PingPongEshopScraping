import os
import subprocess
import time
import logging
from typing import List, Dict
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from .constants import SCRIPT_EXECUTION_TIMEOUT, PROGRESS_BAR_UPDATE_INTERVAL

def execute_script(script_path: str) -> Dict[str, any]:
    """
    Execute a single Python script in a new command window.

    Args:
        script_path (str): Path to the script to execute

    Returns:
        Dict containing execution status and details
    """
    script_name = os.path.basename(script_path)
    logging.debug(f"Starting execution of script: {script_name}")

    try:
        # Create platform-specific command
        if os.name == 'nt':  # Windows
            command = f'start cmd /c "python {script_path} && timeout /t 2"'
            shell = True
        else:  # Unix/Linux/MacOS
            command = ['x-terminal-emulator', '-e', f'python {script_path}; sleep 2']
            shell = False

        logging.debug(f"Executing command for {script_name}: {command}")

        # Start the process
        process = subprocess.Popen(
            command,
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait for process to complete with timeout
        try:
            process.wait(timeout=SCRIPT_EXECUTION_TIMEOUT)
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                logging.debug(f"Script {script_name} completed successfully")
            else:
                logging.error(f"Script {script_name} failed with return code {process.returncode}")
                if stderr:
                    logging.error(f"Error output from {script_name}: {stderr.decode()}")

            return {
                'script': script_name,
                'status': 'completed',
                'returncode': process.returncode,
                'error': stderr.decode() if stderr else None
            }

        except subprocess.TimeoutExpired:
            logging.error(f"Script {script_name} execution timed out after {SCRIPT_EXECUTION_TIMEOUT} seconds")
            process.kill()
            return {
                'script': script_name,
                'status': 'timeout',
                'returncode': None,
                'error': f'Script execution timed out after {SCRIPT_EXECUTION_TIMEOUT} seconds'
            }

    except Exception as e:
        error_msg = f"Failed to execute script {script_name}: {str(e)}"
        logging.error(error_msg, exc_info=True)
        return {
            'script': script_name,
            'status': 'failed',
            'returncode': None,
            'error': error_msg
        }

def execute_scripts_parallel(script_paths: List[str]) -> List[Dict[str, any]]:
    """
    Execute multiple Python scripts in parallel with progress bar.

    Args:
        script_paths (List[str]): List of paths to scripts to execute

    Returns:
        List of dictionaries containing execution results
    """
    if not script_paths:
        logging.warning("No scripts to execute")
        return []

    results = []
    total_scripts = len(script_paths)
    completed_scripts = 0

    logging.debug(f"Starting parallel execution of {total_scripts} scripts")
    logging.debug(f"Scripts to execute: {', '.join(os.path.basename(p) for p in script_paths)}")

    # Create progress bar
    with tqdm(total=total_scripts, desc="Executing scripts") as pbar:
        with ThreadPoolExecutor() as executor:
            # Start all scripts
            future_to_script = {
                executor.submit(execute_script, script_path): script_path
                for script_path in script_paths
            }

            # Monitor execution
            while completed_scripts < total_scripts:
                # Update completed count
                new_completed = sum(1 for future in future_to_script.keys() if future.done())
                if new_completed > completed_scripts:
                    pbar.update(new_completed - completed_scripts)
                    completed_scripts = new_completed

                # Collect results from completed scripts
                for future in [f for f in future_to_script.keys() if f.done()]:
                    if future not in results:
                        try:
                            result = future.result()
                            results.append(result)

                            if result['status'] == 'completed' and result['returncode'] == 0:
                                logging.debug(f"Script {result['script']} completed successfully")
                            else:
                                logging.error(
                                    f"Script {result['script']} {result['status']} with error: {result['error']}"
                                )

                        except Exception as e:
                            script_path = future_to_script[future]
                            script_name = os.path.basename(script_path)
                            error_msg = f"Failed to get result for {script_name}: {str(e)}"
                            logging.error(error_msg, exc_info=True)
                            results.append({
                                'script': script_name,
                                'status': 'failed',
                                'returncode': None,
                                'error': error_msg
                            })

                time.sleep(PROGRESS_BAR_UPDATE_INTERVAL)

    # Log final summary
    successful = sum(1 for r in results if r['status'] == 'completed' and r['returncode'] == 0)
    failed = len(results) - successful
    logging.info(f"Script execution completed: {successful} successful, {failed} failed")
    
    return results
