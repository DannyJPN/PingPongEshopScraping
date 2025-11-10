"""
Specific OpenAI module for unifier operations.

This module contains specific methods that call generic OpenAI methods
with concrete data for unifier operations. All prompts are in English
and use humble requests with explicit JSON return format.
"""

import json
import logging
import random
from typing import Dict, Any, Optional, List
from unifierlib.openai_client import OpenAIClient
from unifierlib.downloaded_product import DownloadedProduct


class OpenAIUnifier:
    """
    Specific OpenAI client for unifier operations.
    Uses humble English prompts and always expects JSON responses.
    """

    def __init__(self, use_fine_tuned_models: bool = False, fine_tuned_models: Optional[Dict[str, str]] = None,
                 supported_languages_data: Optional[list] = None):
        """Initialize with generic OpenAI client."""
        self.client = OpenAIClient(use_fine_tuned_models, fine_tuned_models)
        self.supported_languages_data = supported_languages_data

    def _create_system_prompt(self, task_type: str, language: str, supported_languages_data: list = None) -> str:
        """Create system prompt with expert role and language requirements."""
        from unifierlib.memory_manager import get_language_name
        target_language = get_language_name(language, supported_languages_data)

        system_prompts = {
            'category_mapping': f"""You are an expert e-commerce product categorization specialist with deep knowledge of table tennis equipment and online marketplace category structures. Your expertise includes understanding product taxonomies across platforms like Heureka, Glami, Google Shopping, and Zbozi.

Your task is to map product categories accurately while ensuring proper translation to {target_language} when required. You have extensive knowledge of table tennis terminology and how different platforms organize their category hierarchies.""",

            'brand_detection': f"""You are an expert table tennis equipment specialist with comprehensive knowledge of all major and minor table tennis brands worldwide. Your expertise includes brand recognition, manufacturer identification, and understanding of brand naming conventions in the table tennis industry.

Your task is to accurately identify product brands while ensuring proper translation to {target_language} when required. You understand brand variations, subsidiaries, and regional naming differences.""",

            'product_analysis': f"""You are an expert table tennis product analyst with deep knowledge of equipment specifications, product naming conventions, and market terminology. Your expertise spans all categories of table tennis equipment including rubbers, blades, balls, paddles, and accessories.

Your task is to analyze product information and extract accurate details while ensuring proper translation to {target_language} when required. You understand technical specifications and industry-standard terminology.""",

            'keyword_generation': f"""You are an expert digital marketing specialist focused on table tennis equipment with deep understanding of search engine optimization and e-commerce platform keyword strategies. Your expertise includes keyword research, search behavior analysis, and platform-specific optimization.

Your task is to generate relevant keywords while ensuring proper translation to {target_language} when required. You understand how customers search for table tennis products and platform-specific keyword requirements.""",

            'translation': f"""You are an expert translator specializing in table tennis equipment and e-commerce content with deep knowledge of technical terminology and marketing language. Your expertise includes preserving technical accuracy while ensuring natural language flow.

CRITICAL: You must prioritize table tennis slang and industry terminology over literal translations. Table tennis has its own specialized vocabulary that must be preserved. For example:
- "rubber" = "potah" (NOT "guma")
- "blade" = "dřevo" (NOT "čepel")
- "paddle/racket" = "pálka"
- "spin" = "rotace" or "točení"
- "speed" = "rychlost"
- "control" = "kontrola"
- "sponge" = "houba"
- "topsheet" = "povrch"

Your task is to translate content accurately to {target_language} using proper table tennis slang and terminology while maintaining HTML formatting. Always use the established table tennis vocabulary rather than literal dictionary translations.""",

            'name_generation': f"""You are an expert table tennis product naming specialist with comprehensive knowledge of industry naming conventions, brand structures, and product categorization. Your expertise includes understanding how products are named across different manufacturers and markets.

CRITICAL: Use table tennis slang and industry terminology, not literal translations. Examples:
- "rubber" = "potah" (NOT "guma")
- "blade" = "dřevo" (NOT "čepel")
- "paddle/racket" = "pálka"

Your task is to analyze and structure product names while ensuring proper translation to {target_language} using correct table tennis slang and terminology. You understand the distinction between product types, brands, and models in the table tennis industry."""
        }

        return system_prompts.get(task_type, f"""You are an expert assistant specializing in table tennis equipment and e-commerce operations.

CRITICAL: Always use table tennis slang and industry terminology, not literal translations. Examples:
- "rubber" = "potah" (NOT "guma")
- "blade" = "dřevo" (NOT "čepel")
- "paddle/racket" = "pálka"

Your task requires accurate analysis and proper translation to {target_language} using correct table tennis slang and terminology when needed.""")

    def find_category(self, product: DownloadedProduct, category_list: List[str], language: str = 'CS', heuristic_info: str = "") -> Optional[str]:
        """
        Find category for product using OpenAI.

        Args:
            product (DownloadedProduct): Product to categorize
            category_list (List[str]): List of available categories
            language (str): Target language code
            heuristic_info (str): Information about heuristic extraction results

        Returns:
            Optional[str]: Selected category or None if error
        """
        from unifierlib.memory_manager import get_language_name
        target_language = get_language_name(language, self.supported_languages_data)

        product_json = json.dumps({
            'name': product.name,
            'description': product.description,
            'short_description': product.short_description,
            'url': product.url
        }, ensure_ascii=False)

        categories_text = '\n'.join([f"- {cat}" for cat in category_list])

        system_prompt = self._create_system_prompt('category_mapping', language)

        # Add heuristic info to the prompt if available
        heuristic_section = f"\n\n{heuristic_info}" if heuristic_info else ""

        user_prompt = f"""I humbly request your assistance in categorizing a product. Please help me select the most appropriate category from the provided list.

Product information:
{product_json}{heuristic_section}

Available categories:
{categories_text}

I kindly ask you to:
1. Search the internet for similar products to understand their categorization
2. Check pincesobchod.cz for table tennis product categories
3. Analyze the product information carefully
4. Select EXACTLY ONE category from the list above
5. The category must be selected strictly from the provided list
6. If the selected category is not in {target_language}, translate it to {target_language} using proper table tennis slang and terminology (e.g., "rubber" = "potah" NOT "guma", "blade" = "dřevo" NOT "čepel")
7. Use your knowledge of current market categorization standards
8. Return the result as JSON with the property "category"

Please return your response as valid JSON only."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.json_completion(messages, task_type='category_mapping', max_tokens=100)

        if response and 'category' in response:
            selected_category = response['category']
            if selected_category in category_list:
                return selected_category
            else:
                logging.warning(f"OpenAI returned category not in list: {selected_category}")
                return None

        return None

    def find_brand(self, product: DownloadedProduct, brand_list: List[str], language: str = 'CS', heuristic_info: str = "") -> Optional[str]:
        """
        Find brand for product using OpenAI.

        Args:
            product (DownloadedProduct): Product to analyze
            brand_list (List[str]): List of available brands
            language (str): Target language code
            heuristic_info (str): Information about heuristic extraction results

        Returns:
            Optional[str]: Selected brand or None if error
        """
        from unifierlib.memory_manager import get_language_name
        target_language = get_language_name(language, self.supported_languages_data)

        product_json = json.dumps({
            'name': product.name,
            'description': product.description,
            'short_description': product.short_description,
            'url': product.url
        }, ensure_ascii=False)

        brands_text = '\n'.join([f"- {brand}" for brand in brand_list])

        system_prompt = self._create_system_prompt('brand_detection', language)

        # Add heuristic info to the prompt if available
        heuristic_section = f"\n\n{heuristic_info}" if heuristic_info else ""

        user_prompt = f"""I humbly request your help in identifying the brand of a product. Please assist me in selecting the correct brand from the provided list.

