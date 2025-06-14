"""
Fine-tuning module for desaka_unifier project.

This module handles fine-tuning of OpenAI models for specific tasks like
product name generation, description translation, category mapping, etc.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from unifierlib.openai_client import OpenAIClient
from unifierlib.constants import FINE_TUNED_MODELS_FILE
from shared.file_ops import ensure_directory_exists, load_json_file, save_json_file, save_jsonl_file


class FineTuningManager:
    """
    Manager for fine-tuning OpenAI models for specific product processing tasks.
    """
    
    def __init__(self, memory_data: Optional[Dict[str, Any]] = None, language: str = 'CS'):
        """
        Initialize fine-tuning manager.
        
        Args:
            memory_data (Optional[Dict[str, Any]]): Memory data for training examples
            language (str): Language code for training data
        """
        self.memory = memory_data or {}
        self.language = language
        self.openai_client = OpenAIClient()
        
        # Define task types for fine-tuning
        self.task_types = {
            'name_generation': 'Product name generation from type, brand, model',
            'description_translation': 'Product description translation and validation',
            'category_mapping': 'Category mapping for different platforms',
            'brand_detection': 'Brand detection from product names',
            'type_detection': 'Product type detection from names',
            'model_detection': 'Product model detection from names',
            'keyword_generation': 'Keyword generation for platforms'
        }
        
    def prepare_training_data(self, task_type: str) -> List[Dict[str, Any]]:
        """
        Prepare training data for specific task type from memory files.
        
        Args:
            task_type (str): Type of task to prepare data for
            
        Returns:
            List[Dict[str, Any]]: Training examples in OpenAI format
        """
        training_examples = []
        
        if task_type == 'name_generation':
            training_examples = self._prepare_name_generation_data()
        elif task_type == 'description_translation':
            training_examples = self._prepare_description_data()
        elif task_type == 'category_mapping':
            training_examples = self._prepare_category_mapping_data()
        elif task_type == 'brand_detection':
            training_examples = self._prepare_brand_detection_data()
        elif task_type == 'type_detection':
            training_examples = self._prepare_type_detection_data()
        elif task_type == 'model_detection':
            training_examples = self._prepare_model_detection_data()
        elif task_type == 'keyword_generation':
            training_examples = self._prepare_keyword_generation_data()
        else:
            logging.error(f"Unknown task type: {task_type}")
            
        return training_examples
    
    def _prepare_name_generation_data(self) -> List[Dict[str, Any]]:
        """Prepare training data for product name generation using actual production prompts."""
        examples = []

        # Get memory data
        name_memory_key = f"NameMemory_{self.language}"
        type_memory_key = f"ProductTypeMemory_{self.language}"
        brand_memory_key = f"ProductBrandMemory_{self.language}"
        model_memory_key = f"ProductModelMemory_{self.language}"

        name_memory = self.memory.get(name_memory_key, {})
        type_memory = self.memory.get(type_memory_key, {})
        brand_memory = self.memory.get(brand_memory_key, {})
        model_memory = self.memory.get(model_memory_key, {})

        for original_name, final_name in name_memory.items():
            if original_name in type_memory and original_name in brand_memory and original_name in model_memory:
                product_type = type_memory[original_name]
                brand = brand_memory[original_name]
                model = model_memory[original_name]

                # Use actual production prompt from openai_unifier.py
                product_json = f'{{"name": "{original_name}", "description": "", "short_description": "", "url": ""}}'

                prompt = f"""I humbly request your assistance in analyzing a table tennis product name. Please help me break down the product information into three distinct, non-overlapping components.

Product information:
{product_json}

I respectfully ask you to:
1. Search the internet for table tennis product naming conventions
2. Check pincesobchod.cz for how they structure table tennis product names
3. Analyze the product information carefully
4. Extract three DISTINCT components: type, brand, and model
5. If the text is not in Czech, translate 'type' and 'model' to Czech while preserving table tennis-specific vocabulary
6. Keep 'brand' in original language (manufacturer name)
7. Ensure these three sections DO NOT overlap - each word should belong to only one category
8. TYPE: General product category (e.g., "Rubber", "Blade", "Ball", "Paddle")
9. BRAND: Manufacturer name (e.g., "Butterfly", "Stiga", "Yasaka")
10. MODEL: Specific product model/name (e.g., "Tenergy 05", "Clipper Wood", "Premium 3-Star")
11. Use current industry standards for product naming
12. Return JSON with exactly three properties: "type", "brand", "model"

