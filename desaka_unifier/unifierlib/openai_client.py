"""
Generic OpenAI client module for desaka_unifier project.

This module provides generic methods for communicating with OpenAI API.
Contains only general methods that OpenAI API supports.
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional, List
from unifierlib.constants import DEFAULT_MAX_TOKENS, API_KEY_OPENAI


class OpenAIClient:
    """
    Generic client for OpenAI API communication.
    Provides basic methods for chat completions and other OpenAI services.
    """
    
    def __init__(self, use_fine_tuned_models: bool = False, fine_tuned_models: Optional[Dict[str, str]] = None):
        """Initialize OpenAI client with API key from environment."""
        api_key = os.getenv(API_KEY_OPENAI)
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        # Try to import openai
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key,timeout=1200.0)
        except ImportError:
            logging.error("OpenAI library not installed. Install with: pip install openai")
            raise

        # Define latest available models
        self.models = {
            'flagship': 'gpt-4o',  # Latest flagship model for complex tasks
            'efficient': 'gpt-4o-mini',  # Cost-efficient model for simpler tasks
            'reasoning': 'gpt-4o',  # Best for reasoning and analysis
            'creative': 'gpt-4o',  # Best for creative tasks
            'fine_tuning': 'gpt-4o-mini'  # Model for fine-tuning
        }

        # Fine-tuned model settings
        self.use_fine_tuned_models = use_fine_tuned_models
        self.fine_tuned_models = fine_tuned_models or {}

    def get_model_for_task(self, task_type: str = 'general') -> str:
        """
        Get the appropriate model for a specific task type.

        Args:
            task_type (str): Type of task ('general', 'complex', 'simple', 'reasoning', 'creative', 'fine_tuning')

        Returns:
            str: Model name to use
        """
        # Check if we should use fine-tuned models and if one exists for this task
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
            'fine_tuning': self.models['fine_tuning'],
            'category_mapping': self.models['flagship'],
            'product_analysis': self.models['flagship'],  # Complex analysis
            'text_generation': self.models['flagship'],  # Simple text tasks
            'translation': self.models['flagship'],  # Translation tasks
            'name_generation': self.models['flagship'],  # Product name generation
            'description_translation': self.models['flagship'],  # Description translation
            'brand_detection': self.models['efficient'],  # Brand detection
            'type_detection': self.models['efficient'],  # Type detection
            'model_detection': self.models['efficient'],  # Model detection
            'keyword_generation': self.models['efficient']  # Keyword generation
        }

        return task_model_mapping.get(task_type, self.models['efficient'])

    def chat_completion(self, messages: List[Dict[str, str]], model: str = None,
                       temperature: float = 0.4, max_tokens: Optional[int] = None,
                       task_type: str = 'general') -> Optional[str]:
        """
        Send chat completion request to OpenAI.

        Args:
            messages (List[Dict[str, str]]): List of messages with 'role' and 'content'
            model (str): Model to use (if None, will be selected based on task_type)
            temperature (float): Temperature for response randomness (default: 0.1)
            max_tokens (Optional[int]): Maximum tokens in response
            task_type (str): Type of task to determine appropriate model

        Returns:
            Optional[str]: Response content or None if error
        """
        # Select model if not provided
        if model is None:
            model = self.get_model_for_task(task_type)

        # Ensure max_tokens is always a number, never None
        if max_tokens is None:
            max_tokens = DEFAULT_MAX_TOKENS

        try:
            logging.debug(f"OpenAI API call - Model: {model}, Temperature: {temperature}, Max tokens: {max_tokens}")
            logging.debug(f"OpenAI API call - Messages: {len(messages)} messages")
            time.sleep(10)
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            if response.choices and len(response.choices) > 0:
                response_content = response.choices[0].message.content.strip()
                logging.debug(f"OpenAI API response received - Length: {len(response_content)} characters")
                return response_content
            else:
                logging.error("No response choices returned from OpenAI")
                return None

        except Exception as e:
            logging.error(f"Error in OpenAI chat completion: {str(e)}", exc_info=True)
            return None
    
    def json_completion(self, messages: List[Dict[str, str]], model: str = None,
                       temperature: float = 0.4, max_tokens: Optional[int] = None,
                       task_type: str = 'general') -> Optional[Dict[str, Any]]:
        """
        Send chat completion request expecting JSON response.

        Args:
            messages (List[Dict[str, str]]): List of messages with 'role' and 'content'
            model (str): Model to use (if None, will be selected based on task_type)
            temperature (float): Temperature for response randomness (default: 0.1)
            max_tokens (Optional[int]): Maximum tokens in response
            task_type (str): Type of task to determine appropriate model

        Returns:
            Optional[Dict[str, Any]]: Parsed JSON response or None if error
        """
        # Add JSON format instruction to the last message
        if messages and len(messages) > 0:
            last_message = messages[-1]
            if last_message.get('role') == 'user':
                last_message['content'] += "\n\nPlease return your response as valid JSON only, no additional text."

        response_text = self.chat_completion(messages, model, temperature, max_tokens, task_type)

        if not response_text:
            return None

        try:
            # Try to parse JSON from response
            # Sometimes OpenAI wraps JSON in markdown code blocks
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()

            return json.loads(response_text)

        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON from OpenAI response: {str(e)}")
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
            temperature (float): Temperature for response randomness (default: 0.1)
            max_tokens (Optional[int]): Maximum tokens in response
            task_type (str): Type of task to determine appropriate model

        Returns:
            Optional[str]: Response content or None if error
        """
        # Ensure max_tokens is always a number, never None
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
            temperature (float): Temperature for response randomness (default: 0.1)
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
            model (str): Base model to fine-tune (if None, uses fine_tuning model)
            suffix (str): Suffix for the fine-tuned model name
            hyperparameters (Optional[Dict[str, Any]]): Training hyperparameters

        Returns:
            Optional[str]: Fine-tuning job ID or None if error
        """
        if model is None:
            model = self.models['fine_tuning']

        try:
            job_params = {
                "training_file": training_file_id,
                "model": model
            }

            if suffix:
                job_params["suffix"] = suffix

            if hyperparameters:
                job_params["hyperparameters"] = hyperparameters

            response = self.client.fine_tuning.jobs.create(**job_params)
            return response.id

        except Exception as e:
            logging.error(f"Error creating fine-tuning job: {str(e)}", exc_info=True)
            return None

    def upload_training_file(self, file_path: str) -> Optional[str]:
        """
        Upload a training file for fine-tuning.

        Args:
            file_path (str): Path to the training file (JSONL format)

        Returns:
            Optional[str]: File ID or None if error
        """
        try:
            with open(file_path, 'rb') as file:
                response = self.client.files.create(
                    file=file,
                    purpose='fine-tune'
                )
            return response.id

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
            response = self.client.fine_tuning.jobs.retrieve(job_id)
            return {
                'id': response.id,
                'status': response.status,
                'model': response.model,
                'fine_tuned_model': response.fine_tuned_model,
                'created_at': response.created_at,
                'finished_at': response.finished_at,
                'error': response.error
            }

        except Exception as e:
            logging.error(f"Error getting fine-tuning job status: {str(e)}", exc_info=True)
            return None