Product information:
{product_json}{heuristic_section}

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

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.json_completion(messages, task_type='brand_detection', max_tokens=50)

        if response and 'brand' in response:
            selected_brand = response['brand']
            if selected_brand in brand_list:
                return selected_brand
            else:
                logging.warning(f"OpenAI returned brand not in list: {selected_brand}")
                return None

        return None

    def _get_diverse_memory_items(self, memory_content: Dict[str, str], max_items: int = 1000) -> List[str]:
        """
        Selects a diverse subset of memory items, aiming to represent all unique values
        if possible within max_items.

        Args:
            memory_content (Dict[str, str]): The memory content dictionary.
            max_items (int): Maximum number of items to return.

        Returns:
            List[str]: A list of formatted memory items.
        """
        if not memory_content:
            return []

        # Step 1: Collect one (key, value) pair for each unique value.
        # The first encountered (key, value) for a unique value is taken.
        unique_value_representatives_map = {}  # Maps value -> (key, value)
        for k, v in memory_content.items():
            if v not in unique_value_representatives_map:
                unique_value_representatives_map[v] = (k, v)

        items_representing_all_uniques = list(unique_value_representatives_map.values())

        formatted_unique_items = [f"- {k} -> {v}" for k, v in items_representing_all_uniques]

        # Step 2: Decide what to return based on counts
        if len(formatted_unique_items) >= max_items:
            # If we have more (or equal) unique items than max_items,
            # select a random subset of these items.
            random.shuffle(formatted_unique_items)
            return formatted_unique_items[:max_items]
        else:
            # All unique values are included, and we have space for more items.
            result_items = formatted_unique_items

            # Collect all other items from memory_content that are not yet included.
            # A set of (k,v) pairs already included for efficient lookup.
            selected_pairs_set = set(items_representing_all_uniques)

            additional_items_candidates_formatted = []
            for k, v in memory_content.items():
                if (k, v) not in selected_pairs_set:
                    additional_items_candidates_formatted.append(f"- {k} -> {v}")

            random.shuffle(additional_items_candidates_formatted)

            num_needed = max_items - len(result_items)
            result_items.extend(additional_items_candidates_formatted[:num_needed])

            return result_items

    def generate_google_keywords(self, product: DownloadedProduct, memory_content: Dict[str, str] = None, language: str = 'CS') -> Optional[str]:
        """Generate Google keywords for product using OpenAI with memory content."""
        from unifierlib.memory_manager import get_language_name
        target_language = get_language_name(language, self.supported_languages_data)

        product_json = json.dumps({
            'name': product.name,
            'description': product.description,
            'short_description': product.short_description,
            'url': product.url
        }, ensure_ascii=False)

        # Include memory content in prompt if available
        memory_section = ""
        if memory_content:
            memory_items = self._get_diverse_memory_items(memory_content)
            if memory_items: # check if memory_items is not empty
                memory_section = f"""

Existing Google keywords from memory:
{chr(10).join(memory_items)}

Please draw inspiration from these existing keywords to ensure consistency and avoid duplication."""

        system_prompt = self._create_system_prompt('keyword_generation', language)

        user_prompt = f"""I humbly request your assistance in generating keywords for a product. Please help me create relevant search keywords.

Product information:
{product_json}{memory_section}

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

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.json_completion(messages, task_type='keyword_generation', max_tokens=200)

        if response and 'keywords' in response:
            return response['keywords']

        return None

    def generate_zbozi_keywords(self, product: DownloadedProduct, memory_content: Dict[str, str] = None, language: str = 'CS') -> Optional[str]:
        """Generate Zbozi keywords for product using OpenAI with memory content."""
        from unifierlib.memory_manager import get_language_name
        target_language = get_language_name(language, self.supported_languages_data)

        product_json = json.dumps({
            'name': product.name,
            'description': product.description,
            'short_description': product.short_description,
            'url': product.url
        }, ensure_ascii=False)

        # Include memory content in prompt if available
        memory_section = ""
        if memory_content:
            memory_items = self._get_diverse_memory_items(memory_content)
            if memory_items: # check if memory_items is not empty
                memory_section = f"""

