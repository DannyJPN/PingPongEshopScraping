"""
Generic Mistral AI client module for desaka_unifier project.

This module provides generic methods for communicating with Mistral AI API.
Contains only general methods that Mistral API supports.
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional, List
from unifierlib.constants import DEFAULT_MAX_TOKENS


class MistralClient:
    """
    Generic client for Mistral AI API communication.
    Provides basic methods for chat completions and other Mistral services.
    """

    def __init__(self, use_fine_tuned_models: bool = False, fine_tuned_models: Optional[Dict[str, str]] = None):
        """Initialize Mistral client with API key from environment."""
        api_key = os.getenv('MISTRAL_API_KEY')
        if not api_key:
            raise ValueError("MISTRAL_API_KEY environment variable is not set")

        # Try to import mistralai
        try:
            from mistralai.client import MistralClient as MistralAPIClient
            self.client = MistralAPIClient(api_key=api_key)
        except ImportError:
            logging.error("Mistral AI library not installed. Install with: pip install mistralai")
            raise

        # Define latest available models
        self.models = {
            'flagship': 'mistral-large-latest',  # Latest large model
            'efficient': 'mistral-small-latest',  # Cost-efficient model
            'reasoning': 'mistral-large-latest',  # Best for reasoning
            'creative': 'mistral-large-latest',  # Best for creative tasks
            'nemo': 'open-mistral-nemo'  # Open source model
        }

        # Fine-tuned model settings
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

        task_model_mapping = {
            'general': self.models['efficient'],
            'complex': self.models['flagship'],
            'simple': self.models['efficient'],
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
        Send chat completion request to Mistral AI.

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
            from mistralai.models.chat_completion import ChatMessage

            # Convert messages to Mistral format
            mistral_messages = []
            for msg in messages:
                mistral_messages.append(
                    ChatMessage(role=msg['role'], content=msg['content'])
                )

            logging.debug(f"Mistral AI API call - Model: {model}, Temperature: {temperature}, Max tokens: {max_tokens}")
            logging.debug(f"Mistral AI API call - Messages: {len(mistral_messages)} messages")
            time.sleep(10)

            response = self.client.chat(
                model=model,
                messages=mistral_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            if response.choices and len(response.choices) > 0:
                response_content = response.choices[0].message.content.strip()
                logging.debug(f"Mistral AI API response received - Length: {len(response_content)} characters")
                return response_content
            else:
                logging.error("No response choices returned from Mistral AI")
                return None

        except Exception as e:
            logging.error(f"Error in Mistral AI chat completion: {str(e)}", exc_info=True)
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
            logging.error(f"Failed to parse JSON from Mistral AI response: {str(e)}")
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

        Args:
            training_file_id (str): ID of the uploaded training file
            model (str): Base model to fine-tune
            suffix (str): Suffix for the fine-tuned model name
            hyperparameters (Optional[Dict[str, Any]]): Training hyperparameters

        Returns:
            Optional[str]: Fine-tuning job ID or None if error
        """
        try:
            from mistralai.models.jobs import TrainingParameters

            training_params = TrainingParameters(
                training_steps=10,
                learning_rate=0.0001
            )

            if hyperparameters:
                if 'training_steps' in hyperparameters:
                    training_params.training_steps = hyperparameters['training_steps']
                if 'learning_rate' in hyperparameters:
                    training_params.learning_rate = hyperparameters['learning_rate']

            job = self.client.jobs.create(
                model=model or self.models['efficient'],
                training_files=[training_file_id],
                hyperparameters=training_params,
                suffix=suffix
            )

            return job.id

        except Exception as e:
            logging.error(f"Error creating fine-tuning job: {str(e)}", exc_info=True)
            return None

    def upload_training_file(self, file_path: str) -> Optional[str]:
        """
        Upload a training file for fine-tuning.

        Args:
            file_path (str): Path to the training file

        Returns:
            Optional[str]: File ID or None if error
        """
        try:
            with open(file_path, 'rb') as f:
                file_response = self.client.files.create(
                    file=f,
                    purpose='fine-tune'
                )

            return file_response.id

        except Exception as e:
            logging.error(f"Error uploading training file: {str(e)}", exc_info=True)
            return None

    def get_fine_tuning_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a fine-tuning job.

        Args:
            job_id (str): Fine-tuning job ID

        Returns:
            Optional[Dict[str, Any]]: Job status information or None if error
        """
        try:
            job = self.client.jobs.retrieve(job_id)

            return {
                'id': job.id,
                'status': job.status,
                'model': job.model,
                'fine_tuned_model': job.fine_tuned_model if hasattr(job, 'fine_tuned_model') else None,
                'created_at': job.created_at,
                'finished_at': job.finished_at if hasattr(job, 'finished_at') else None
            }

        except Exception as e:
            logging.error(f"Error getting fine-tuning job status: {str(e)}", exc_info=True)
            return None
