"""
Generic Local Multimodal Models client module for desaka_unifier project.

This module provides generic methods for communicating with local MULTIMODAL LLM models
(text + vision) via multiple backends: Ollama, LM Studio, and Hugging Face.
Includes automatic backend detection, model download, and management.

IMPORTANT: This module uses ONLY multimodal models capable of processing both text and images.
This enables product image analysis, OCR, visual product detection, and image-based categorization
for e-commerce applications.

Supported multimodal models:
- LLaVA (Large Language and Vision Assistant) - Popular vision model
- Qwen2-VL - Multimodal version of Qwen with vision capabilities
- MiniCPM-V - Efficient Chinese multimodal model
- Moondream - Small efficient vision model
"""

import os
import json
import logging
import subprocess
import shutil
from enum import Enum
from typing import Dict, Any, Optional, List
from unifierlib.constants import DEFAULT_MAX_TOKENS, API_KEY_HUGGINGFACE, API_KEY_HUGGINGFACE_ALT


class LocalBackend(Enum):
    """Supported local model backends."""
    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"
    HUGGINGFACE_LOCAL = "huggingface_local"
    HUGGINGFACE_API = "huggingface_api"


class LocalClient:
    """
    Generic client for local MULTIMODAL LLM models with multi-backend support.

    MULTIMODAL ONLY: This client exclusively uses multimodal models (text + vision)
    for e-commerce product analysis, including image recognition, OCR, and visual categorization.

    Supported backends:
    - Ollama: LLaVA, Qwen2-VL, MiniCPM-V, Moondream
    - LM Studio: Any loaded multimodal model (auto-detected)
    - Hugging Face (local & API): LLaVA, Qwen2-VL, MiniCPM-V, Moondream

    Features:
    - Automatic backend detection and initialization
    - Automatic model download (Ollama)
    - Disk space verification before download
    - Multimodal model filtering (LM Studio)
    - Lazy model loading (Hugging Face)
    """

    def __init__(self, use_fine_tuned_models: bool = False, fine_tuned_models: Optional[Dict[str, str]] = None,
                 model_storage_path: str = None, preferred_backend: Optional[str] = None):
        """
        Initialize Local client with automatic backend detection.

        Args:
            use_fine_tuned_models: Whether to use fine-tuned models
            fine_tuned_models: Dict of fine-tuned model mappings
            model_storage_path: Path for model storage (backend-specific)
            preferred_backend: Force specific backend ('ollama', 'lm_studio', 'huggingface')
        """
        # Get model storage paths from constants
        if model_storage_path is None:
            from unifierlib.constants import (
                LOCAL_MODEL_STORAGE_PATH_OLLAMA,
                LOCAL_MODEL_STORAGE_PATH_LMSTUDIO,
                LOCAL_MODEL_STORAGE_PATH_HUGGINGFACE
            )
            self.storage_paths = {
                'ollama': LOCAL_MODEL_STORAGE_PATH_OLLAMA,
                'lm_studio': LOCAL_MODEL_STORAGE_PATH_LMSTUDIO,
                'huggingface': LOCAL_MODEL_STORAGE_PATH_HUGGINGFACE
            }
        else:
            self.storage_paths = {
                'ollama': model_storage_path,
                'lm_studio': model_storage_path,
                'huggingface': model_storage_path
            }

        # Fine-tuned model settings
        self.use_fine_tuned_models = use_fine_tuned_models
        self.fine_tuned_models = fine_tuned_models or {}

        # Backend and client initialization
        self.backend = None
        self.client = None
        self.backend_info = {}

        # Detect and initialize backend
        if preferred_backend:
            logging.info(f"Attempting to use preferred backend: {preferred_backend}")
            if not self._init_backend(preferred_backend):
                raise RuntimeError(f"Preferred backend '{preferred_backend}' is not available")
        else:
            logging.info("Auto-detecting available local multimodal model backend...")
            if not self._auto_detect_backend():
                raise RuntimeError(
                    "No local multimodal model backend available. Please install one of:\n"
                    "- Ollama: https://ollama.ai/download (then: ollama pull llava:13b)\n"
                    "- LM Studio: https://lmstudio.ai (load a multimodal model like LLaVA or Qwen2-VL)\n"
                    "- Hugging Face: pip install transformers torch (supports LLaVA, Qwen2-VL, MiniCPM-V, Moondream)\n"
                    "\n"
                    "IMPORTANT: Only multimodal (text + vision) models are supported for product image analysis."
                )

        logging.info(f"Using multimodal backend: {self.backend.value}")
        logging.info(f"Backend info: {self.backend_info}")

        # Define available models based on backend
        self._init_model_catalog()

    def _auto_detect_backend(self) -> bool:
        """
        Auto-detect available backend in order of preference.

        Returns:
            bool: True if a backend was found and initialized
        """
        # Try backends in order of preference
        backends_to_try = [
            'ollama',      # Fastest, best UX
            'lm_studio',   # Good UX, OpenAI-compatible
            'huggingface'  # Most flexible, but slower
        ]

        for backend_name in backends_to_try:
            if self._init_backend(backend_name):
                return True

        return False

    def _init_backend(self, backend_name: str) -> bool:
        """
        Initialize specific backend.

        Args:
            backend_name: Name of backend to initialize

        Returns:
            bool: True if initialization successful
        """
        try:
            if backend_name == 'ollama':
                return self._init_ollama()
            elif backend_name == 'lm_studio':
                return self._init_lm_studio()
            elif backend_name == 'huggingface':
                return self._init_huggingface()
            else:
                logging.error(f"Unknown backend: {backend_name}")
                return False
        except Exception as e:
            logging.debug(f"Failed to initialize {backend_name}: {str(e)}")
            return False

    def _init_ollama(self) -> bool:
        """Initialize Ollama backend."""
        # Check if Ollama is installed
        if not shutil.which('ollama'):
            logging.debug("Ollama not installed")
            return False

        # Check if Ollama service is running
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                logging.debug("Ollama service not running")
                return False
        except Exception as e:
            logging.debug(f"Ollama check failed: {str(e)}")
            return False

        # Try to import ollama library
        try:
            import ollama
            self.client = ollama.Client()
            self.backend = LocalBackend.OLLAMA
            self.backend_info = {
                'name': 'Ollama',
                'url': 'https://ollama.ai',
                'storage_path': self.storage_paths['ollama']
            }
            return True
        except ImportError:
            logging.debug("Ollama Python library not installed")
            return False

    def _init_lm_studio(self) -> bool:
        """Initialize LM Studio backend (OpenAI-compatible API)."""
        try:
            import openai

            # Test if LM Studio server is running (default port 1234)
            test_client = openai.OpenAI(
                base_url="http://localhost:1234/v1",
                api_key="lm-studio",  # LM Studio doesn't require real API key
                timeout=5.0
            )

            # Try to list models to verify server is running
            try:
                models = test_client.models.list()
                if not models.data:
                    logging.debug("LM Studio server running but no models loaded")
                    return False
            except Exception as e:
                logging.debug(f"LM Studio server not responding: {str(e)}")
                return False

            self.client = test_client
            self.backend = LocalBackend.LM_STUDIO
            self.backend_info = {
                'name': 'LM Studio',
                'url': 'http://localhost:1234',
                'storage_path': self.storage_paths['lm_studio']
            }
            return True

        except ImportError:
            logging.debug("OpenAI library not installed (required for LM Studio)")
            return False
        except Exception as e:
            logging.debug(f"LM Studio initialization failed: {str(e)}")
            return False

    def _init_huggingface(self) -> bool:
        """Initialize Hugging Face backend (local transformers)."""
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

            # Check if CUDA is available
            device = "cuda" if torch.cuda.is_available() else "cpu"

            self.client = {
                'AutoModelForCausalLM': AutoModelForCausalLM,
                'AutoTokenizer': AutoTokenizer,
                'pipeline': pipeline,
                'device': device,
                'loaded_model': None,
                'loaded_tokenizer': None,
                'current_model_name': None
            }

            self.backend = LocalBackend.HUGGINGFACE_LOCAL
            self.backend_info = {
                'name': 'Hugging Face (Local)',
                'device': device,
                'storage_path': self.storage_paths['huggingface']
            }

            logging.info(f"Hugging Face backend initialized (device: {device})")
            return True

        except ImportError as e:
            logging.debug(f"Hugging Face libraries not installed: {str(e)}")

            # Try Hugging Face Inference API as fallback
            hf_token = os.getenv(API_KEY_HUGGINGFACE) or os.getenv(API_KEY_HUGGINGFACE_ALT)
            if hf_token:
                try:
                    import requests
                    self.client = {
                        'api_token': hf_token,
                        'api_url': 'https://api-inference.huggingface.co/models/'
                    }
                    self.backend = LocalBackend.HUGGINGFACE_API
                    self.backend_info = {
                        'name': 'Hugging Face (API)',
                        'url': 'https://huggingface.co'
                    }
                    logging.info("Using Hugging Face Inference API")
                    return True
                except ImportError:
                    logging.debug("requests library not installed")
                    return False

            return False

    def _init_model_catalog(self):
        """Initialize model catalog based on backend - MULTIMODAL MODELS ONLY (text + vision)."""
        if self.backend == LocalBackend.OLLAMA:
            # Ollama - multimodal vision models for product image analysis
            self.models = {
                'flagship': 'llava:34b',           # Best multimodal model
                'efficient': 'llava:13b',          # Good balance for vision tasks
                'reasoning': 'llava:34b',          # Complex vision reasoning
                'creative': 'llava:34b',           # Creative image analysis
                'tiny': 'moondream',               # Smallest efficient vision model (~1.6B params)
                'medium': 'minicpm-v:8b',          # Medium-sized multimodal (MiniCPM-V)
                'vision_flagship': 'qwen2-vl:72b', # Qwen2-VL flagship for complex vision
                'vision_efficient': 'qwen2-vl:7b', # Qwen2-VL efficient
                'vision_tiny': 'llava:7b',         # LLaVA small
            }
            self.model_sizes = {
                'moondream': 1.6,           # ~1.6GB - very efficient
                'llava:7b': 4.5,           # ~4.5GB
                'qwen2-vl:7b': 4.7,        # ~4.7GB
                'minicpm-v:8b': 5.2,       # ~5.2GB
                'llava:13b': 7.3,          # ~7.3GB
                'llava:34b': 19.0,         # ~19GB
                'qwen2-vl:72b': 43.0,      # ~43GB
            }

        elif self.backend == LocalBackend.LM_STUDIO:
            # LM Studio - get available multimodal models from server
            try:
                models_list = self.client.models.list()
                available = [m.id for m in models_list.data]

                # Filter for multimodal models (llava, vision, vl, minicpm-v, moondream, qwen-vl)
                multimodal_keywords = ['llava', 'vision', '-vl', 'minicpm-v', 'moondream', 'qwen-vl', 'qwen2-vl']
                multimodal_models = [
                    m for m in available
                    if any(keyword in m.lower() for keyword in multimodal_keywords)
                ]

                # Use first available multimodal model as default for all tasks
                default_model = multimodal_models[0] if multimodal_models else (available[0] if available else None)

                if not multimodal_models and available:
                    logging.warning(f"No multimodal models detected in LM Studio. Available: {available}")
                    logging.warning("Please load a multimodal model (LLaVA, Qwen2-VL, MiniCPM-V, Moondream)")

                self.models = {
                    'flagship': default_model,
                    'efficient': default_model,
                    'reasoning': default_model,
                    'creative': default_model,
                    'tiny': default_model,
                    'medium': default_model,
                }
                self.model_sizes = {}  # LM Studio manages models externally

                logging.info(f"LM Studio multimodal models: {multimodal_models if multimodal_models else 'none'}")
                logging.info(f"LM Studio using model: {default_model}")

            except Exception as e:
                logging.error(f"Failed to get LM Studio models: {str(e)}")
                self.models = {}
                self.model_sizes = {}

        elif self.backend == LocalBackend.HUGGINGFACE_LOCAL:
            # Hugging Face local - multimodal vision models (Czech-friendly)
            self.models = {
                'flagship': 'Qwen/Qwen2-VL-72B-Instruct',          # Best multimodal
                'efficient': 'Qwen/Qwen2-VL-7B-Instruct',          # Efficient vision
                'reasoning': 'Qwen/Qwen2-VL-72B-Instruct',         # Complex reasoning
                'creative': 'liuhaotian/llava-v1.6-vicuna-13b',    # Creative LLaVA
                'tiny': 'openbmb/MiniCPM-V-2_6',                   # Tiny but powerful (~8B)
                'medium': 'liuhaotian/llava-v1.6-vicuna-13b',      # Medium LLaVA
                'vision_tiny': 'vikhyatk/moondream2',              # Moondream 2 (~1.6B)
                'vision_efficient': 'Qwen/Qwen2-VL-7B-Instruct',   # Qwen2-VL small
                'vision_flagship': 'Qwen/Qwen2-VL-72B-Instruct',   # Qwen2-VL large
            }
            self.model_sizes = {
                'vikhyatk/moondream2': 3.5,                       # ~3.5GB with weights
                'openbmb/MiniCPM-V-2_6': 18.0,                    # ~18GB (8B params)
                'Qwen/Qwen2-VL-7B-Instruct': 16.0,                # ~16GB
                'liuhaotian/llava-v1.6-vicuna-13b': 28.0,         # ~28GB
                'Qwen/Qwen2-VL-72B-Instruct': 150.0,              # ~150GB
            }

        elif self.backend == LocalBackend.HUGGINGFACE_API:
            # Hugging Face API - multimodal models via inference API
            self.models = {
                'flagship': 'Qwen/Qwen2-VL-72B-Instruct',          # Best via API
                'efficient': 'Qwen/Qwen2-VL-7B-Instruct',          # Faster multimodal
                'reasoning': 'Qwen/Qwen2-VL-72B-Instruct',         # Complex tasks
                'creative': 'liuhaotian/llava-v1.6-vicuna-13b',    # Creative vision
                'tiny': 'openbmb/MiniCPM-V-2_6',                   # Small efficient
                'medium': 'liuhaotian/llava-v1.6-vicuna-13b',      # Medium size
                'vision_tiny': 'vikhyatk/moondream2',              # Moondream API
                'vision_efficient': 'Qwen/Qwen2-VL-7B-Instruct',   # Qwen2-VL API
            }
            self.model_sizes = {}  # API doesn't download models

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
            'keyword_generation': self.models.get('efficient')
        }

        return task_model_mapping.get(task_type, self.models.get('efficient'))

    def _chat_completion_ollama(self, messages: List[Dict[str, str]], model: str,
                                temperature: float, max_tokens: int) -> Optional[str]:
        """Chat completion using Ollama backend."""
        # Ensure model is available (auto-download if needed)
        if not self._ensure_model_available_ollama(model):
            logging.error(f"Model {model} not available via Ollama")
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

    def _chat_completion_lm_studio(self, messages: List[Dict[str, str]], model: str,
                                   temperature: float, max_tokens: int) -> Optional[str]:
        """Chat completion using LM Studio backend (OpenAI-compatible)."""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content.strip()
            return None

        except Exception as e:
            logging.error(f"LM Studio chat completion error: {str(e)}", exc_info=True)
            return None

    def _chat_completion_huggingface_local(self, messages: List[Dict[str, str]], model: str,
                                           temperature: float, max_tokens: int) -> Optional[str]:
        """Chat completion using local Hugging Face transformers."""
        try:
            # Load model if not already loaded or if different model requested
            if (self.client['loaded_model'] is None or
                self.client['current_model_name'] != model):

                logging.info(f"Loading Hugging Face model: {model}")

                tokenizer = self.client['AutoTokenizer'].from_pretrained(
                    model,
                    cache_dir=self.storage_paths['huggingface']
                )

                model_obj = self.client['AutoModelForCausalLM'].from_pretrained(
                    model,
                    cache_dir=self.storage_paths['huggingface'],
                    device_map="auto" if self.client['device'] == "cuda" else None,
                    torch_dtype="auto"
                )

                self.client['loaded_model'] = model_obj
                self.client['loaded_tokenizer'] = tokenizer
                self.client['current_model_name'] = model

                logging.info(f"Model {model} loaded successfully")

            # Format messages for model
            tokenizer = self.client['loaded_tokenizer']
            model_obj = self.client['loaded_model']

            # Convert messages to prompt format
            prompt = self._format_messages_for_hf(messages, tokenizer)

            # Generate response
            inputs = tokenizer(prompt, return_tensors="pt")
            if self.client['device'] == "cuda":
                inputs = inputs.to("cuda")

            outputs = model_obj.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                pad_token_id=tokenizer.eos_token_id
            )

            response = tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Extract only the new generated text (after the prompt)
            response = response[len(prompt):].strip()

            return response

        except Exception as e:
            logging.error(f"Hugging Face local completion error: {str(e)}", exc_info=True)
            return None

    def _chat_completion_huggingface_api(self, messages: List[Dict[str, str]], model: str,
                                         temperature: float, max_tokens: int) -> Optional[str]:
        """Chat completion using Hugging Face Inference API."""
        try:
            import requests

            api_url = self.client['api_url'] + model
            headers = {"Authorization": f"Bearer {self.client['api_token']}"}

            # Format messages into prompt
            prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])

            payload = {
                "inputs": prompt,
                "parameters": {
                    "temperature": temperature,
                    "max_new_tokens": max_tokens,
                    "return_full_text": False
                }
            }

            response = requests.post(api_url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()

            result = response.json()

            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', '').strip()
            elif isinstance(result, dict):
                return result.get('generated_text', '').strip()

            return None

        except Exception as e:
            logging.error(f"Hugging Face API completion error: {str(e)}", exc_info=True)
            return None

    def _format_messages_for_hf(self, messages: List[Dict[str, str]], tokenizer) -> str:
        """Format messages for Hugging Face models using chat template."""
        try:
            # Try to use chat template if available
            if hasattr(tokenizer, 'apply_chat_template'):
                return tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True
                )
        except Exception as e:
            logging.debug(f"Chat template not available: {str(e)}")

        # Fallback to simple formatting
        formatted = ""
        for msg in messages:
            role = msg['role']
            content = msg['content']

            if role == 'system':
                formatted += f"System: {content}\n\n"
            elif role == 'user':
                formatted += f"User: {content}\n\n"
            elif role == 'assistant':
                formatted += f"Assistant: {content}\n\n"

        formatted += "Assistant: "
        return formatted

    def _ensure_model_available_ollama(self, model_name: str) -> bool:
        """Ensure Ollama model is available, downloading if necessary."""
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
            stat = shutil.disk_usage(self.storage_paths['ollama'])
            available_space = stat.free / (1024 ** 3)

            if available_space < required_space * 1.2:
                logging.error(
                    f"Insufficient disk space for {model_name}. "
                    f"Required: {required_space:.1f}GB, Available: {available_space:.1f}GB"
                )
                return False

            # Download model
            logging.info(f"Downloading Ollama model: {model_name} ({required_space:.1f}GB)...")
            result = subprocess.run(
                ['ollama', 'pull', model_name],
                capture_output=True,
                text=True,
                timeout=3600
            )

            return result.returncode == 0

        except Exception as e:
            logging.error(f"Error ensuring Ollama model availability: {str(e)}")
            return False

    def chat_completion(self, messages: List[Dict[str, str]], model: str = None,
                       temperature: float = 0.4, max_tokens: Optional[int] = None,
                       task_type: str = 'general') -> Optional[str]:
        """
        Send chat completion request to local model.

        Args:
            messages: List of messages with 'role' and 'content'
            model: Model to use (if None, will be selected based on task_type)
            temperature: Temperature for response randomness (default: 0.4)
            max_tokens: Maximum tokens in response
            task_type: Type of task to determine appropriate model

        Returns:
            Optional[str]: Response content or None if error
        """
        if model is None:
            model = self.get_model_for_task(task_type)

        if max_tokens is None:
            max_tokens = DEFAULT_MAX_TOKENS

        if not model:
            logging.error(f"No model available for task type: {task_type}")
            return None

        logging.debug(f"Local {self.backend.value} API call - Model: {model}, Temp: {temperature}, Max tokens: {max_tokens}")

        # Route to appropriate backend
        if self.backend == LocalBackend.OLLAMA:
            return self._chat_completion_ollama(messages, model, temperature, max_tokens)
        elif self.backend == LocalBackend.LM_STUDIO:
            return self._chat_completion_lm_studio(messages, model, temperature, max_tokens)
        elif self.backend == LocalBackend.HUGGINGFACE_LOCAL:
            return self._chat_completion_huggingface_local(messages, model, temperature, max_tokens)
        elif self.backend == LocalBackend.HUGGINGFACE_API:
            return self._chat_completion_huggingface_api(messages, model, temperature, max_tokens)
        else:
            logging.error(f"Unknown backend: {self.backend}")
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
            logging.error(f"Failed to parse JSON from local model response: {str(e)}")
            logging.error(f"Response was: {response_text}")
            return None

    def simple_completion(self, prompt: str, model: str = None,
                         temperature: float = 0.4, max_tokens: Optional[int] = None,
                         task_type: str = 'general') -> Optional[str]:
        """Send simple completion request with single prompt."""
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
        """Validate that local model system is working."""
        try:
            response = self.simple_completion("Hello", model=self.models.get('tiny'), max_tokens=5)
            return response is not None
        except Exception as e:
            logging.error(f"Local model validation failed: {str(e)}")
            return False

    def create_fine_tuning_job(self, training_file_id: str, model: str = None,
                              suffix: str = None, hyperparameters: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Fine-tuning not supported via this API (manual process required)."""
        logging.warning("Local model fine-tuning requires manual process")
        return None

    def upload_training_file(self, file_path: str) -> Optional[str]:
        """Training file upload not supported (manual process required)."""
        logging.warning("Local model fine-tuning requires manual process")
        return None

    def get_fine_tuning_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Fine-tuning status not supported (manual process required)."""
        logging.warning("Local model fine-tuning requires manual process")
        return None

    def get_backend_info(self) -> Dict[str, Any]:
        """
        Get information about current backend and available models.

        Returns:
            Dict with backend info, models, and storage details
        """
        info = {
            'backend': self.backend.value if self.backend else None,
            'backend_info': self.backend_info,
            'available_models': self.models,
            'model_sizes_gb': self.model_sizes,
        }

        if self.backend == LocalBackend.OLLAMA:
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

        elif self.backend == LocalBackend.LM_STUDIO:
            # Add LM Studio-specific info
            try:
                models_list = self.client.models.list()
                info['loaded_models'] = [m.id for m in models_list.data]
            except Exception as e:
                logging.debug(f"Could not get LM Studio models: {str(e)}")

        elif self.backend == LocalBackend.HUGGINGFACE_LOCAL:
            # Add HF local-specific info
            info['device'] = self.client['device']
            info['currently_loaded'] = self.client['current_model_name']

        return info