Existing Zbozi keywords from memory:
{chr(10).join(memory_items)}

Please draw inspiration from these existing keywords to ensure consistency and avoid duplication."""

        system_prompt = self._create_system_prompt('keyword_generation', language)

        user_prompt = f"""I humbly request your help in generating keywords for a Czech shopping platform. Please assist me in creating relevant keywords.

Product information:
{product_json}{memory_section}

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

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.json_completion(messages, task_type='keyword_generation', max_tokens=150)

        if response and 'keywords' in response:
            return response['keywords']

        return None

    def standardize_variant_name(self, variant_name: str, language: str, memory_content: Dict[str, str] = None) -> Optional[str]:
        """Standardize variant name using OpenAI with memory content."""
        from unifierlib.memory_manager import get_language_name
        target_language = get_language_name(language)

        # Include memory content in prompt if available
        memory_section = ""
        if memory_content:
            memory_items = self._get_diverse_memory_items(memory_content)
            if memory_items: # check if memory_items is not empty
                memory_section = f"""

Existing standardized variant names from memory:
{chr(10).join(memory_items)}

Please draw inspiration from these existing standardizations to ensure consistency."""

        system_prompt = self._create_system_prompt('translation', language)

        user_prompt = f"""I humbly request your assistance in standardizing a table tennis product variant name. Please help me create a consistent variant name.

Original variant name: {variant_name}{memory_section}

I respectfully ask you to:
1. Search the internet for standard table tennis product variant terminology
2. Check pincesobchod.cz for how they categorize table tennis product variants
3. If the text is not in {target_language}, translate it to {target_language} using proper table tennis terminology (e.g., "rubber" = "potah", "blade" = "dřevo", not literal translations)
4. Use common terminology for product variants (e.g., "Color", "Thickness", "Hardness", "Size")
5. Keep it concise and clear
6. Preserve table tennis terminology where applicable
7. Draw inspiration from existing standardizations in memory to ensure consistency
8. Use industry-standard terminology that customers would recognize
9. Return the result as JSON with the property "standardized_name"

Please return your response as valid JSON only."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.json_completion(messages, task_type='translation', max_tokens=100)

        if response and 'standardized_name' in response:
            return response['standardized_name']

        return None

    def standardize_variant_value(self, variant_value: str, language: str, memory_content: Dict[str, str] = None) -> Optional[str]:
        """Standardize variant value using OpenAI with memory content."""
        from unifierlib.memory_manager import get_language_name
        target_language = get_language_name(language)

        # Include memory content in prompt if available
        memory_section = ""
        if memory_content:
            memory_items = self._get_diverse_memory_items(memory_content)
            if memory_items: # check if memory_items is not empty
                memory_section = f"""

