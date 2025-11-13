"""
Generic Local Models client module for desaka_unifier project using Ollama.

This module provides generic methods for communicating with local LLM models
via Ollama. Includes automatic model download and management.
"""

import os
import json
import logging
import subprocess
import shutil
from typing import Dict, Any, Optional, List
from unifierlib.constants import DEFAULT_MAX_TOKENS


class LocalClient:
    """
    Generic client for local LLM models via Ollama.
    Provides basic methods for chat completions with automatic model management.
    """

    def __init__(self, use_fine_tuned_models: bool = False, fine_tuned_models: Optional[Dict[str, str]] = None,
                 model_storage_path: str = None):
        """Initialize Local client with Ollama."""
        # Get model storage path from constants or parameter
        if model_storage_path is None:
            from unifierlib.constants import LOCAL_MODEL_STORAGE_PATH
            model_storage_path = LOCAL_MODEL_STORAGE_PATH

        self.model_storage_path = model_storage_path

        # Verify Ollama is installed
        if not self._is_ollama_installed():
            raise RuntimeError(
                "Ollama is not installed. Please install from https://ollama.ai/download"
            )

        # Try to import ollama
        try:
            import ollama
            self.client = ollama.Client()
        except ImportError:
            logging.error("Ollama Python library not installed. Install with: pip install ollama")
            raise

        # Define available models (ordered by size - smallest first)
        self.models = {
            'flagship': 'qwen2.5:72b',  # Best Czech language support
            'efficient': 'qwen2.5:14b',  # Efficient Czech support
            'reasoning': 'qwen2.5:72b',  # Best for reasoning
            'creative': 'qwen2.5:72b',  # Best for creative tasks
            'tiny': 'qwen2.5:7b',  # Smallest, fastest
            'medium': 'qwen2.5:32b',  # Medium size
        }

        # Model size estimates in GB (approximate)
        self.model_sizes = {
            'qwen2.5:7b': 4.7,
            'qwen2.5:14b': 9.0,
            'qwen2.5:32b': 20.0,
            'qwen2.5:72b': 43.0,
        }

        # Fine-tuned model settings
        self.use_fine_tuned_models = use_fine_tuned_models
        self.fine_tuned_models = fine_tuned_models or {}

        # Cache of available models
        self._available_models_cache = None

    def _is_ollama_installed(self) -> bool:
        """Check if Ollama is installed on the system."""
        return shutil.which('ollama') is not None

    def _is_ollama_running(self) -> bool:
        """Check if Ollama service is running."""
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _get_available_disk_space(self) -> float:
        """
        Get available disk space in GB where models are stored.

        Returns:
            float: Available space in GB
        """
        try:
            stat = shutil.disk_usage(self.model_storage_path)
            return stat.free / (1024 ** 3)  # Convert to GB
        except Exception as e:
            logging.error(f"Error getting disk space: {str(e)}")
            return 0.0

    def _get_installed_models(self) -> List[str]:
        """
        Get list of currently installed models.

        Returns:
            List[str]: List of installed model names
        """
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                logging.error(f"Error listing models: {result.stderr}")
                return []

            # Parse output
            lines = result.stdout.strip().split('\n')
            if len(lines) <= 1:  # Only header or empty
                return []

            models = []
            for line in lines[1:]:  # Skip header
                parts = line.split()
                if parts:
                    models.append(parts[0])

            return models

        except Exception as e:
            logging.error(f"Error getting installed models: {str(e)}")
            return []

    def _download_model(self, model_name: str) -> bool:
        """
        Download a model using Ollama.

        Args:
            model_name (str): Name of the model to download

        Returns:
            bool: True if download successful, False otherwise
        """
        # Check disk space
        required_space = self.model_sizes.get(model_name, 50.0)  # Default 50GB if unknown
        available_space = self._get_available_disk_space()

        if available_space < required_space * 1.2:  # Need 20% extra for safety
            logging.error(
                f"Insufficient disk space for {model_name}. "
                f"Required: {required_space:.1f}GB, Available: {available_space:.1f}GB"
            )
            return False

        logging.info(f"Downloading model {model_name} ({required_space:.1f}GB)...")

        try:
            # Use ollama pull command
            result = subprocess.run(
                ['ollama', 'pull', model_name],
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout for download
            )

            if result.returncode == 0:
                logging.info(f"Successfully downloaded {model_name}")
                self._available_models_cache = None  # Invalidate cache
                return True
            else:
                logging.error(f"Error downloading {model_name}: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logging.error(f"Timeout downloading {model_name} (exceeded 1 hour)")
            return False
        except Exception as e:
            logging.error(f"Error downloading {model_name}: {str(e)}")
            return False

    def _ensure_model_available(self, model_name: str) -> bool:
        """
        Ensure a model is available, downloading if necessary.

        Args:
            model_name (str): Name of the model

        Returns:
            bool: True if model is available, False otherwise
        """
        # Check if model is already installed
        installed_models = self._get_installed_models()

        if model_name in installed_models:
            logging.debug(f"Model {model_name} is already installed")
            return True

        # Model not installed, try to download
        logging.info(f"Model {model_name} not found locally, attempting download...")
        return self._download_model(model_name)

    def get_model_for_task(self, task_type: str = 'general') -> str:
        """
        Get the appropriate model for a specific task type.

        Args:
            task_type (str): Type of task

        Returns:
            str: Model name to use
        """
        if self.use_fine_tuned_models and task_type in self.fine_tuned_models:
            fine_tuned_model = self.fine_tuned_models[task_type]
            if fine_tuned_model:
                logging.debug(f"Using fine-tuned model for {task_type}: {fine_tuned_model}")
                return fine_tuned_model

        task_model_mapping = {
            'general': self.models['efficient'],
            'complex': self.models['flagship'],
            'simple': self.models['tiny'],
            'reasoning': self.models['reasoning'],
            'creative': self.models['creative'],
            'category_mapping': self.models['flagship'],
            'product_analysis': self.models['flagship'],
            'text_generation': self.models['flagship'],
            'translation': self.models['flagship'],
            'name_generation': self.models['flagship'],
            'description_translation': self.models['flagship'],
            'brand_detection': self.models['efficient'],
            'type_detection': self.models['efficient'],
            'model_detection': self.models['efficient'],
            'keyword_generation': self.models['efficient']
        }

        return task_model_mapping.get(task_type, self.models['efficient'])

    def chat_completion(self, messages: List[Dict[str, str]], model: str = None,
                       temperature: float = 0.4, max_tokens: Optional[int] = None,
                       task_type: str = 'general') -> Optional[str]:
        """
        Send chat completion request to local model via Ollama.

        Args:
            messages (List[Dict[str, str]]): List of messages with 'role' and 'content'
            model (str): Model to use (if None, will be selected based on task_type)
            temperature (float): Temperature for response randomness (default: 0.4)
            max_tokens (Optional[int]): Maximum tokens in response
            task_type (str): Type of task to determine appropriate model

        Returns:
            Optional[str]: Response content or None if error
        """
        if model is None:
            model = self.get_model_for_task(task_type)

        if max_tokens is None:
            max_tokens = DEFAULT_MAX_TOKENS

        # Ensure model is available
        if not self._ensure_model_available(model):
            logging.error(f"Model {model} is not available and could not be downloaded")
            return None

        try:
            logging.debug(f"Local Ollama API call - Model: {model}, Temperature: {temperature}, Max tokens: {max_tokens}")
            logging.debug(f"Local Ollama API call - Messages: {len(messages)} messages")

            response = self.client.chat(
                model=model,
                messages=messages,
                options={
                    'temperature': temperature,
                    'num_predict': max_tokens,
                }
            )

            if response and 'message' in response:
                response_content = response['message']['content'].strip()
                logging.debug(f"Local Ollama API response received - Length: {len(response_content)} characters")
                return response_content
            else:
                logging.error("No response returned from local model")
                return None

        except Exception as e:
            logging.error(f"Error in local model chat completion: {str(e)}", exc_info=True)
            return None

    def json_completion(self, messages: List[Dict[str, str]], model: str = None,
                       temperature: float = 0.4, max_tokens: Optional[int] = None,
                       task_type: str = 'general') -> Optional[Dict[str, Any]]:
        """
        Send chat completion request expecting JSON response.

        Args:
            messages (List[Dict[str, str]]): List of messages with 'role' and 'content'
            model (str): Model to use (if None, will be selected based on task_type)
            temperature (float): Temperature for response randomness (default: 0.4)
            max_tokens (Optional[int]): Maximum tokens in response
            task_type (str): Type of task to determine appropriate model

        Returns:
            Optional[Dict[str, Any]]: Parsed JSON response or None if error
        """
        if messages and len(messages) > 0:
            last_message = messages[-1]
            if last_message.get('role') == 'user':
                last_message['content'] += "\n\nPlease return your response as valid JSON only, no additional text."

        response_text = self.chat_completion(messages, model, temperature, max_tokens, task_type)

        if not response_text:
            return None

        try:
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()

            return json.loads(response_text)

        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON from local model response: {str(e)}")
            logging.error(f"Response was: {response_text}")
            return None

    def simple_completion(self, prompt: str, model: str = None,
                         temperature: float = 0.4, max_tokens: Optional[int] = None,
                         task_type: str = 'general') -> Optional[str]:
        """
        Send simple completion request with single prompt.

        Args:
            prompt (str): The prompt to send
            model (str): Model to use (if None, will be selected based on task_type)
            temperature (float): Temperature for response randomness (default: 0.4)
            max_tokens (Optional[int]): Maximum tokens in response
            task_type (str): Type of task to determine appropriate model

        Returns:
            Optional[str]: Response content or None if error
        """
        if max_tokens is None:
            max_tokens = DEFAULT_MAX_TOKENS

        messages = [
            {"role": "user", "content": prompt}
        ]

        return self.chat_completion(messages, model, temperature, max_tokens, task_type)

    def simple_json_completion(self, prompt: str, model: str = None,
                              temperature: float = 0.4, max_tokens: Optional[int] = None,
                              task_type: str = 'general') -> Optional[Dict[str, Any]]:
        """
        Send simple completion request expecting JSON response.

        Args:
            prompt (str): The prompt to send
            model (str): Model to use (if None, will be selected based on task_type)
            temperature (float): Temperature for response randomness (default: 0.4)
            max_tokens (Optional[int]): Maximum tokens in response
            task_type (str): Type of task to determine appropriate model

        Returns:
            Optional[Dict[str, Any]]: Parsed JSON response or None if error
        """
        messages = [
            {"role": "user", "content": prompt}
        ]

        return self.json_completion(messages, model, temperature, max_tokens, task_type)

    def validate_api_key(self) -> bool:
        """
        Validate that local model system is working.

        Returns:
            bool: True if system is operational, False otherwise
        """
        try:
            # Check if Ollama is running
            if not self._is_ollama_running():
                logging.error("Ollama service is not running")
                return False

            # Try a simple completion with smallest model
            response = self.simple_completion("Hello", model=self.models['tiny'], max_tokens=5)
            return response is not None
        except Exception as e:
            logging.error(f"Local model validation failed: {str(e)}")
            return False

    def create_fine_tuning_job(self, training_file_id: str, model: str = None,
                              suffix: str = None, hyperparameters: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Create a fine-tuning job.

        Note: Fine-tuning local models requires manual process with tools like
        Unsloth, LLaMA-Factory, or Axolotl. Not supported via this API.

        Args:
            training_file_id (str): ID of the uploaded training file
            model (str): Base model to fine-tune
            suffix (str): Suffix for the fine-tuned model name
            hyperparameters (Optional[Dict[str, Any]]): Training hyperparameters

        Returns:
            Optional[str]: Fine-tuning job ID or None if error
        """
        logging.warning(
            "Local model fine-tuning requires manual process with tools like "
            "Unsloth, LLaMA-Factory, or Axolotl. Not supported via this API."
        )
        return None

    def upload_training_file(self, file_path: str) -> Optional[str]:
        """
        Upload a training file for fine-tuning.

        Note: Fine-tuning local models requires manual process.

        Args:
            file_path (str): Path to the training file

        Returns:
            Optional[str]: File ID or None if error
        """
        logging.warning("Local model fine-tuning requires manual process")
        return None

    def get_fine_tuning_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a fine-tuning job.

        Note: Fine-tuning local models requires manual process.

        Args:
            job_id (str): Fine-tuning job ID

        Returns:
            Optional[Dict[str, Any]]: Job status information or None if error
        """
        logging.warning("Local model fine-tuning requires manual process")
        return None

    def get_installed_models_info(self) -> Dict[str, Any]:
        """
        Get information about installed models and disk space.

        Returns:
            Dict[str, Any]: Information about models and storage
        """
        installed = self._get_installed_models()
        available_space = self._get_available_disk_space()

        info = {
            'installed_models': installed,
            'available_models': list(self.models.values()),
            'available_disk_space_gb': round(available_space, 2),
            'model_sizes_gb': self.model_sizes,
            'storage_path': self.model_storage_path
        }

        return info
