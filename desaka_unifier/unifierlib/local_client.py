"""
Generic Local Models client module for desaka_unifier project.

This module provides methods for communicating with local LLM models via Ollama.
Includes automatic model download and management.
"""

import os
import json
import logging
import subprocess
import shutil
import time
from typing import Dict, Any, Optional, List


class LocalClient:
    """
    Client for local LLM models using Ollama backend.
    Provides automatic model management and download.
    """

    def __init__(self, use_fine_tuned_models: bool = False, fine_tuned_models: Optional[Dict[str, str]] = None,
                 model_storage_path: str = None):
        """
        Initialize Local client with Ollama backend.

        Args:
            use_fine_tuned_models: Whether to use fine-tuned models
            fine_tuned_models: Dict of fine-tuned model mappings
            model_storage_path: Path for model storage (Ollama directory)
        """
        # Get model storage path from constants
        if model_storage_path is None:
            from unifierlib.constants import LOCAL_MODEL_STORAGE_PATH_OLLAMA
            self.storage_path = LOCAL_MODEL_STORAGE_PATH_OLLAMA
        else:
            self.storage_path = model_storage_path

        # Fine-tuned model settings
        self.use_fine_tuned_models = use_fine_tuned_models
        self.fine_tuned_models = fine_tuned_models or {}

        # Initialize Ollama client
        self.client = None
        self._init_ollama()

        logging.info("Using Ollama backend for local models")

        # Define available models
        self._init_model_catalog()

    def _init_ollama(self):
        """Initialize Ollama backend."""
        # Check if Ollama is installed
        if not shutil.which('ollama'):
            raise RuntimeError(
                "Ollama not installed. Please install from: https://ollama.ai/download"
            )

        # Check if Ollama service is running
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("Ollama service not running. Please start Ollama.")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Ollama service not responding. Please check Ollama status.")
        except Exception as e:
            raise RuntimeError(f"Ollama check failed: {str(e)}")

        # Try to import ollama library
        try:
            import ollama
            self.client = ollama.Client()
        except ImportError:
            raise RuntimeError(
                "Ollama Python library not installed. Install with: pip install ollama"
            )

    def _init_model_catalog(self):
        """Initialize model catalog for Ollama."""
        self.models = {
            'flagship': 'qwen2.5:72b',
            'efficient': 'qwen2.5:14b',
            'reasoning': 'qwen2.5:72b',
            'creative': 'qwen2.5:72b',
            'tiny': 'qwen2.5:7b',
            'medium': 'qwen2.5:32b',
            # Multimodal models
            'multimodal_flagship': 'llava-llama3:13b',
            'multimodal_efficient': 'llava-phi3',
            'multimodal_tiny': 'moondream',
            'multimodal_medium': 'qwen2-vl:7b',
            'multimodal_advanced': 'llava:34b',
        }
        self.model_sizes = {
            'qwen2.5:7b': 4.7,
            'qwen2.5:14b': 9.0,
            'qwen2.5:32b': 20.0,
            'qwen2.5:72b': 43.0,
            # Multimodal model sizes
            'llava-llama3:13b': 8.0,
            'llava-phi3': 3.8,
            'moondream': 1.8,
            'qwen2-vl:7b': 4.5,
            'llava:34b': 20.0,
        }

    def get_model_for_task(self, task_type: str = 'general') -> str:
        """Get the appropriate model for a specific task type."""
        if self.use_fine_tuned_models and task_type in self.fine_tuned_models:
            fine_tuned_model = self.fine_tuned_models[task_type]
            if fine_tuned_model:
                logging.debug(f"Using fine-tuned model for {task_type}: {fine_tuned_model}")
                return fine_tuned_model

        task_model_mapping = {
            'general': self.models.get('efficient'),
            'complex': self.models.get('flagship'),
            'simple': self.models.get('tiny'),
            'reasoning': self.models.get('reasoning'),
            'creative': self.models.get('creative'),
            'category_mapping': self.models.get('flagship'),
            'product_analysis': self.models.get('flagship'),
            'text_generation': self.models.get('flagship'),
            'translation': self.models.get('flagship'),
            'name_generation': self.models.get('flagship'),
            'description_translation': self.models.get('flagship'),
            'brand_detection': self.models.get('efficient'),
            'type_detection': self.models.get('efficient'),
            'model_detection': self.models.get('efficient'),
            'keyword_generation': self.models.get('efficient'),
            # Multimodal tasks
            'image_analysis': self.models.get('multimodal_efficient'),
            'image_description': self.models.get('multimodal_efficient'),
            'product_image_analysis': self.models.get('multimodal_flagship'),
            'ocr': self.models.get('multimodal_efficient'),
            'visual_qa': self.models.get('multimodal_medium'),
            'image_captioning': self.models.get('multimodal_tiny'),
        }

        return task_model_mapping.get(task_type, self.models.get('efficient'))

    def _ensure_model_available(self, model_name: str) -> bool:
        """
        Ensure Ollama model is available, downloading if necessary.
        Includes cleanup of incomplete downloads.
        """
        try:
            # Check if model is already installed
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                installed_models = [line.split()[0] for line in result.stdout.strip().split('\n')[1:]]
                if model_name in installed_models:
                    return True

            # Model not installed, check disk space
            required_space = self.model_sizes.get(model_name, 50.0)
            stat = shutil.disk_usage(self.storage_path)
            available_space = stat.free / (1024 ** 3)

            if available_space < required_space * 1.2:
                logging.error(
                    f"Insufficient disk space for {model_name}. "
                    f"Required: {required_space:.1f}GB, Available: {available_space:.1f}GB"
                )
                return False

            # Download model with timeout
            logging.info(f"Downloading Ollama model: {model_name} ({required_space:.1f}GB)...")

            try:
                # Start download process
                process = subprocess.Popen(
                    ['ollama', 'pull', model_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                # Wait for completion with timeout (1 hour max)
                stdout, stderr = process.communicate(timeout=3600)

                if process.returncode == 0:
                    logging.info(f"Model {model_name} downloaded successfully")
                    return True
                else:
                    logging.error(f"Model download failed: {stderr}")
                    # Cleanup incomplete download
                    self._cleanup_incomplete_model(model_name)
                    return False

            except subprocess.TimeoutExpired:
                logging.error(f"Model download timed out after 1 hour: {model_name}")
                process.kill()
                process.communicate()
                # Cleanup incomplete download
                self._cleanup_incomplete_model(model_name)
                return False

        except Exception as e:
            logging.error(f"Error ensuring Ollama model availability: {str(e)}")
            # Try cleanup on any error
            self._cleanup_incomplete_model(model_name)
            return False

    def _cleanup_incomplete_model(self, model_name: str):
        """Clean up incomplete model download."""
        try:
            logging.info(f"Cleaning up incomplete download for {model_name}...")
            result = subprocess.run(
                ['ollama', 'rm', model_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                logging.info(f"Successfully cleaned up {model_name}")
            else:
                logging.debug(f"Model cleanup returned: {result.stderr}")
        except Exception as e:
            logging.debug(f"Could not cleanup model {model_name}: {str(e)}")

    def chat_completion(self, messages: List[Dict[str, str]], model: str = None,
                       temperature: float = 0.4, max_tokens: Optional[int] = None,
                       task_type: str = 'general') -> Optional[str]:
        """
        Send chat completion request to Ollama.

        Args:
            messages: List of messages with 'role' and 'content'
            model: Model to use (if None, will be selected based on task_type)
            temperature: Temperature for response randomness (default: 0.4)
            max_tokens: Maximum tokens in response
            task_type: Type of task to determine appropriate model

        Returns:
            Optional[str]: Response content or None if error
        """
        from unifierlib.constants import DEFAULT_MAX_TOKENS

        if model is None:
            model = self.get_model_for_task(task_type)

        if max_tokens is None:
            max_tokens = DEFAULT_MAX_TOKENS

        if not model:
            logging.error(f"No model available for task type: {task_type}")
            return None

        logging.debug(f"Ollama API call - Model: {model}, Temp: {temperature}, Max tokens: {max_tokens}")

        # Ensure model is available (auto-download if needed)
        if not self._ensure_model_available(model):
            logging.error(f"Model {model} not available")
            return None

        try:
            response = self.client.chat(
                model=model,
                messages=messages,
                options={
                    'temperature': temperature,
                    'num_predict': max_tokens,
                }
            )

            if response and 'message' in response:
                return response['message']['content'].strip()
            return None

        except Exception as e:
            logging.error(f"Ollama chat completion error: {str(e)}", exc_info=True)
            return None

    def json_completion(self, messages: List[Dict[str, str]], model: str = None,
                       temperature: float = 0.4, max_tokens: Optional[int] = None,
                       task_type: str = 'general') -> Optional[Dict[str, Any]]:
        """Send chat completion request expecting JSON response."""
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
            logging.error(f"Failed to parse JSON from Ollama response: {str(e)}")
            logging.error(f"Response was: {response_text}")
            return None

    def simple_completion(self, prompt: str, model: str = None,
                         temperature: float = 0.4, max_tokens: Optional[int] = None,
                         task_type: str = 'general') -> Optional[str]:
        """Send simple completion request with single prompt."""
        from unifierlib.constants import DEFAULT_MAX_TOKENS

        if max_tokens is None:
            max_tokens = DEFAULT_MAX_TOKENS

        messages = [
            {"role": "user", "content": prompt}
        ]

        return self.chat_completion(messages, model, temperature, max_tokens, task_type)

    def simple_json_completion(self, prompt: str, model: str = None,
                              temperature: float = 0.4, max_tokens: Optional[int] = None,
                              task_type: str = 'general') -> Optional[Dict[str, Any]]:
        """Send simple completion request expecting JSON response."""
        messages = [
            {"role": "user", "content": prompt}
        ]

        return self.json_completion(messages, model, temperature, max_tokens, task_type)

    def validate_api_key(self) -> bool:
        """Validate that Ollama is working."""
        try:
            response = self.simple_completion("Hello", model=self.models.get('tiny'), max_tokens=5)
            return response is not None
        except Exception as e:
            logging.error(f"Ollama validation failed: {str(e)}")
            return False

    def get_backend_info(self) -> Dict[str, Any]:
        """
        Get information about Ollama backend and available models.

        Returns:
            Dict with backend info, models, and storage details
        """
        info = {
            'backend': 'ollama',
            'backend_info': {
                'name': 'Ollama',
                'url': 'https://ollama.ai',
                'storage_path': self.storage_path
            },
            'available_models': self.models,
            'model_sizes_gb': self.model_sizes,
        }

        # Add Ollama-specific info
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                installed = [line.split()[0] for line in result.stdout.strip().split('\n')[1:]]
                info['installed_models'] = installed
        except Exception as e:
            logging.debug(f"Could not get installed models: {str(e)}")

        return info