Existing standardized variant values from memory:
{chr(10).join(memory_items)}

Please draw inspiration from these existing standardizations to ensure consistency."""

        system_prompt = self._create_system_prompt('translation', language)

        user_prompt = f"""I humbly request your help in standardizing a table tennis product variant value. Please assist me in creating a consistent variant value.

Original variant value: {variant_value}{memory_section}

I respectfully ask you to:
1. Search the internet for standard table tennis product specifications and terminology
2. Check pincesobchod.cz for how they specify table tennis product variant values
3. If the text is not in {target_language}, translate it to {target_language} using proper table tennis terminology (e.g., "rubber" = "potah", "blade" = "dřevo", not literal translations)
4. Use common terminology and units (e.g., "mm" for thickness, standard color names)
5. Keep it concise and clear
6. Preserve table tennis-specific terms where applicable
7. Draw inspiration from existing standardizations in memory to ensure consistency
8. Use industry-standard units and terminology that customers would recognize
9. Return the result as JSON with the property "standardized_value"

Please return your response as valid JSON only."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.json_completion(messages, task_type='translation', max_tokens=100)

        if response and 'standardized_value' in response:
            return response['standardized_value']

        return None

    def suggest_category_mapping(self, category: str, platform: str, language: str, memory_content: Dict[str, str] = None) -> Optional[str]:
        """Suggest category mapping for specific platform using OpenAI with memory content."""
        from unifierlib.memory_manager import get_language_name
        target_language = get_language_name(language)

        # Include memory content in prompt if available
        memory_section = ""
        if memory_content:
            memory_items = self._get_diverse_memory_items(memory_content)
            if memory_items: # check if memory_items is not empty
                memory_section = f"""

Existing {platform} category mappings from memory:
{chr(10).join(memory_items)}

Please draw inspiration from these existing mappings to ensure consistency."""

        # Get platform-specific URL for research
        platform_urls = {
            'Heureka': 'heureka.cz',
            'Glami': 'glami.cz',
            'Google': 'google.com/shopping',
            'Zbozi': 'zbozi.cz'
        }
        platform_url = platform_urls.get(platform, f"{platform.lower()}.com")

        system_prompt = self._create_system_prompt('category_mapping', language)

        user_prompt = f"""I humbly request your assistance in mapping a product category to {platform} platform category. Please help me find the most appropriate mapping.

Original category: {category}
Target platform: {platform}{memory_section}

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

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.json_completion(messages, task_type='category_mapping', max_tokens=200)

        if response and 'mapping' in response:
            return response['mapping']

        return None

    def translate_and_validate_description(self, description: str, language: str) -> Optional[str]:
        """Translate and validate description using OpenAI (not generate)."""
        # Remove external links and replace with their content
        if description:
            import re
            # Remove <a> tags that link to external sites and replace with inner text
            description = re.sub(r'<a[^>]*href=["\'][^"\']*[^"\']*["\'][^>]*>(.*?)</a>', r'\1', description)

        from unifierlib.memory_manager import get_language_name
        target_language = get_language_name(language)

        system_prompt = self._create_system_prompt('translation', language)

        user_prompt = f"""I humbly request your assistance in translating and validating a product description for table tennis equipment. Please help me translate the following text while preserving table tennis terminology.

