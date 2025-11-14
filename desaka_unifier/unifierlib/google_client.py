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
from unifierlib.constants import DEFAULT_MAX_TOKENS, API_KEY_GOOGLE


class GoogleClient:
    """
    Generic client for Google Gemini API communication.
    Provides basic methods for chat completions and other Google services.
    """

    def __init__(self, use_fine_tuned_models: bool = False, fine_tuned_models: Optional[Dict[str, str]] = None):
        """Initialize Google Gemini client with API key from environment."""
        api_key = os.getenv(API_KEY_GOOGLE)
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
        Create a fine-tuning job using Google Gemini Tuning API.

        Args:
            training_file_id (str): Training data (JSONL content, not file ID)
            model (str): Base model to fine-tune (default: gemini-1.5-flash-001-tuning)
            suffix (str): Suffix for the fine-tuned model name (display_name)
            hyperparameters (Optional[Dict[str, Any]]): Training hyperparameters

        Returns:
            Optional[str]: Tuned model name or None if error
        """
        try:
            # Google Gemini uses tuned models API
            base_model = model or 'models/gemini-1.5-flash-001-tuning'

            # Load training data from file (training_file_id is actually file path)
            import json
            training_examples = []
            with open(training_file_id, 'r', encoding='utf-8') as f:
                for line in f:
                    example = json.loads(line)
                    # Convert OpenAI format to Google format
                    if 'messages' in example:
                        text_input = ""
                        output = ""
                        for msg in example['messages']:
                            if msg['role'] == 'user':
                                text_input += msg['content']
                            elif msg['role'] == 'assistant':
                                output = msg['content']

                        training_examples.append({
                            'text_input': text_input,
                            'output': output
                        })

            # Create tuning job
            display_name = suffix or f"tuned_model_{int(time.time())}"

            # Build tuning config
            tuning_config = {
                'epoch_count': hyperparameters.get('epochs', 5) if hyperparameters else 5,
                'batch_size': hyperparameters.get('batch_size', 4) if hyperparameters else 4,
                'learning_rate': hyperparameters.get('learning_rate', 0.001) if hyperparameters else 0.001,
            }

            operation = self.genai.create_tuned_model(
                source_model=base_model,
                training_data=training_examples,
                id=display_name,
                epoch_count=tuning_config['epoch_count'],
                batch_size=tuning_config['batch_size'],
                learning_rate=tuning_config['learning_rate'],
                display_name=display_name
            )

            logging.info(f"Started Google Gemini tuning job: {display_name}")
            return display_name

        except Exception as e:
            logging.error(f"Error creating Google Gemini tuning job: {str(e)}", exc_info=True)
            logging.warning("Note: Google Gemini fine-tuning requires specific model access and permissions")
            return None

    def upload_training_file(self, file_path: str) -> Optional[str]:
        """
        Prepare training file for Google Gemini tuning.

        Note: Google Gemini doesn't require separate file upload.
        Training data is passed directly to create_tuned_model.
        This method returns the file path to be used in create_fine_tuning_job.

        Args:
            file_path (str): Path to the training file (JSONL format)

        Returns:
            Optional[str]: File path (not uploaded, just validated) or None if error
        """
        try:
            # Validate file exists and is readable
            if not os.path.exists(file_path):
                logging.error(f"Training file not found: {file_path}")
                return None

            # Validate JSONL format
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                line_count = 0
                for line in f:
                    json.loads(line)  # Validate JSON
                    line_count += 1

                if line_count == 0:
                    logging.error("Training file is empty")
                    return None

            logging.info(f"Validated training file: {file_path} ({line_count} examples)")
            return file_path  # Return path, not ID

        except Exception as e:
            logging.error(f"Error validating training file: {str(e)}", exc_info=True)
            return None

    def get_fine_tuning_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a Google Gemini tuning job.

        Args:
            job_id (str): Tuned model name/ID

        Returns:
            Optional[Dict[str, Any]]: Job status information or None if error
        """
        try:
            # Get tuned model info
            tuned_model = self.genai.get_tuned_model(f"tunedModels/{job_id}")

            # Map Google state to OpenAI-like status
            state_mapping = {
                'CREATING': 'running',
                'ACTIVE': 'succeeded',
                'FAILED': 'failed',
            }

            status = state_mapping.get(tuned_model.state, 'unknown')

            result = {
                'id': job_id,
                'status': status,
                'model': tuned_model.base_model if hasattr(tuned_model, 'base_model') else None,
                'fine_tuned_model': f"tunedModels/{job_id}" if status == 'succeeded' else None,
                'state': tuned_model.state,
                'created_at': tuned_model.create_time if hasattr(tuned_model, 'create_time') else None,
                'finished_at': tuned_model.update_time if hasattr(tuned_model, 'update_time') and status != 'running' else None
            }

            logging.info(f"Google Gemini tuning job {job_id} status: {status}")
            return result

        except Exception as e:
            logging.error(f"Error getting Google Gemini tuning job status: {str(e)}", exc_info=True)
            return None