IMPORTANT: Type, brand, and model must be completely separate - no word should appear in multiple categories.

Example: "Butterfly Tenergy 05 Rubber" -> type: "Rubber", brand: "Butterfly", model: "Tenergy 05"

Please return your response as valid JSON only."""

                expected_response = f'{{"type": "{product_type}", "brand": "{brand}", "model": "{model}"}}'

                example = {
                    "messages": [
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": expected_response}
                    ]
                }
                examples.append(example)

        return examples
    
    def _prepare_description_data(self) -> List[Dict[str, Any]]:
        """Prepare training data for description translation using actual production prompts."""
        examples = []

        desc_memory_key = f"DescMemory_{self.language}"
        desc_memory = self.memory.get(desc_memory_key, {})

        for original_name, translated_desc in desc_memory.items():
            if translated_desc and len(translated_desc) > 20:  # Only meaningful descriptions
                # Use actual production prompt from openai_unifier.py
                prompt = f"""I humbly request your assistance in translating and validating a product description for table tennis equipment. Please help me translate the following text while preserving table tennis terminology.

Original description: {translated_desc}

I respectfully ask you to:
1. Search the internet for current table tennis terminology and product descriptions
2. Check pincesobchod.cz for how they describe similar table tennis products
3. If the text is not in Czech, translate it to Czech while preserving table tennis-specific vocabulary (e.g., "rubber", "blade", "paddle", "spin", "speed", "control")
4. Remove any external website links and replace them with their text content
5. Preserve and correct HTML formatting - DO NOT remove HTML tags, only fix syntax errors
6. Keep the original meaning and structure intact
7. Maintain all HTML formatting including <p>, <br>, <strong>, <em>, <ul>, <li> tags
8. Use current industry-standard terminology that customers would understand
9. Return the result as JSON with the property "description"

IMPORTANT: HTML must be preserved and corrected, not removed.

Please return your response as valid JSON only."""

                expected_response = f'{{"description": "{translated_desc}"}}'

                example = {
                    "messages": [
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": expected_response}
                    ]
                }
                examples.append(example)

        return examples
    
    def _prepare_category_mapping_data(self) -> List[Dict[str, Any]]:
        """Prepare training data for category mapping using actual production prompts."""
        examples = []

        platforms = ['Glami', 'Google', 'Heureka', 'Zbozi']

        for platform in platforms:
            mapping_key = f"CategoryMapping{platform}_{self.language}"
            mapping_data = self.memory.get(mapping_key, {})

            # Get platform-specific URL for research
            platform_urls = {
                'Heureka': 'heureka.cz',
                'Glami': 'glami.cz',
                'Google': 'google.com/shopping',
                'Zbozi': 'zbozi.cz'
            }
            platform_url = platform_urls.get(platform, f"{platform.lower()}.com")

            for category, mapped_category in mapping_data.items():
                if mapped_category:
                    # Use actual production prompt from openai_unifier.py
                    prompt = f"""I humbly request your assistance in mapping a product category to {platform} platform category. Please help me find the most appropriate mapping.

Original category: {category}
Target platform: {platform}

I respectfully ask you to:
1. Search the internet for {platform} platform category structure
2. Visit {platform_url} to research their current category taxonomy
3. Check pincesobchod.cz for table tennis product categorization
4. Analyze the original category carefully
5. Consider the target platform's category structure and naming conventions
6. Draw inspiration from existing mappings in memory for consistency
7. Suggest the most appropriate {platform} category mapping
8. Use Czech language if applicable for the platform
9. Ensure the mapping follows {platform}'s actual category structure
10. Return the result as JSON with the property "mapping"

