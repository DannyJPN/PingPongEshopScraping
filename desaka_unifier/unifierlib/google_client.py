"""
Generic Google Gemini client module for desaka_unifier project.

This module provides generic methods for communicating with Google Gemini API.
Contains only general methods that Google Gemini API supports.
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional, List
from unifierlib.constants import DEFAULT_MAX_TOKENS


class GoogleClient:
    """
    Generic client for Google Gemini API communication.
    Provides basic methods for chat completions and other Google services.
    """

    def __init__(self, use_fine_tuned_models: bool = False, fine_tuned_models: Optional[Dict[str, str]] = None):
        """Initialize Google Gemini client with API key from environment."""
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")

        # Try to import google.generativeai
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.genai = genai
        except ImportError:
            logging.error("Google Generative AI library not installed. Install with: pip install google-generativeai")
            raise

        # Define latest available models
        self.models = {
            'flagship': 'gemini-1.5-pro',  # Flagship model with long context
            'efficient': 'gemini-2.0-flash-exp',  # Ultra-efficient latest model
            'reasoning': 'gemini-1.5-pro',  # Best for reasoning
            'creative': 'gemini-1.5-pro',  # Best for creative tasks
            'flash': 'gemini-1.5-flash'  # Fast and efficient
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
        Send chat completion request to Google Gemini.

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
            # Convert messages to Gemini format
            # Gemini uses 'user' and 'model' roles, and system instructions separately
            system_instruction = None
            chat_history = []
            user_message = None

            for msg in messages:
                if msg['role'] == 'system':
                    system_instruction = msg['content']
                elif msg['role'] == 'user':
                    user_message = msg['content']
                elif msg['role'] == 'assistant':
                    # Gemini calls it 'model' not 'assistant'
                    chat_history.append({'role': 'model', 'parts': [msg['content']]})

            logging.debug(f"Google Gemini API call - Model: {model}, Temperature: {temperature}, Max tokens: {max_tokens}")
            time.sleep(10)

            # Configure generation
            generation_config = {
                'temperature': temperature,
                'max_output_tokens': max_tokens,
            }

            # Create model
            gemini_model = self.genai.GenerativeModel(
                model_name=model,
                generation_config=generation_config,
                system_instruction=system_instruction
            )

            # Generate response
            if chat_history:
                chat = gemini_model.start_chat(history=chat_history)
                response = chat.send_message(user_message)
            else:
                response = gemini_model.generate_content(user_message)

            if response and response.text:
                response_content = response.text.strip()
                logging.debug(f"Google Gemini API response received - Length: {len(response_content)} characters")
                return response_content
            else:
                logging.error("No response text returned from Google Gemini")
                return None

        except Exception as e:
            logging.error(f"Error in Google Gemini chat completion: {str(e)}", exc_info=True)
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
            logging.error(f"Failed to parse JSON from Google Gemini response: {str(e)}")
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

        Note: Google Gemini fine-tuning is done through AI Studio, not this API.

        Args:
            training_file_id (str): ID of the uploaded training file
            model (str): Base model to fine-tune
            suffix (str): Suffix for the fine-tuned model name
            hyperparameters (Optional[Dict[str, Any]]): Training hyperparameters

        Returns:
            Optional[str]: Fine-tuning job ID or None if error
        """
        logging.warning("Google Gemini fine-tuning is done through AI Studio, not via this API")
        return None

    def upload_training_file(self, file_path: str) -> Optional[str]:
        """
        Upload a training file for fine-tuning.

        Note: Google Gemini fine-tuning is done through AI Studio, not this API.

        Args:
            file_path (str): Path to the training file

        Returns:
            Optional[str]: File ID or None if error
        """
        logging.warning("Google Gemini fine-tuning is done through AI Studio, not via this API")
        return None

    def get_fine_tuning_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a fine-tuning job.

        Note: Google Gemini fine-tuning is done through AI Studio, not this API.

        Args:
            job_id (str): Fine-tuning job ID

        Returns:
            Optional[Dict[str, Any]]: Job status information or None if error
        """
        logging.warning("Google Gemini fine-tuning is done through AI Studio, not via this API")
        return None
