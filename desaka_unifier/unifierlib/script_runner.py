"""
Script runner module for desaka_unifier project.
Contains logic for parallel execution of eshop downloader scripts.
"""

import os
import sys
import logging
import subprocess
import threading
import signal
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time
from .language_utils import language_to_country_code

# Import subprocess constants for Windows
if sys.platform == "win32":
    import subprocess


class ScriptRunner:
    """Class for managing parallel execution of eshop downloader scripts."""

    def __init__(self):
        self.running_processes = {}
        self.completed_scripts = []
        self.failed_scripts = []

    def run_scripts_parallel(self, eshop_list: List[Dict[str, Any]], language: str, result_dir: str,
                             debug: bool = False, overwrite: bool = False, max_workers: int = 5) -> bool:
        """
        Run eshop downloader scripts in parallel with progress tracking.

        Args:
            eshop_list (List[Dict[str, Any]]): List of eshop information from EshopList.csv
            language (str): Language code to pass to scripts
            result_dir (str): Base result directory
            debug (bool): Debug flag to pass to scripts
            overwrite (bool): Overwrite flag to pass to scripts
            max_workers (int): Maximum number of parallel workers

        Returns:
            bool: True if all scripts completed successfully, False otherwise
        """
        if not eshop_list:
            logging.warning("No eshop scripts to run")
            return True

        logging.info(f"Starting parallel execution of {len(eshop_list)} eshop scripts")

        try:
            # Create progress bar
            with tqdm(total=len(eshop_list), desc="Running eshop scripts", unit="script") as pbar:
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all scripts for execution
                    future_to_eshop = {
                        executor.submit(self._run_single_script, eshop, language, result_dir, debug, overwrite): eshop
                        for eshop in eshop_list
                    }

                    # Process completed scripts
                    for future in as_completed(future_to_eshop):
                        eshop = future_to_eshop[future]
                        try:
                            success = future.result()
                            if success:
                                self.completed_scripts.append(eshop)
                                logging.debug(f"Script completed successfully: {eshop.get('Script', 'Unknown')}")
                            else:
                                self.failed_scripts.append(eshop)
                                logging.error(f"Script failed: {eshop.get('Script', 'Unknown')}")
                        except Exception as e:
                            self.failed_scripts.append(eshop)
                            logging.error(f"Exception in script {eshop.get('Script', 'Unknown')}: {str(e)}", exc_info=True)

                        # Update progress bar
                        pbar.update(1)
                        pbar.set_postfix({
                            'Completed': len(self.completed_scripts),
                            'Failed': len(self.failed_scripts)
                        })
        except KeyboardInterrupt:
            logging.warning("Keyboard interrupt received during script execution")
            self.stop_all_scripts()
            raise

        # Log final results
        total_scripts = len(eshop_list)
        successful_scripts = len(self.completed_scripts)
        failed_scripts = len(self.failed_scripts)

        logging.info(f"Script execution summary:")
        logging.info(f"  - Total scripts: {total_scripts}")
        logging.info(f"  - Successful: {successful_scripts}")
        logging.info(f"  - Failed: {failed_scripts}")

        if failed_scripts > 0:
            logging.warning(f"Failed scripts: {[eshop.get('Script', 'Unknown') for eshop in self.failed_scripts]}")

        return failed_scripts == 0

    def _run_single_script(self, eshop: Dict[str, Any], language: str, result_dir: str,
                          debug: bool, overwrite: bool) -> bool:
        """
        Run a single eshop downloader script in its own window.

        Args:
            eshop (Dict[str, Any]): Eshop information containing Name, URL, Script
            language (str): Language code to pass to the script
            result_dir (str): Base result directory
            debug (bool): Debug flag to pass to script
            overwrite (bool): Overwrite flag to pass to script

        Returns:
            bool: True if script completed successfully, False otherwise
        """
        script_path = eshop.get('Script', '')
        eshop_name = eshop.get('Name', 'Unknown')

        if not script_path:
            logging.error(f"No script path provided for eshop: {eshop_name}")
            return False

        # Convert relative path to absolute path
        if script_path.startswith('../'):
            # script_runner.py is in workspace/desaka_unifier/unifierlib/
            # We need to go up to workspace/desaka_unifier level first, then resolve relative path
            # This gets us to workspace/desaka_unifier
            unifier_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            abs_script_path = os.path.normpath(os.path.join(unifier_dir, script_path))
        else:
            abs_script_path = script_path

        try:
            logging.debug(f"Starting script: {script_path} for eshop: {eshop_name}")
            logging.debug(f"Script relative path: {script_path}")
            logging.debug(f"Script runner location: {os.path.abspath(__file__)}")
            logging.debug(f"Unifierlib directory: {os.path.dirname(os.path.abspath(__file__))}")
            logging.debug(f"Unifier directory: {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}")
            logging.debug(f"Calculated absolute path: {abs_script_path}")
            logging.debug(f"Script exists: {os.path.exists(abs_script_path)}")
            if os.path.exists(abs_script_path):
                logging.debug(f"Script file size: {os.path.getsize(abs_script_path)} bytes")
            else:
                # List directory contents to help debug
                script_dir_parent = os.path.dirname(abs_script_path)
                if os.path.exists(script_dir_parent):
                    logging.debug(f"Contents of {script_dir_parent}: {os.listdir(script_dir_parent)}")
                else:
                    logging.debug(f"Parent directory {script_dir_parent} does not exist")

            # Check if script exists - if not, this is an error
            if not os.path.exists(abs_script_path):
                logging.error(f"Script not found: {abs_script_path} for eshop: {eshop_name}")
                logging.error(f"Please ensure the downloader script exists at the specified path")
                return False  # Return failure as this is a real error

            # Get script directory and filename
            script_dir = os.path.dirname(abs_script_path)
            script_filename =abs_script_path

            # Determine correct parameters based on eshop type
            script_args = [sys.executable, script_filename]

            # Calculate eshop-specific result directory
            if eshop_name.lower() in ['pincesobchod', 'pincesobchod_cs', 'pincesobchod_sk'] or 'pincesobchod' in eshop_name.lower():
                # Pincesobchod adds language suffix itself, so just pass base folder
                eshop_result_dir = os.path.join(result_dir, "Pincesobchod")
            else:
                # Other eshops use eshop name as result dir
                eshop_result_dir = os.path.join(result_dir, eshop_name)

            # Add common parameters for all scripts
            script_args.extend(["--result_folder", eshop_result_dir])

            if debug:
                script_args.append("--debug")

            if overwrite:
                script_args.append("--overwrite")

            # Pincesobchod uses different parameters than other eshops
            if eshop_name.lower() in ['pincesobchod', 'pincesobchod_cs', 'pincesobchod_sk'] or 'pincesobchod' in eshop_name.lower():
                # Pincesobchod expects --country_code parameter
                country_code = language_to_country_code(language)
                if country_code:
                    script_args.extend(["--country_code", country_code])
                    logging.debug(f"Using pincesobchod parameters: --country_code {country_code} (converted from language {language}), --result_folder {eshop_result_dir}")
                else:
                    logging.error(f"Failed to convert language '{language}' to country code for pincesobchod")
                    return False
            else:
                # Other eshops don't expect any language parameter
                logging.debug(f"Using standard parameters: --result_folder {eshop_result_dir}")

            # Log final command for debugging
            logging.debug(f"Final script command: {' '.join(script_args)}")
            logging.debug(f"Working directory: {script_dir}")

            # Run script in new window (Windows specific)
            if sys.platform == "win32":
                # Use subprocess.Popen with CREATE_NEW_CONSOLE to create new window
                # Don't redirect stdout/stderr so the console window shows output
                process = subprocess.Popen(
                    script_args,
                    cwd=script_dir,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                batch_file_to_cleanup = None
            else:
                # For non-Windows systems, run directly
                process = subprocess.Popen(
                    script_args,
                    cwd=script_dir
                )
                batch_file_to_cleanup = None

            # Store process info
            self.running_processes[eshop_name] = {
                'process': process,
                'script_path': abs_script_path,
                'start_time': time.time()
            }

            try:
                # Wait for process to complete
                return_code = process.wait()

                # Remove from running processes
                if eshop_name in self.running_processes:
                    del self.running_processes[eshop_name]

                if return_code == 0:
                    logging.debug(f"Script completed successfully: {script_path}")
                    return True
                else:
                    logging.error(f"Script failed with return code {return_code}: {script_path}")
                    return False
            except KeyboardInterrupt:
                # If interrupted, terminate the process and clean up
                logging.warning(f"Keyboard interrupt received while running script: {script_path}")
                try:
                    if sys.platform == "win32":
                        process.terminate()
                        try:
                            process.wait(timeout=3)
                        except subprocess.TimeoutExpired:
                            process.kill()
                    else:
                        process.terminate()
                        try:
                            process.wait(timeout=3)
                        except subprocess.TimeoutExpired:
                            process.kill()
                except Exception as e:
                    logging.error(f"Error terminating interrupted script {script_path}: {str(e)}")

                # Remove from running processes
                if eshop_name in self.running_processes:
                    del self.running_processes[eshop_name]

                # Re-raise the KeyboardInterrupt
                raise

        except Exception as e:
            logging.error(f"Error running script {script_path}: {str(e)}", exc_info=True)
            return False

    def get_running_scripts_count(self) -> int:
        """Get the number of currently running scripts."""
        return len(self.running_processes)

    def get_completed_scripts_count(self) -> int:
        """Get the number of completed scripts."""
        return len(self.completed_scripts)

    def get_failed_scripts_count(self) -> int:
        """Get the number of failed scripts."""
        return len(self.failed_scripts)

    def stop_all_scripts(self):
        """Stop all running scripts."""
        logging.info("Stopping all running scripts...")
        for eshop_name, process_info in list(self.running_processes.items()):
            try:
                process = process_info['process']

                if sys.platform == "win32":
                    # On Windows, we need to kill the entire process tree
                    # because we created new console windows
                    try:
                        # Try to terminate gracefully first
                        process.terminate()
                        # Wait a bit for graceful termination
                        try:
                            process.wait(timeout=3)
                            logging.info(f"Gracefully terminated script for eshop: {eshop_name}")
                        except subprocess.TimeoutExpired:
                            # If graceful termination fails, force kill
                            process.kill()
                            logging.info(f"Force killed script for eshop: {eshop_name}")
                    except Exception as e:
                        # If terminate/kill fails, try using taskkill to kill the process tree
                        try:
                            subprocess.run(['taskkill', '/F', '/T', '/PID', str(process.pid)],
                                         check=False, capture_output=True)
                            logging.info(f"Used taskkill to terminate script for eshop: {eshop_name}")
                        except Exception as e2:
                            logging.error(f"Failed to kill process tree for eshop {eshop_name}: {str(e2)}")
                else:
                    # On Unix-like systems
                    try:
                        # Send SIGTERM first
                        process.terminate()
                        try:
                            process.wait(timeout=3)
                            logging.info(f"Gracefully terminated script for eshop: {eshop_name}")
                        except subprocess.TimeoutExpired:
                            # If SIGTERM doesn't work, send SIGKILL
                            process.kill()
                            logging.info(f"Force killed script for eshop: {eshop_name}")
                    except Exception as e:
                        logging.error(f"Error terminating script for eshop {eshop_name}: {str(e)}")

            except Exception as e:
                logging.error(f"Error stopping script for eshop {eshop_name}: {str(e)}")

        self.running_processes.clear()
        logging.info("All script termination attempts completed.")