Please return your response as valid JSON only."""

                    expected_response = f'{{"mapping": "{mapped_category}"}}'

                    example = {
                        "messages": [
                            {"role": "user", "content": prompt},
                            {"role": "assistant", "content": expected_response}
                        ]
                    }
                    examples.append(example)

        return examples
    
    def _prepare_brand_detection_data(self) -> List[Dict[str, Any]]:
        """Prepare training data for brand detection using actual production prompts."""
        examples = []

        brand_memory_key = f"ProductBrandMemory_{self.language}"
        brand_memory = self.memory.get(brand_memory_key, {})

        # Get brand list for context
        brand_list = list(self.memory.get('BrandCodeList', {}).keys())
        brands_text = '\n'.join([f"- {brand}" for brand in brand_list])

        for product_name, brand in brand_memory.items():
            if brand and brand in brand_list:
                # Use actual production prompt from openai_unifier.py
                product_json = f'{{"name": "{product_name}", "description": "", "short_description": "", "url": ""}}'

                prompt = f"""I humbly request your help in identifying the brand of a product. Please assist me in selecting the correct brand from the provided list.

Product information:
{product_json}

Available brands:
{brands_text}

I respectfully ask you to:
1. Search the internet for information about table tennis brands and manufacturers
2. Check pincesobchod.cz for brand information and product listings
3. Carefully analyze the product information
4. Select EXACTLY ONE brand from the list above
5. The brand must be chosen strictly from the provided list
6. Use your knowledge of current table tennis brand landscape
7. Return the result as JSON with the property "brand"

Please return your response as valid JSON only."""

                expected_response = f'{{"brand": "{brand}"}}'

                example = {
                    "messages": [
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": expected_response}
                    ]
                }
                examples.append(example)

        return examples
    
    def _prepare_type_detection_data(self) -> List[Dict[str, Any]]:
        """Prepare training data for product type detection using actual production prompts."""
        examples = []

        type_memory_key = f"ProductTypeMemory_{self.language}"
        type_memory = self.memory.get(type_memory_key, {})

        for product_name, product_type in type_memory.items():
            if product_type:
                # Use actual production prompt from openai_unifier.py
                product_json = f'{{"name": "{product_name}", "description": "", "short_description": "", "url": ""}}'

                prompt = f"""I humbly request your assistance in identifying the product type. Please help me determine what type of product this is.

Product information:
{product_json}

I respectfully ask you to:
1. Analyze the product information carefully
2. Determine the general product type (e.g., "Laptop", "Shirt", "Ball", "Racket")
3. Use Czech language for the type
4. Keep it concise and general (not specific model)
5. Return the result as JSON with the property "type"

Please return your response as valid JSON only."""

                expected_response = f'{{"type": "{product_type}"}}'

                example = {
                    "messages": [
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": expected_response}
                    ]
                }
                examples.append(example)

        return examples
    
    def _prepare_model_detection_data(self) -> List[Dict[str, Any]]:
        """Prepare training data for product model detection using actual production prompts."""
        examples = []

        model_memory_key = f"ProductModelMemory_{self.language}"
        model_memory = self.memory.get(model_memory_key, {})

        for product_name, model in model_memory.items():
            if model:
                # Use actual production prompt from openai_unifier.py
                product_json = f'{{"name": "{product_name}", "description": "", "short_description": "", "url": ""}}'

                prompt = f"""I humbly request your assistance in identifying the product model. Please help me determine the specific model of this product.

Product information:
{product_json}

I respectfully ask you to:
1. Analyze the product information carefully
2. Determine the specific product model (e.g., "Tenergy 05", "Clipper Wood", "Premium 3-Star")
3. Use Czech language for the model if applicable
4. Keep it specific to the model, not general type or brand
5. Return the result as JSON with the property "model"

