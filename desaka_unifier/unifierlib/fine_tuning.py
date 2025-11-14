"""
Fine-tuning module for desaka_unifier project.

This module handles fine-tuning of OpenAI models for specific tasks like
product name generation, description translation, category mapping, etc.

Includes support for negative examples from Trash files to improve model training.
"""

import os
import json
import logging
import csv
from typing import Dict, Any, List, Optional
from datetime import datetime
from unifierlib.openai_client import OpenAIClient
from unifierlib.constants import FINE_TUNED_MODELS_FILE
from shared.file_ops import ensure_directory_exists, load_json_file, save_json_file, save_jsonl_file


class FineTuningManager:
    """
    Manager for fine-tuning OpenAI models for specific product processing tasks.
    Supports both positive examples (Memory files) and negative examples (Trash files).
    """

    def __init__(self, memory_data: Optional[Dict[str, Any]] = None, language: str = 'CS',
                 trash_dir: Optional[str] = None):
        """
        Initialize fine-tuning manager.

        Args:
            memory_data (Optional[Dict[str, Any]]): Memory data for training examples
            language (str): Language code for training data
            trash_dir (Optional[str]): Directory containing trash files with negative examples
        """
        self.memory = memory_data or {}
        self.language = language
        self.openai_client = OpenAIClient()

        # Set trash directory (default: memory_tests/trash relative to Memory dir)
        if trash_dir is None:
            # Try to find trash directory relative to typical Memory location
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.trash_dir = os.path.join(script_dir, "memory_tests", "trash")
        else:
            self.trash_dir = trash_dir

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

    def _load_trash_file(self, memory_prefix: str) -> Dict[str, str]:
        """
        Load trash file with rejected values (negative examples).

        Args:
            memory_prefix (str): Memory file prefix (e.g., 'ProductBrandMemory')

        Returns:
            Dict[str, str]: Dictionary mapping keys to rejected values
        """
        trash_filename = f"{memory_prefix}_{self.language}_trash.csv"
        trash_filepath = os.path.join(self.trash_dir, trash_filename)

        trash_data = {}

        if not os.path.exists(trash_filepath):
            logging.debug(f"Trash file not found: {trash_filepath}")
            return trash_data

        try:
            with open(trash_filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    key = row.get('KEY', '').strip()
                    value = row.get('VALUE', '').strip()
                    if key and value:
                        trash_data[key] = value

            logging.info(f"Loaded {len(trash_data)} trash entries from {trash_filepath}")
        except Exception as e:
            logging.error(f"Error loading trash file {trash_filepath}: {str(e)}", exc_info=True)

        return trash_data
        
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

        # Get target language name
        from unifierlib.memory_manager import get_language_name
        target_language = get_language_name(self.language)

        # Note: Trash handling for name generation is covered by individual
        # type/brand/model detection methods since the output consists of these components

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
5. If the text is not in {target_language}, translate 'type' and 'model' to {target_language} using proper table tennis terminology (e.g., "rubber" = "potah", "blade" = "dřevo", not literal translations)
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

        logging.info(f"Name generation: {len(examples)} training examples")
        return examples

    def _prepare_description_data(self) -> List[Dict[str, Any]]:
        """Prepare training data for description translation using actual production prompts."""
        examples = []

        desc_memory_key = f"DescMemory_{self.language}"
        desc_memory = self.memory.get(desc_memory_key, {})

        # Get target language name
        from unifierlib.memory_manager import get_language_name
        target_language = get_language_name(self.language)

        # Load trash data (rejected descriptions)
        trash_data = self._load_trash_file("DescMemory")

        # Process positive examples
        for original_name, translated_desc in desc_memory.items():
            if translated_desc and len(translated_desc) > 20:  # Only meaningful descriptions
                # Use actual production prompt from openai_unifier.py
                prompt = f"""I humbly request your assistance in translating and validating a product description for table tennis equipment. Please help me translate the following text while preserving table tennis terminology.

Original description: {translated_desc}

I respectfully ask you to:
1. Search the internet for current table tennis terminology and product descriptions
2. Check pincesobchod.cz for how they describe similar table tennis products
3. If the text is not in {target_language}, translate it to {target_language} using proper table tennis SLANG and terminology - prioritize table tennis industry terms over literal translations:
   • "rubber" = "potah" (NEVER "guma")
   • "blade" = "dřevo" (NEVER "čepel")
   • "paddle/racket" = "pálka"
   • "spin" = "rotace" or "točení"
   • "speed" = "rychlost"
   • "control" = "kontrola"
   • "sponge" = "houba"
   • "topsheet" = "povrch"
4. Remove any external website links and replace them with their text content
5. Preserve and correct HTML formatting - DO NOT remove HTML tags, only fix syntax errors
6. Keep the original meaning and structure intact
7. Maintain all HTML formatting including <p>, <br>, <strong>, <em>, <ul>, <li> tags
8. Use current table tennis industry terminology that customers would understand
9. Return the result as JSON with the property "description"

CRITICAL: Use table tennis slang, not literal translations. HTML must be preserved and corrected, not removed.

Please return your response as valid JSON only."""

                expected_response = f'{{"description": "{translated_desc}"}}'

                example = {
                    "messages": [
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": expected_response}
                    ]
                }
                examples.append(example)

        # Process negative examples from trash
        for original_name, rejected_desc in trash_data.items():
            if original_name in desc_memory:
                correct_desc = desc_memory[original_name]
                if correct_desc and len(correct_desc) > 20:
                    prompt = f"""I humbly request your assistance in translating and validating a product description for table tennis equipment. Please help me translate the following text while preserving table tennis terminology.

Original description: {correct_desc}

I respectfully ask you to:
1. Search the internet for current table tennis terminology and product descriptions
2. Check pincesobchod.cz for how they describe similar table tennis products
3. If the text is not in {target_language}, translate it to {target_language} using proper table tennis SLANG and terminology - prioritize table tennis industry terms over literal translations:
   • "rubber" = "potah" (NEVER "guma")
   • "blade" = "dřevo" (NEVER "čepel")
   • "paddle/racket" = "pálka"
   • "spin" = "rotace" or "točení"
   • "speed" = "rychlost"
   • "control" = "kontrola"
   • "sponge" = "houba"
   • "topsheet" = "povrch"
4. Remove any external website links and replace them with their text content
5. Preserve and correct HTML formatting - DO NOT remove HTML tags, only fix syntax errors
6. Keep the original meaning and structure intact
7. Maintain all HTML formatting including <p>, <br>, <strong>, <em>, <ul>, <li> tags
8. Use current table tennis industry terminology that customers would understand
9. Return the result as JSON with the property "description"

CRITICAL: Use table tennis slang, not literal translations. HTML must be preserved and corrected, not removed.

Please return your response as valid JSON only."""

                    expected_response = f'{{"description": "{correct_desc}"}}'

                    example = {
                        "messages": [
                            {"role": "user", "content": prompt},
                            {"role": "assistant", "content": expected_response}
                        ]
                    }
                    examples.append(example)

        logging.info(f"Description translation: {len(examples)} training examples (including trash-derived examples)")
        return examples

    def _prepare_category_mapping_data(self) -> List[Dict[str, Any]]:
        """Prepare training data for category mapping using actual production prompts."""
        examples = []

        # Get target language name
        from unifierlib.memory_manager import get_language_name
        target_language = get_language_name(self.language)

        platforms = ['Glami', 'Google', 'Heureka', 'Zbozi']

        for platform in platforms:
            mapping_key = f"CategoryMapping{platform}_{self.language}"
            mapping_data = self.memory.get(mapping_key, {})

            # Load trash data for this platform
            trash_data = self._load_trash_file(f"CategoryMapping{platform}")

            # Get platform-specific URL for research
            platform_urls = {
                'Heureka': 'heureka.cz',
                'Glami': 'glami.cz',
                'Google': 'google.com/shopping',
                'Zbozi': 'zbozi.cz'
            }
            platform_url = platform_urls.get(platform, f"{platform.lower()}.com")

            # Process positive examples
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
8. Translate the mapping to {target_language} if applicable for the platform
9. Use proper table tennis terminology in {target_language} (e.g., "rubber" = "potah", "blade" = "dřevo", not literal translations)
10. Ensure the mapping follows {platform}'s actual category structure
11. Return the result as JSON with the property "mapping"

Please return your response as valid JSON only."""

                    expected_response = f'{{"mapping": "{mapped_category}"}}'

                    example = {
                        "messages": [
                            {"role": "user", "content": prompt},
                            {"role": "assistant", "content": expected_response}
                        ]
                    }
                    examples.append(example)

            # Process negative examples from trash
            for category, rejected_mapping in trash_data.items():
                if category in mapping_data:
                    correct_mapping = mapping_data[category]
                    if correct_mapping:
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
8. Translate the mapping to {target_language} if applicable for the platform
9. Use proper table tennis terminology in {target_language} (e.g., "rubber" = "potah", "blade" = "dřevo", not literal translations)
10. Ensure the mapping follows {platform}'s actual category structure
11. Return the result as JSON with the property "mapping"

Please return your response as valid JSON only."""

                        expected_response = f'{{"mapping": "{correct_mapping}"}}'

                        example = {
                            "messages": [
                                {"role": "user", "content": prompt},
                                {"role": "assistant", "content": expected_response}
                            ]
                        }
                        examples.append(example)

        logging.info(f"Category mapping: {len(examples)} training examples (including trash-derived examples)")
        return examples

    def _prepare_brand_detection_data(self) -> List[Dict[str, Any]]:
        """Prepare training data for brand detection using actual production prompts."""
        examples = []

        brand_memory_key = f"ProductBrandMemory_{self.language}"
        brand_memory = self.memory.get(brand_memory_key, {})

        # Get target language name
        from unifierlib.memory_manager import get_language_name
        target_language = get_language_name(self.language)

        # Load trash data (rejected brand values)
        trash_data = self._load_trash_file("ProductBrandMemory")

        # Get brand list for context
        brand_list = list(self.memory.get('BrandCodeList', {}).keys())
        brands_text = '\n'.join([f"- {brand}" for brand in brand_list])

        # Process positive examples from memory
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
6. Keep brand names in their original language (manufacturer names should not be translated)
7. If any explanatory text is needed, translate it to {target_language} using proper table tennis terminology (e.g., "rubber" = "potah", "blade" = "dřevo", not literal translations)
8. Use your knowledge of current table tennis brand landscape
9. Return the result as JSON with the property "brand"

Please return your response as valid JSON only."""

                expected_response = f'{{"brand": "{brand}"}}'

                example = {
                    "messages": [
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": expected_response}
                    ]
                }
                examples.append(example)

        # Process negative examples from trash - reinforce correct answers
        for product_name, rejected_brand in trash_data.items():
            # If we have the correct brand in memory, create additional training example
            if product_name in brand_memory:
                correct_brand = brand_memory[product_name]
                if correct_brand and correct_brand in brand_list:
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
6. Keep brand names in their original language (manufacturer names should not be translated)
7. If any explanatory text is needed, translate it to {target_language} using proper table tennis terminology (e.g., "rubber" = "potah", "blade" = "dřevo", not literal translations)
8. Use your knowledge of current table tennis brand landscape
9. Return the result as JSON with the property "brand"

Please return your response as valid JSON only."""

                    expected_response = f'{{"brand": "{correct_brand}"}}'

                    example = {
                        "messages": [
                            {"role": "user", "content": prompt},
                            {"role": "assistant", "content": expected_response}
                        ]
                    }
                    examples.append(example)

        logging.info(f"Brand detection: {len(examples)} training examples (including trash-derived examples)")
        return examples
    
    def _prepare_type_detection_data(self) -> List[Dict[str, Any]]:
        """Prepare training data for product type detection using actual production prompts."""
        examples = []

        type_memory_key = f"ProductTypeMemory_{self.language}"
        type_memory = self.memory.get(type_memory_key, {})

        # Get target language name
        from unifierlib.memory_manager import get_language_name
        target_language = get_language_name(self.language)

        # Load trash data (rejected type values)
        trash_data = self._load_trash_file("ProductTypeMemory")

        # Process positive examples from memory
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
3. Translate the product type to {target_language} using proper table tennis terminology (e.g., "rubber" = "potah", "blade" = "dřevo", not literal translations)
4. Keep it concise and general (not specific model)
5. Use {target_language} language for the type
6. Return the result as JSON with the property "type"
7. Always begin the response with capital letter

Please return your response as valid JSON only."""

                expected_response = f'{{"type": "{product_type}"}}'

                example = {
                    "messages": [
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": expected_response}
                    ]
                }
                examples.append(example)

        # Process negative examples from trash
        for product_name, rejected_type in trash_data.items():
            if product_name in type_memory:
                correct_type = type_memory[product_name]
                if correct_type:
                    product_json = f'{{"name": "{product_name}", "description": "", "short_description": "", "url": ""}}'

                    prompt = f"""I humbly request your assistance in identifying the product type. Please help me determine what type of product this is.

Product information:
{product_json}

I respectfully ask you to:
1. Analyze the product information carefully
2. Determine the general product type (e.g., "Laptop", "Shirt", "Ball", "Racket")
3. Translate the product type to {target_language} using proper table tennis terminology (e.g., "rubber" = "potah", "blade" = "dřevo", not literal translations)
4. Keep it concise and general (not specific model)
5. Use {target_language} language for the type
6. Return the result as JSON with the property "type"
7. Always begin the response with capital letter

Please return your response as valid JSON only."""

                    expected_response = f'{{"type": "{correct_type}"}}'

                    example = {
                        "messages": [
                            {"role": "user", "content": prompt},
                            {"role": "assistant", "content": expected_response}
                        ]
                    }
                    examples.append(example)

        logging.info(f"Type detection: {len(examples)} training examples (including trash-derived examples)")
        return examples
    
    def _prepare_model_detection_data(self) -> List[Dict[str, Any]]:
        """Prepare training data for product model detection using actual production prompts."""
        examples = []

        model_memory_key = f"ProductModelMemory_{self.language}"
        model_memory = self.memory.get(model_memory_key, {})

        # Get target language name
        from unifierlib.memory_manager import get_language_name
        target_language = get_language_name(self.language)

        # Load trash data (rejected model values)
        trash_data = self._load_trash_file("ProductModelMemory")

        # Process positive examples from memory
        for product_name, model in model_memory.items():
            if model:
                # Use actual production prompt from openai_unifier.py
                product_json = f'{{"name": "{product_name}", "description": "", "short_description": "", "url": ""}}'

                prompt = f"""I humbly request your help in identifying the product model. Please assist me in determining the specific model of this product.

Product information:
{product_json}

I respectfully ask you to:
1. Analyze the product information thoroughly
2. Extract the specific model name/number (e.g., "ROG Strix", "Air Max 90", "Pro V1")
3. If the model name is not in {target_language}, translate descriptive parts to {target_language} using proper table tennis terminology (e.g., "rubber" = "potah", "blade" = "dřevo", not literal translations)
4. Keep brand-specific model names in their original form when appropriate
5. Keep it concise and specific to the model
6. Return the result as JSON with the property "model"

Please return your response as valid JSON only."""

                expected_response = f'{{"model": "{model}"}}'

                example = {
                    "messages": [
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": expected_response}
                    ]
                }
                examples.append(example)

        # Process negative examples from trash
        for product_name, rejected_model in trash_data.items():
            if product_name in model_memory:
                correct_model = model_memory[product_name]
                if correct_model:
                    product_json = f'{{"name": "{product_name}", "description": "", "short_description": "", "url": ""}}'

                    prompt = f"""I humbly request your help in identifying the product model. Please assist me in determining the specific model of this product.

Product information:
{product_json}

I respectfully ask you to:
1. Analyze the product information thoroughly
2. Extract the specific model name/number (e.g., "ROG Strix", "Air Max 90", "Pro V1")
3. If the model name is not in {target_language}, translate descriptive parts to {target_language} using proper table tennis terminology (e.g., "rubber" = "potah", "blade" = "dřevo", not literal translations)
4. Keep brand-specific model names in their original form when appropriate
5. Keep it concise and specific to the model
6. Return the result as JSON with the property "model"

Please return your response as valid JSON only."""

                    expected_response = f'{{"model": "{correct_model}"}}'

                    example = {
                        "messages": [
                            {"role": "user", "content": prompt},
                            {"role": "assistant", "content": expected_response}
                        ]
                    }
                    examples.append(example)

        logging.info(f"Model detection: {len(examples)} training examples (including trash-derived examples)")
        return examples
    
    def _prepare_keyword_generation_data(self) -> List[Dict[str, Any]]:
        """Prepare training data for keyword generation using actual production prompts."""
        examples = []

        # Get target language name
        from unifierlib.memory_manager import get_language_name
        target_language = get_language_name(self.language)

        platforms = ['Google', 'Zbozi']

        for platform in platforms:
            keywords_key = f"Keywords{platform}_{self.language}"
            keywords_data = self.memory.get(keywords_key, {})

            # Load trash data for this platform
            trash_data = self._load_trash_file(f"Keywords{platform}")

            # Process positive examples
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
4. Generate exactly 5 relevant keywords in {target_language}
5. Keywords should be suitable for Google advertising
6. Draw inspiration from existing keywords in memory for consistency
7. Use current market terminology and popular search terms in {target_language}
8. Use proper table tennis terminology in {target_language} (e.g., "rubber" = "potah", "blade" = "dřevo", not literal translations)
9. Return the result as JSON with the property "keywords"
10. Format as a single string with keywords separated by commas

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
5. Generate exactly 2 relevant keywords in {target_language}
6. Keywords should be suitable for Zbozi.cz platform
7. Preferably extract from product name but not exclusively
8. Draw inspiration from existing keywords in memory for consistency
9. Use {target_language} terminology that customers would search for
10. Use proper table tennis terminology in {target_language} (e.g., "rubber" = "potah", "blade" = "dřevo", not literal translations)
11. Return the result as JSON with the property "keywords"
12. Format as a single string with 2 keywords separated by comma

Please return your response as valid JSON only."""

                    expected_response = f'{{"keywords": "{keywords}"}}'

                    example = {
                        "messages": [
                            {"role": "user", "content": prompt},
                            {"role": "assistant", "content": expected_response}
                        ]
                    }
                    examples.append(example)

            # Process negative examples from trash
            for product_name, rejected_keywords in trash_data.items():
                if product_name in keywords_data:
                    correct_keywords = keywords_data[product_name]
                    if correct_keywords:
                        product_json = f'{{"name": "{product_name}", "description": "", "short_description": "", "url": ""}}'

                        if platform == 'Google':
                            prompt = f"""I humbly request your assistance in generating keywords for a product. Please help me create relevant search keywords.

Product information:
{product_json}

I respectfully ask you to:
1. Search the internet for similar products and current market trends
2. Check pincesobchod.cz for table tennis product terminology and keywords
3. Analyze the product information thoroughly
4. Generate exactly 5 relevant keywords in {target_language}
5. Keywords should be suitable for Google advertising
6. Draw inspiration from existing keywords in memory for consistency
7. Use current market terminology and popular search terms in {target_language}
8. Use proper table tennis terminology in {target_language} (e.g., "rubber" = "potah", "blade" = "dřevo", not literal translations)
9. Return the result as JSON with the property "keywords"
10. Format as a single string with keywords separated by commas

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
5. Generate exactly 2 relevant keywords in {target_language}
6. Keywords should be suitable for Zbozi.cz platform
7. Preferably extract from product name but not exclusively
8. Draw inspiration from existing keywords in memory for consistency
9. Use {target_language} terminology that customers would search for
10. Use proper table tennis terminology in {target_language} (e.g., "rubber" = "potah", "blade" = "dřevo", not literal translations)
11. Return the result as JSON with the property "keywords"
12. Format as a single string with 2 keywords separated by comma

Please return your response as valid JSON only."""

                        expected_response = f'{{"keywords": "{correct_keywords}"}}'

                        example = {
                            "messages": [
                                {"role": "user", "content": prompt},
                                {"role": "assistant", "content": expected_response}
                            ]
                        }
                        examples.append(example)

        logging.info(f"Keyword generation: {len(examples)} training examples (including trash-derived examples)")
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


def main():
    """
    Main function for standalone fine-tuning script execution.
    Can be run independently or called by unifier.py as subprocess.
    """
    import argparse
    import sys

    # Setup argument parser
    parser = argparse.ArgumentParser(
        description='Fine-tune AI models for product processing tasks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run fine-tuning for all tasks
  python fine_tuning.py --language CS --memory_dir Memory

  # Run fine-tuning for specific tasks
  python fine_tuning.py --language CS --tasks name_generation brand_detection

  # Check status of existing fine-tuning jobs
  python fine_tuning.py --check_status --job_ids_file fine_tuning_jobs.json
        """
    )

    parser.add_argument('--language', type=str, default='CS',
                       help='Language code (CS or SK, default: CS)')
    parser.add_argument('--memory_dir', type=str, default=None,
                       help='Path to Memory directory with training data')
    parser.add_argument('--trash_dir', type=str, default=None,
                       help='Path to Trash directory with negative examples')
    parser.add_argument('--tasks', nargs='+', default=None,
                       help='Specific tasks to fine-tune (default: all tasks)')
    parser.add_argument('--check_status', action='store_true',
                       help='Check status of existing fine-tuning jobs')
    parser.add_argument('--job_ids_file', type=str, default='fine_tuning_jobs.json',
                       help='File to store/load job IDs (default: fine_tuning_jobs.json)')
    parser.add_argument('--output_dir', type=str, default=None,
                       help='Directory for training files (default: script_dir/training_data)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Get script directory
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Set default memory directory
    if args.memory_dir is None:
        args.memory_dir = os.path.join(script_dir, 'Memory')

    # Set default output directory
    if args.output_dir is None:
        args.output_dir = os.path.join(script_dir, 'training_data')

    ensure_directory_exists(args.output_dir)

    # Check status mode
    if args.check_status:
        logging.info("Checking fine-tuning job status...")
        job_ids_path = os.path.join(script_dir, args.job_ids_file)

        if not os.path.exists(job_ids_path):
            logging.error(f"Job IDs file not found: {job_ids_path}")
            sys.exit(1)

        job_ids = load_json_file(job_ids_path)
        if not job_ids:
            logging.error("No job IDs found in file")
            sys.exit(1)

        # Create manager and check status
        manager = FineTuningManager(language=args.language, trash_dir=args.trash_dir)
        status_report = manager.check_fine_tuning_status(job_ids, script_dir)

        logging.info("\n=== Fine-tuning Status Report ===")
        for task_type, status in status_report.items():
            logging.info(f"{task_type}: {status}")

        sys.exit(0)

    # Load memory data
    logging.info(f"Loading memory data from: {args.memory_dir}")
    memory_data = {}

    try:
        # Load all memory CSV files
        memory_files = [
            f'BrandMemory_{args.language}.csv',
            f'CategoryMemory_{args.language}.csv',
            f'NameMemory_{args.language}.csv',
            f'ProductBrandMemory_{args.language}.csv',
            f'ProductTypeMemory_{args.language}.csv',
            f'KeywordsGoogle_{args.language}.csv',
            f'KeywordsZbozi_{args.language}.csv'
        ]

        for filename in memory_files:
            filepath = os.path.join(args.memory_dir, filename)
            if os.path.exists(filepath):
                memory_key = filename.replace(f'_{args.language}.csv', '')
                memory_data[memory_key] = {}

                with open(filepath, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    header = next(reader, None)
                    for row in reader:
                        if len(row) >= 2:
                            memory_data[memory_key][row[0]] = row[1]

                logging.info(f"Loaded {len(memory_data[memory_key])} entries from {filename}")
            else:
                logging.warning(f"Memory file not found: {filepath}")

    except Exception as e:
        logging.error(f"Error loading memory data: {str(e)}", exc_info=True)
        sys.exit(1)

    # Create fine-tuning manager
    logging.info("Initializing fine-tuning manager...")
    manager = FineTuningManager(
        memory_data=memory_data,
        language=args.language,
        trash_dir=args.trash_dir
    )

    # Determine which tasks to process
    if args.tasks:
        tasks_to_process = {k: v for k, v in manager.task_types.items() if k in args.tasks}
        if not tasks_to_process:
            logging.error(f"No valid tasks found. Available tasks: {list(manager.task_types.keys())}")
            sys.exit(1)
    else:
        tasks_to_process = manager.task_types

    logging.info(f"Processing {len(tasks_to_process)} tasks: {list(tasks_to_process.keys())}")

    # Prepare training data and create jobs
    job_ids = {}

    for task_type, task_config in tasks_to_process.items():
        try:
            logging.info(f"\n=== Processing task: {task_type} ===")

            # Prepare training data
            training_data = manager.prepare_training_data(task_type)
            if not training_data:
                logging.warning(f"No training data generated for {task_type}")
                continue

            logging.info(f"Generated {len(training_data)} training examples")

            # Save training file
            training_filename = f"{task_type}_training_{args.language}.jsonl"
            training_filepath = os.path.join(args.output_dir, training_filename)
            save_jsonl_file(training_filepath, training_data)
            logging.info(f"Saved training data to: {training_filepath}")

            # Upload training file
            file_id = manager.upload_training_file(training_filepath)
            if not file_id:
                logging.error(f"Failed to upload training file for {task_type}")
                continue

            logging.info(f"Uploaded training file: {file_id}")

            # Create fine-tuning job
            job_id = manager.create_fine_tuning_job(
                task_type=task_type,
                training_file_id=file_id
            )

            if job_id:
                job_ids[task_type] = job_id
                logging.info(f"Created fine-tuning job: {job_id}")
            else:
                logging.error(f"Failed to create fine-tuning job for {task_type}")

        except Exception as e:
            logging.error(f"Error processing task {task_type}: {str(e)}", exc_info=True)
            continue

    # Save job IDs
    if job_ids:
        job_ids_path = os.path.join(script_dir, args.job_ids_file)
        save_json_file(job_ids_path, job_ids)
        logging.info(f"\n=== Fine-tuning jobs created ===")
        logging.info(f"Job IDs saved to: {job_ids_path}")
        for task_type, job_id in job_ids.items():
            logging.info(f"{task_type}: {job_id}")
        logging.info("\nUse --check_status to monitor job progress")
    else:
        logging.warning("No fine-tuning jobs were created")
        sys.exit(1)


if __name__ == '__main__':
    main()