Original description: {description}

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

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.json_completion(messages, task_type='translation', max_tokens=16384)

        if response and 'description' in response:
            return response['description']

        return None

    def generate_product_name(self, product: DownloadedProduct, language: str) -> Optional[Dict[str, str]]:
        """Generate product name components using OpenAI."""
        product_json = json.dumps({
            'name': product.name,
            'description': product.description,
            'short_description': product.short_description,
            'url': product.url
        }, ensure_ascii=False)

        from unifierlib.memory_manager import get_language_name
        target_language = get_language_name(language, self.supported_languages_data)

        system_prompt = self._create_system_prompt('name_generation', language)

        user_prompt = f"""I humbly request your assistance in analyzing a table tennis product name. Please help me break down the product information into three distinct, non-overlapping components.

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

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.json_completion(messages, task_type='name_generation', max_tokens=300)

        if response and all(key in response for key in ['model', 'type', 'brand']):
            return response

        return None

    def translate_and_validate_short_description(self, short_description: str, language: str, description: str = "") -> Optional[str]:
        """Translate and validate short description using OpenAI, or generate from description if short_description is empty."""
        from unifierlib.memory_manager import get_language_name
        target_language = get_language_name(language, self.supported_languages_data)

        system_prompt = self._create_system_prompt('translation', language)

        # If short description is empty but description is available, generate from description
        if not short_description or not short_description.strip():
            if description and description.strip():
                user_prompt = f"""I humbly request your help in generating a short product description for table tennis equipment from the full description. Please assist me in creating a proper short description.

Full product description: {description}

I respectfully ask you to:
1. Create a concise short description based on the full description
2. If the text is not in {target_language}, translate it to {target_language} using proper table tennis SLANG and terminology - prioritize table tennis industry terms over literal translations:
   • "rubber" = "potah" (NEVER "guma")
   • "blade" = "dřevo" (NEVER "čepel")
   • "paddle/racket" = "pálka"
3. Maximum 150 characters
4. Focus on the most important product features and benefits
5. Return plain text without HTML
6. Return the result as JSON with the property "shortdesc"

Please return your response as valid JSON only."""
            else:
                return None
        else:
            # Original logic for translating existing short description
            user_prompt = f"""I humbly request your help in translating and validating a short product description for table tennis equipment. Please assist me in creating a proper short description.

Original short description: {short_description}

I respectfully ask you to:
1. If the text is not in {target_language}, translate it to {target_language} using proper table tennis SLANG and terminology - prioritize table tennis industry terms over literal translations:
   • "rubber" = "potah" (NEVER "guma")
   • "blade" = "dřevo" (NEVER "čepel")
   • "paddle/racket" = "pálka"
2. Maximum 150 characters
3. Keep the original meaning intact
4. Return plain text without HTML
5. Return the result as JSON with the property "shortdesc"