Please return your response as valid JSON only."""

                expected_response = f'{{"model": "{model}"}}'

                example = {
                    "messages": [
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": expected_response}
                    ]
                }
                examples.append(example)

        return examples
    
    def _prepare_keyword_generation_data(self) -> List[Dict[str, Any]]:
        """Prepare training data for keyword generation using actual production prompts."""
        examples = []

        platforms = ['Google', 'Zbozi']

        for platform in platforms:
            keywords_key = f"Keywords{platform}_{self.language}"
            keywords_data = self.memory.get(keywords_key, {})

            for product_name, keywords in keywords_data.items():
                if keywords:
                    # Use actual production prompt from openai_unifier.py
                    product_json = f'{{"name": "{product_name}", "description": "", "short_description": "", "url": ""}}'

                    if platform == 'Google':
                        prompt = f"""I humbly request your assistance in generating keywords for a product. Please help me create relevant search keywords.

Product information:
{product_json}

I respectfully ask you to:
1. Search the internet for similar products and current market trends
2. Check pincesobchod.cz for table tennis product terminology and keywords
3. Analyze the product information thoroughly
4. Generate exactly 5 relevant keywords
5. Keywords should be suitable for Google advertising
6. Draw inspiration from existing keywords in memory for consistency
7. Use current market terminology and popular search terms
8. Return the result as JSON with the property "keywords"
9. Format as a single string with keywords separated by commas

Please return your response as valid JSON only."""
                    else:  # Zbozi
                        prompt = f"""I humbly request your help in generating keywords for a Czech shopping platform. Please assist me in creating relevant keywords.

Product information:
{product_json}

I respectfully ask you to:
1. Search the internet for similar products on Czech e-commerce sites
2. Check pincesobchod.cz for table tennis product terminology in Czech
3. Research Zbozi.cz platform to understand their keyword structure
4. Analyze the product information carefully
5. Generate exactly 2 relevant keywords
6. Keywords should be suitable for Zbozi.cz platform
7. Preferably extract from product name but not exclusively
8. Draw inspiration from existing keywords in memory for consistency
9. Use Czech terminology that Czech customers would search for
10. Return the result as JSON with the property "keywords"
11. Format as a single string with 2 keywords separated by comma

