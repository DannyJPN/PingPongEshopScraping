"""
Generic xAI Grok client module for desaka_unifier project.

This module provides generic methods for communicating with xAI Grok API.
Contains only general methods that xAI Grok API supports.
Note: Grok API is OpenAI-compatible.
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional, List
from unifierlib.constants import DEFAULT_MAX_TOKENS, API_KEY_XAI


class GrokClient:
    """
    Generic client for xAI Grok API communication.
    Provides basic methods for chat completions and other xAI services.
    Note: Uses OpenAI-compatible API.
    """

    def __init__(self, use_fine_tuned_models: bool = False, fine_tuned_models: Optional[Dict[str, str]] = None):
        """Initialize xAI Grok client with API key from environment."""
        api_key = os.getenv(API_KEY_XAI)
        if not api_key:
            raise ValueError("XAI_API_KEY environment variable is not set")

        # Try to import openai (Grok uses OpenAI-compatible API)
        try:
            import openai
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.x.ai/v1",
                timeout=1200.0
            )
        except ImportError:
            logging.error("OpenAI library not installed. Install with: pip install openai")
            raise

        # Define latest available models
        self.models = {
            'flagship': 'grok-beta',  # Latest Grok model
            'efficient': 'grok-beta',  # Same model (no variations yet)
            'reasoning': 'grok-beta',  # Best for reasoning
            'creative': 'grok-beta',  # Best for creative tasks
        }

        # Fine-tuned model settings (not supported by xAI yet)
        self.use_fine_tuned_models = use_fine_tuned_models
        self.fine_tuned_models = fine_tuned_models or {}

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

        # All tasks use the same model for now
        return self.models['flagship']

    def chat_completion(self, messages: List[Dict[str, str]], model: str = None,
                       temperature: float = 0.4, max_tokens: Optional[int] = None,
                       task_type: str = 'general') -> Optional[str]:
        """
        Send chat completion request to xAI Grok.

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

        try:
            logging.debug(f"xAI Grok API call - Model: {model}, Temperature: {temperature}, Max tokens: {max_tokens}")
            logging.debug(f"xAI Grok API call - Messages: {len(messages)} messages")
            time.sleep(10)

            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            if response.choices and len(response.choices) > 0:
                response_content = response.choices[0].message.content.strip()
                logging.debug(f"xAI Grok API response received - Length: {len(response_content)} characters")
                return response_content
            else:
                logging.error("No response choices returned from xAI Grok")
                return None

        except Exception as e:
            logging.error(f"Error in xAI Grok chat completion: {str(e)}", exc_info=True)
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
            logging.error(f"Failed to parse JSON from xAI Grok response: {str(e)}")
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
        Validate that API key is working by making a simple request.

        Returns:
            bool: True if API key is valid, False otherwise
        """
        try:
            response = self.simple_completion("Hello", max_tokens=5)
            return response is not None
        except Exception as e:
            logging.error(f"API key validation failed: {str(e)}")
            return False

    def create_fine_tuning_job(self, training_file_id: str, model: str = None,
                              suffix: str = None, hyperparameters: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Create a fine-tuning job.

        Note: xAI Grok does not support fine-tuning yet.

        Args:
            training_file_id (str): ID of the uploaded training file
            model (str): Base model to fine-tune
            suffix (str): Suffix for the fine-tuned model name
            hyperparameters (Optional[Dict[str, Any]]): Training hyperparameters

        Returns:
            Optional[str]: Fine-tuning job ID or None if error
        """
        logging.warning("xAI Grok does not support fine-tuning yet")
        return None

    def upload_training_file(self, file_path: str) -> Optional[str]:
        """
        Upload a training file for fine-tuning.

        Note: xAI Grok does not support fine-tuning yet.

        Args:
            file_path (str): Path to the training file

        Returns:
            Optional[str]: File ID or None if error
        """
        logging.warning("xAI Grok does not support fine-tuning yet")
        return None

    def get_fine_tuning_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a fine-tuning job.

        Note: xAI Grok does not support fine-tuning yet.

        Args:
            job_id (str): Fine-tuning job ID

        Returns:
            Optional[Dict[str, Any]]: Job status information or None if error
        """
        logging.warning("xAI Grok does not support fine-tuning yet")
        return None