Please return your response as valid JSON only."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.json_completion(messages, task_type='translation', max_tokens=200)

        if response and 'shortdesc' in response:
            return response['shortdesc']

        return None

    def get_product_type(self, product: DownloadedProduct, language: str, heuristic_info: str = "") -> Optional[str]:
        """Get product type using OpenAI."""
        product_json = json.dumps({
            'name': product.name,
            'description': product.description,
            'short_description': product.short_description,
            'url': product.url
        }, ensure_ascii=False)

        from unifierlib.memory_manager import get_language_name
        target_language = get_language_name(language)

        system_prompt = self._create_system_prompt('product_analysis', language)

        # Add heuristic info to the prompt if available
        heuristic_section = f"\n\n{heuristic_info}" if heuristic_info else ""

        user_prompt = f"""I humbly request your assistance in identifying the product type. Please help me determine what type of product this is.

Product information:
{product_json}{heuristic_section}

I respectfully ask you to:
1. Analyze the product information carefully
2. Determine the general product type (e.g., "Laptop", "Shirt", "Ball", "Racket")
3. Translate the product type to {target_language} using proper table tennis terminology (e.g., "rubber" = "potah", "blade" = "dřevo", not literal translations)
4. Keep it concise and general (not specific model)
5. Use {target_language} language for the type
6. Return the result as JSON with the property "type"
7. Always begin the response with capital letter 

Please return your response as valid JSON only."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.json_completion(messages, task_type='product_analysis', max_tokens=50)

        if response and 'type' in response:
            return response['type']

        return None

    def get_product_brand(self, product: DownloadedProduct, brand_list: List[str], heuristic_info: str = "") -> Optional[str]:
        """Get product brand using OpenAI (similar to find_brand but for name composition)."""
        return self.find_brand(product, brand_list, 'CS', heuristic_info)

    def get_product_model(self, product: DownloadedProduct, language: str, heuristic_info: str = "") -> Optional[str]:
        """Get product model using OpenAI."""
        product_json = json.dumps({
            'name': product.name,
            'description': product.description,
            'short_description': product.short_description,
            'url': product.url
        }, ensure_ascii=False)

        from unifierlib.memory_manager import get_language_name
        target_language = get_language_name(language, self.supported_languages_data)

        system_prompt = self._create_system_prompt('product_analysis', language)

        # Add heuristic info to the prompt if available
        heuristic_section = f"\n\n{heuristic_info}" if heuristic_info else ""

        user_prompt = f"""I humbly request your help in identifying the product model. Please assist me in determining the specific model of this product.

Product information:
{product_json}{heuristic_section}

I respectfully ask you to:
1. Analyze the product information thoroughly
2. Extract the specific model name/number (e.g., "ROG Strix", "Air Max 90", "Pro V1")
3. If the model name is not in {target_language}, translate descriptive parts to {target_language} using proper table tennis terminology (e.g., "rubber" = "potah", "blade" = "dřevo", not literal translations)
4. Keep brand-specific model names in their original form when appropriate
5. Keep it concise and specific to the model
6. Return the result as JSON with the property "model"

Please return your response as valid JSON only."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.json_completion(messages, task_type='product_analysis', max_tokens=150)

        if response and 'model' in response:
            return response['model']

        return None

    def standardize_stock_status(self, stock_status: str, language: str, memory_content: Dict[str, str] = None) -> Optional[str]:
        """Standardize stock status using OpenAI with memory content."""
        from unifierlib.memory_manager import get_language_name
        target_language = get_language_name(language)

        # Include memory content in prompt if available
        memory_section = ""
        if memory_content:
            memory_items = self._get_diverse_memory_items(memory_content)
            if memory_items: # check if memory_items is not empty
                memory_section = f"""

Existing stock status translations from memory:
{chr(10).join(memory_items)}

Please draw inspiration from these existing translations to ensure consistency."""

        system_prompt = self._create_system_prompt('translation', language)

        user_prompt = f"""I humbly request your assistance in standardizing and translating a stock status for table tennis equipment. Please help me translate and standardize the following stock status.

Original stock status: {stock_status}

I respectfully ask you to:
1. If the text is not in {target_language}, translate it to {target_language} using proper terminology
2. Standardize the stock status to common e-commerce terms
3. Use consistent terminology for stock availability (e.g., "skladem", "není skladem", "na objednávku")
4. Keep the meaning clear and customer-friendly
5. Draw inspiration from existing translations in memory for consistency
6. Return the result as JSON with the property "standardized_value"

Please return your response as valid JSON only."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.client.json_completion(messages, task_type='translation', max_tokens=100)

        if response and 'standardized_value' in response:
            return response['standardized_value']

        return None