Please return your response as valid JSON only."""

                    expected_response = f'{{"keywords": "{keywords}"}}'

                    example = {
                        "messages": [
                            {"role": "user", "content": prompt},
                            {"role": "assistant", "content": expected_response}
                        ]
                    }
                    examples.append(example)

        return examples
    
    def save_training_file(self, task_type: str, training_examples: List[Dict[str, Any]],
                          output_dir: str = None) -> str:
        """
        Save training examples to JSONL file for OpenAI fine-tuning using file_ops.

        Args:
            task_type (str): Type of task
            training_examples (List[Dict[str, Any]]): Training examples
            output_dir (str): Output directory (default: script directory)

        Returns:
            str: Path to saved training file
        """
        if output_dir is None:
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_dir = script_dir

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"training_{task_type}_{self.language}_{timestamp}.jsonl"
        filepath = os.path.join(output_dir, filename)

        save_jsonl_file(training_examples, filepath)
        logging.info(f"Saved {len(training_examples)} training examples to {filepath}")
        return filepath
    
    def start_fine_tuning(self, task_type: str, min_examples: int = 50) -> Optional[str]:
        """
        Start fine-tuning process for specific task type.
        
        Args:
            task_type (str): Type of task to fine-tune
            min_examples (int): Minimum number of examples required
            
        Returns:
            Optional[str]: Fine-tuning job ID or None if failed
        """
        if task_type not in self.task_types:
            logging.error(f"Unknown task type: {task_type}")
            return None
            
        # Prepare training data
        training_examples = self.prepare_training_data(task_type)
        
        if len(training_examples) < min_examples:
            logging.warning(f"Not enough training examples for {task_type}: {len(training_examples)} < {min_examples}")
            return None
            
        # Save training file
        training_file_path = self.save_training_file(task_type, training_examples)
        
        # Upload training file
        file_id = self.openai_client.upload_training_file(training_file_path)
        if not file_id:
            logging.error(f"Failed to upload training file for {task_type}")
            return None
            
        # Start fine-tuning job
        suffix = f"{task_type}_{self.language}".lower()
        job_id = self.openai_client.create_fine_tuning_job(
            training_file_id=file_id,
            suffix=suffix
        )
        
        if job_id:
            logging.info(f"Started fine-tuning job {job_id} for {task_type}")
        else:
            logging.error(f"Failed to start fine-tuning job for {task_type}")
            
        return job_id
    
    def fine_tune_all_tasks(self, min_examples: int = 10) -> Dict[str, Optional[str]]:
        """
        Start fine-tuning for all available task types.
        
        Args:
            min_examples (int): Minimum number of examples required per task
            
        Returns:
            Dict[str, Optional[str]]: Dictionary mapping task types to job IDs
        """
        job_ids = {}
        
        for task_type in self.task_types.keys():
            logging.info(f"Starting fine-tuning for {task_type}...")
            job_id = self.start_fine_tuning(task_type, min_examples)
            job_ids[task_type] = job_id
            
        return job_ids

    def load_fine_tuned_models(self, script_dir: str) -> Dict[str, str]:
        """
        Load fine-tuned model IDs from file using file_ops.

        Args:
            script_dir (str): Script directory where models file is stored

        Returns:
            Dict[str, str]: Dictionary mapping task types to model IDs
        """
        models_file_path = os.path.join(script_dir, FINE_TUNED_MODELS_FILE)

        if not os.path.exists(models_file_path):
            logging.info(f"Fine-tuned models file not found: {models_file_path}")
            return {}

        try:
            models = load_json_file(models_file_path)
            logging.info(f"Loaded {len(models)} fine-tuned models from {models_file_path}")
            return models
        except Exception as e:
            logging.error(f"Error loading fine-tuned models file: {str(e)}", exc_info=True)
            return {}

    def save_fine_tuned_models(self, models: Dict[str, str], script_dir: str) -> bool:
        """
        Save fine-tuned model IDs to file using file_ops.

        Args:
            models (Dict[str, str]): Dictionary mapping task types to model IDs
            script_dir (str): Script directory where models file should be stored

        Returns:
            bool: True if saved successfully, False otherwise
        """
        models_file_path = os.path.join(script_dir, FINE_TUNED_MODELS_FILE)

        try:
            save_json_file(models, models_file_path)
            logging.info(f"Saved {len(models)} fine-tuned models to {models_file_path}")
            return True
        except Exception as e:
            logging.error(f"Error saving fine-tuned models file: {str(e)}", exc_info=True)
            return False

    def update_fine_tuned_model(self, task_type: str, model_id: str, script_dir: str) -> bool:
        """
        Update a specific fine-tuned model ID.

        Args:
            task_type (str): Task type
            model_id (str): Fine-tuned model ID
            script_dir (str): Script directory

        Returns:
            bool: True if updated successfully, False otherwise
        """
        models = self.load_fine_tuned_models(script_dir)
        models[task_type] = model_id
        return self.save_fine_tuned_models(models, script_dir)

    def check_fine_tuning_status(self, job_ids: Dict[str, Optional[str]], script_dir: str) -> Dict[str, str]:
        """
        Check status of fine-tuning jobs and update model IDs when completed.

        Args:
            job_ids (Dict[str, Optional[str]]): Dictionary mapping task types to job IDs
            script_dir (str): Script directory

        Returns:
            Dict[str, str]: Dictionary mapping task types to their status
        """
        status_report = {}
        models = self.load_fine_tuned_models(script_dir)
        models_updated = False

        for task_type, job_id in job_ids.items():
            if not job_id:
                status_report[task_type] = "No job ID"
                continue

            status_info = self.openai_client.get_fine_tuning_job_status(job_id)
            if not status_info:
                status_report[task_type] = "Error getting status"
                continue

            status = status_info.get('status', 'unknown')
            status_report[task_type] = status

            # If job is completed and we have a fine-tuned model, save it
            if status == 'succeeded' and status_info.get('fine_tuned_model'):
                fine_tuned_model = status_info['fine_tuned_model']
                if models.get(task_type) != fine_tuned_model:
                    models[task_type] = fine_tuned_model
                    models_updated = True
                    logging.info(f"Fine-tuning completed for {task_type}: {fine_tuned_model}")

        # Save updated models if any were completed
        if models_updated:
            self.save_fine_tuned_models(models, script_dir)

        return status_report
