"""
Product merger module for combining duplicate RepairedProducts.

This module handles merging of RepairedProducts that have the same name.
Products are considered duplicates if they have the same 'name' property
(after AI/user processing, not original_name).

Merging rules:
- All properties except variants: combine values with '|' separator, remove duplicates
- Variants: merge arrays, remove duplicate variants
- Variant is duplicate if all properties match (prices, key_value_pairs, stock_status)
- For key_value_pairs, order doesn't matter when checking duplicates
"""

import logging
import os
from typing import List, Dict, Any, Optional
from collections import defaultdict, OrderedDict
import json
from tqdm import tqdm
from .repaired_product import RepairedProduct
from .variant import Variant
from .openai_unifier import OpenAIUnifier
from shared.file_ops import load_csv_file, save_csv_file
from .constants import (
    PRODUCT_TYPE_MEMORY_PREFIX,
    PRODUCT_BRAND_MEMORY_PREFIX,
    PRODUCT_MODEL_MEMORY_PREFIX,
    CATEGORY_MEMORY_PREFIX,
    NAME_MEMORY_PREFIX,
    DESC_MEMORY_PREFIX,
    SHORT_DESC_MEMORY_PREFIX,
    KEYWORDS_GOOGLE_PREFIX,
    KEYWORDS_ZBOZI_PREFIX,
    CATEGORY_ID_LIST
)


class ProductMerger:
    """Handles merging of duplicate RepairedProducts."""

    # Maximum number of memory files to keep in cache (LRU eviction)
    MAX_CACHE_SIZE = 10

    def __init__(self, language: str, memory_dir: str, confirm_ai_results: bool = False,
                 skip_ai: bool = False, use_fine_tuned_models: bool = False,
                 fine_tuned_models: Optional[Dict[str, str]] = None,
                 supported_languages_data: Optional[list] = None):
        """
        Initialize the ProductMerger.

        Args:
            language: Language code (e.g., 'CS', 'SK')
            memory_dir: Path to Memory directory
            confirm_ai_results: Whether to automatically confirm AI results (default: False)
            skip_ai: Whether to skip AI processing (default: False)
            use_fine_tuned_models: Whether to use fine-tuned models (default: False)
            fine_tuned_models: Dictionary mapping task types to model IDs
            supported_languages_data: Pre-loaded supported languages data
        """
        self.language = language
        self.memory_dir = memory_dir
        self.trash_dir = os.path.join(os.path.dirname(memory_dir), "Trash")
        self.confirm_ai_results = confirm_ai_results
        self.skip_ai = skip_ai
        # LRU cache: OrderedDict maintains insertion order, we'll move accessed items to end
        self.memory_cache: OrderedDict[str, Dict[str, str]] = OrderedDict()
        self.memory_dirty = set()  # Track which memory files have been modified

        # Initialize OpenAI only if AI is not skipped
        self.openai = None
        if not skip_ai:
            try:
                self.openai = OpenAIUnifier(use_fine_tuned_models, fine_tuned_models, supported_languages_data)
                logging.info("OpenAI integration enabled for merge conflict resolution")
            except (ValueError, ImportError) as e:
                logging.warning(f"OpenAI not available for merge conflict resolution: {str(e)}")
                self.openai = None
        else:
            logging.info("AI usage is disabled for merge conflict resolution (--SkipAI flag)")
    
    def merge_products(self, repaired_products: List[RepairedProduct]) -> List[RepairedProduct]:
        """
        Merge duplicate RepairedProducts based on their name.
        
        Args:
            repaired_products: List of RepairedProducts to merge
            
        Returns:
            List of merged RepairedProducts with duplicates combined
        """
        if not repaired_products:
            return []
        
        logging.info(f"Starting product merging for {len(repaired_products)} products")
        
        # Group products by name
        products_by_name = defaultdict(list)
        for product in repaired_products:
            if product.name:
                products_by_name[product.name.strip()].append(product)
            else:
                # Products without name are kept as-is
                logging.warning(f"Product without name found: {product.original_name}")
                products_by_name[f"__unnamed_{id(product)}"].append(product)
        
        merged_products = []

        with tqdm(total=len(products_by_name), desc="Merging products", unit="product", miniters=1, mininterval=0.01) as pbar:
            for name, products in products_by_name.items():
                if len(products) == 1:
                    # No duplicates, keep as-is
                    merged_products.append(products[0])
                else:
                    # Merge duplicates
                    logging.debug(f"Merging {len(products)} products with name: {name}")
                    merged_product = self._merge_product_group(products)
                    merged_products.append(merged_product)
                pbar.update(1)

        # Save all modified memory files (batch save for efficiency)
        self.save_all_dirty_memory_files()

        logging.info(f"Product merging completed. {len(repaired_products)} -> {len(merged_products)} products")
        return merged_products
    
    def _merge_product_group(self, products: List[RepairedProduct]) -> RepairedProduct:
        """
        Merge a group of products with the same name.

        Args:
            products: List of products to merge (all have same name)

        Returns:
            Single merged RepairedProduct

        Raises:
            ValueError: If string properties have conflicting values that cannot be merged
        """
        if not products:
            raise ValueError("Cannot merge empty product list")

        if len(products) == 1:
            return products[0]

        # Log products being merged for debugging
        logging.info(f"Merging {len(products)} products with name: {products[0].name}")
        for i, product in enumerate(products):
            logging.debug(f"  Product {i+1}: original_name='{product.original_name}', "
                         f"brand='{product.brand}', price='{product.price}'")

        # Use first product as base
        base_product = products[0]

        # Merge all string properties
        # Note: If any property has conflicting values, an exception will be raised
        # User must resolve conflicts manually in the source data
        merged_data = {
            'original_name': self._merge_string_values([p.original_name for p in products],
                                                       'original_name', products, allow_multiple=True),
            'name': base_product.name,  # Name should be the same for all
            'type': self._merge_string_values([p.type for p in products],
                                              'type', products),
            'model': self._merge_string_values([p.model for p in products],
                                               'model', products),
            'category': self._merge_string_values([p.category for p in products],
                                                  'category', products),
            'brand': self._merge_string_values([p.brand for p in products],
                                               'brand', products),
            # category_ids is derived from category, will be recalculated after merge
            'category_ids': '',  # Will be set by _recalculate_category_ids()
            'code': self._merge_string_values([p.code for p in products],
                                              'code', products),
            'desc': self._merge_string_values([p.desc for p in products],
                                              'desc', products),
            'glami_category': self._merge_string_values([p.glami_category for p in products],
                                                        'glami_category', products),
            'google_category': self._merge_string_values([p.google_category for p in products],
                                                         'google_category', products),
            'google_keywords': self._merge_string_values([p.google_keywords for p in products],
                                                         'google_keywords', products),
            'heureka_category': self._merge_string_values([p.heureka_category for p in products],
                                                          'heureka_category', products),
            'price': self._merge_prices([p.price for p in products]),
            'price_standard': self._merge_prices([p.price_standard for p in products]),
            'shortdesc': self._merge_string_values([p.shortdesc for p in products],
                                                   'shortdesc', products),
                    'zbozi_category': self._merge_string_values([p.zbozi_category for p in products],
                                                        'zbozi_category', products),
            'zbozi_keywords': self._merge_string_values([p.zbozi_keywords for p in products],
                                                        'zbozi_keywords', products),
            'url': self._merge_string_values([p.url for p in products],
                                             'url', products, allow_multiple=True)
        }

        # Merge variants
        all_variants = []
        for product in products:
            if product.Variants:
                all_variants.extend(product.Variants)

        merged_variants = self._merge_variants(all_variants)
        merged_data['Variants'] = merged_variants

        # Create merged product
        merged_product = RepairedProduct()
        for key, value in merged_data.items():
            setattr(merged_product, key, value)

        # Recalculate category_ids from category (derived field)
        merged_product.category_ids = self._recalculate_category_ids(merged_product.category)

        # Update NameMemory ONLY if all three components (type, brand, model) are present
        # This ensures we don't create incomplete name compositions
        type_val = merged_data.get('type', '').strip()
        brand_val = merged_data.get('brand', '').strip()
        model_val = merged_data.get('model', '').strip()

        if type_val and brand_val and model_val:
            self._update_name_memory(products, type_val, brand_val, model_val)

        logging.debug(f"Successfully merged {len(products)} products into one: {merged_product.name}")
        return merged_product

    def _recalculate_category_ids(self, category: str) -> str:
        """
        Recalculate category_ids from category path.

        Category IDs are derived from category path by splitting on '>', reversing,
        and looking up each part in CategoryIDList.

        Args:
            category: Category path (e.g., "Potahy>Softy>Softy ALL")

        Returns:
            str: Comma-separated category IDs (e.g., "123,456,789")
        """
        if not category or not category.strip():
            return ""

        # Load CategoryIDList
        category_id_list_path = os.path.join(self.memory_dir, CATEGORY_ID_LIST)

        try:
            # Validate path
            category_id_list_path = self._validate_file_path(category_id_list_path)

            csv_data = load_csv_file(category_id_list_path)

            # Convert to dict (category_part -> ID)
            id_mapping = {}
            for row in csv_data:
                # CategoryIDList has columns like "Category" and "ID" or similar
                # Try different column name patterns
                if 'Category' in row and 'ID' in row:
                    id_mapping[row['Category']] = row['ID']
                elif 'category' in row and 'id' in row:
                    id_mapping[row['category']] = row['id']
                # Fallback: assume first two columns are category and ID
                elif len(row) >= 2:
                    keys = list(row.keys())
                    id_mapping[row[keys[0]]] = row[keys[1]]

            # Split category by >, reverse, and map to IDs
            category_parts = [part.strip() for part in category.split('>')]
            category_parts.reverse()

            ids = []
            for part in category_parts:
                if part in id_mapping:
                    ids.append(str(id_mapping[part]))
                else:
                    logging.warning(f"Category part '{part}' not found in CategoryIDList, skipping")

            result = ','.join(ids)
            logging.debug(f"Recalculated category_ids: '{category}' -> '{result}'")
            return result

        except FileNotFoundError:
            logging.warning(f"CategoryIDList not found at {category_id_list_path}, cannot recalculate category_ids")
            return ""
        except Exception as e:
            logging.error(f"Error recalculating category_ids: {str(e)}", exc_info=True)
            return ""

    def _merge_string_values(self, values: List[str], field_name: str,
                             products: List[RepairedProduct], allow_multiple: bool = False) -> str:
        """
        Merge string values - asks user to resolve conflicts if multiple different values exist.

        Args:
            values: List of string values to merge
            field_name: Name of the field being merged (for error messages)
            products: Original products (for detailed error reporting)
            allow_multiple: If True, allows multiple values (for original_name field only)

        Returns:
            Single merged value (or combined with '|' if allow_multiple=True)
        """
        # Filter out None and empty values
        valid_values = [v.strip() for v in values if v and v.strip()]

        if not valid_values:
            return ""

        if len(valid_values) == 1:
            return valid_values[0]

        # Check if all values are the same
        unique_values = list(set(v.lower() for v in valid_values))

        if len(unique_values) == 1:
            # All values are the same (case-insensitive), return the first one
            return valid_values[0]

        # Multiple different values exist
        if allow_multiple:
            # For original_name, combine all unique values
            return '|'.join(sorted(set(valid_values)))

        # For all other fields, resolve conflict (AI or user)
        logging.warning(f"Conflict detected in field '{field_name}'")

        # Try AI resolution first if available
        ai_suggestion = None
        if self.openai and not self.skip_ai:
            logging.info(f"Attempting AI resolution for field '{field_name}'")
            ai_suggestion = self._resolve_conflict_with_ai(field_name, products)

        # Handle AI result based on confirm_ai_results flag
        if ai_suggestion:
            if self.confirm_ai_results:
                # Auto-confirm AI suggestion
                logging.info(f"Auto-confirming AI suggestion for '{field_name}': {ai_suggestion}")
                chosen_value = ai_suggestion
            else:
                # Show AI suggestion to user for confirmation
                logging.info(f"Showing AI suggestion to user for field '{field_name}'")
                chosen_value = self._confirm_ai_suggestion(field_name, ai_suggestion, products)
        else:
            # No AI available or AI failed - ask user directly
            logging.warning(f"AI not available for '{field_name}' - asking user to resolve")
            chosen_value = self._ask_user_for_conflict_resolution(field_name, products)

        # Update memory file for this field
        self._update_memory_for_field(field_name, products, chosen_value)

        logging.info(f"Conflict resolved for field '{field_name}': chose '{chosen_value}'")

        return chosen_value

    def _merge_prices(self, prices: List[str]) -> str:
        """
        Merge price values by selecting the highest price.

        Args:
            prices: List of price strings to merge

        Returns:
            String representation of the highest price
        """
        # Filter out None, empty values, and convert to float
        valid_prices = []
        for price in prices:
            if price and price.strip():
                try:
                    valid_prices.append(float(price))
                except (ValueError, TypeError):
                    logging.warning(f"Invalid price value: {price}")
                    continue

        if not valid_prices:
            return ""

        # Return the highest price
        max_price = max(valid_prices)
        return str(max_price)
    
    def _merge_variants(self, variants: List[Variant]) -> List[Variant]:
        """
        Merge variant lists by removing duplicates.
        
        Args:
            variants: List of all variants from all products
            
        Returns:
            List of unique variants
        """
        if not variants:
            return []
        
        unique_variants = []
        seen_variants = set()
        
        for variant in variants:
            variant_key = self._get_variant_key(variant)
            if variant_key not in seen_variants:
                unique_variants.append(variant)
                seen_variants.add(variant_key)
        
        logging.debug(f"Merged {len(variants)} variants into {len(unique_variants)} unique variants")
        return unique_variants

    def _sanitize_user_input(self, value: str, field_name: str) -> str:
        """
        Sanitize user input to prevent injection attacks and invalid data.

        Args:
            value: User input value
            field_name: Name of the field (for context-specific validation)

        Returns:
            str: Sanitized value

        Raises:
            ValueError: If input contains dangerous characters or patterns
        """
        # Strip whitespace
        value = value.strip()

        # Check max length (reasonable limit for product data)
        MAX_LENGTH = 5000
        if len(value) > MAX_LENGTH:
            raise ValueError(f"Input too long ({len(value)} chars). Maximum {MAX_LENGTH} characters allowed.")

        # Check for null bytes (can cause issues in CSV)
        if '\x00' in value:
            raise ValueError("Input contains null bytes which are not allowed.")

        # Check for CSV injection patterns (formulas)
        csv_dangerous_prefixes = ['=', '+', '-', '@', '\t', '\r']
        if any(value.startswith(prefix) for prefix in csv_dangerous_prefixes):
            raise ValueError(f"Input cannot start with {csv_dangerous_prefixes} (CSV injection prevention).")

        # Check for control characters (except newline which might be in descriptions)
        import re
        control_chars = re.findall(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', value)
        if control_chars:
            raise ValueError(f"Input contains invalid control characters.")

        # Field-specific validation
        if field_name in ['category', 'type']:
            # Category and type should not contain pipe characters (used as separator)
            if '|' in value and field_name == 'category':
                # Allow > for category paths like "Potahy>Softy>Softy ALL"
                pass
            # Check for reasonable category format
            if len(value) > 500:
                raise ValueError(f"Category/Type value too long ({len(value)} chars). Maximum 500 characters.")

        return value

    def _resolve_conflict_with_ai(self, field_name: str, products: List[RepairedProduct]) -> Optional[str]:
        """
        Use AI to resolve merge conflict by analyzing all product variants and selecting the best value.
        For Pincesobchod products, also analyzes the product page to make better decisions.

        Args:
            field_name: Name of the conflicting field
            products: List of products with conflicting values

        Returns:
            Optional[str]: AI-suggested value, or None if AI is unavailable
        """
        if not self.openai:
            return None

        try:
            # Get all unique values for this field
            values_with_context = []
            for product in products:
                value = getattr(product, field_name, '')
                if value and value.strip():
                    values_with_context.append({
                        'value': value,
                        'original_name': product.original_name,
                        'brand': product.brand,
                        'type': product.type,
                        'model': product.model,
                        'url': product.url,
                        'category': product.category
                    })

            if not values_with_context:
                return None

            # Check if any product is from Pincesobchod (domain analysis)
            pincesobchod_analysis = None
            for item in values_with_context:
                url = item.get('url', '')
                if url and 'pincesobchod' in url.lower():
                    # Fetch and analyze Pincesobchod product page
                    pincesobchod_analysis = self._analyze_pincesobchod_product(url, field_name)
                    if pincesobchod_analysis:
                        logging.info(f"Retrieved Pincesobchod analysis for conflict resolution: {url}")
                        break

            # Build AI prompt
            prompt = self._build_conflict_resolution_prompt(
                field_name, values_with_context, pincesobchod_analysis
            )

            # Call AI
            logging.info(f"Requesting AI to resolve conflict for field '{field_name}'")
            messages = [
                {"role": "system", "content": "You are an expert in e-commerce product data standardization. Your task is to analyze conflicting product field values and select the most appropriate one."},
                {"role": "user", "content": prompt}
            ]

            ai_response = self.openai.client.chat_completion(
                messages=messages,
                task_type='complex',
                temperature=0.3
            )

            if ai_response:
                # Extract the chosen value from AI response
                ai_suggestion = ai_response.strip()
                logging.info(f"AI suggested value for '{field_name}': {ai_suggestion}")
                return ai_suggestion

            return None

        except Exception as e:
            logging.error(f"Error using AI to resolve conflict: {str(e)}", exc_info=True)
            return None

    def _build_conflict_resolution_prompt(self, field_name: str,
                                          values_with_context: List[Dict[str, str]],
                                          pincesobchod_analysis: Optional[str] = None) -> str:
        """
        Build prompt for AI conflict resolution.

        Args:
            field_name: Name of the conflicting field
            values_with_context: List of values with product context
            pincesobchod_analysis: Optional analysis from Pincesobchod product page

        Returns:
            str: Formatted prompt for AI
        """
        prompt = f"""I have multiple products being merged with conflicting values for the field '{field_name}'.
I need you to select the MOST APPROPRIATE value based on the context.

Product being merged: {values_with_context[0]['original_name']}

Conflicting values:
"""

        for i, item in enumerate(values_with_context, 1):
            prompt += f"\n{i}. Value: '{item['value']}'"
            prompt += f"\n   Source: {item['original_name']}"
            if item.get('brand'):
                prompt += f"\n   Brand: {item['brand']}"
            if item.get('type'):
                prompt += f"\n   Type: {item['type']}"
            if item.get('model'):
                prompt += f"\n   Model: {item['model']}"
            if item.get('category'):
                prompt += f"\n   Category: {item['category']}"
            if item.get('url'):
                prompt += f"\n   URL: {item['url']}"
            prompt += "\n"

        if pincesobchod_analysis:
            prompt += f"\nAdditional context from Pincesobchod product page:\n{pincesobchod_analysis}\n"

        prompt += f"""\nBased on the above information, which value is most appropriate for the '{field_name}' field?

IMPORTANT: Return ONLY the exact value (without option number or explanation).
If none of the values are appropriate, you may suggest a better value, but prefer selecting from the given options.
"""

        return prompt

    def _analyze_pincesobchod_product(self, url: str, field_name: str) -> Optional[str]:
        """
        Fetch and analyze Pincesobchod product page to help with conflict resolution.

        Args:
            url: Pincesobchod product URL
            field_name: Field name being resolved (for focused analysis)

        Returns:
            Optional[str]: Analysis text, or None if unavailable
        """
        try:
            import requests
            from bs4 import BeautifulSoup

            logging.info(f"Fetching Pincesobchod product page: {url}")

            # Fetch the page
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract relevant information based on field_name
            analysis_parts = []

            # Product title
            title_elem = soup.find('h1')
            if title_elem:
                analysis_parts.append(f"Product title: {title_elem.get_text(strip=True)}")

            # Product description
            desc_elem = soup.find('div', class_='product-description') or soup.find('div', class_='description')
            if desc_elem:
                desc_text = desc_elem.get_text(strip=True)[:500]  # Limit length
                analysis_parts.append(f"Description excerpt: {desc_text}")

            # Product parameters/specifications
            params_table = soup.find('table', class_='parameters') or soup.find('div', class_='parameters')
            if params_table:
                params = []
                for row in params_table.find_all('tr')[:10]:  # Limit to first 10 parameters
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        param_name = cells[0].get_text(strip=True)
                        param_value = cells[1].get_text(strip=True)
                        params.append(f"{param_name}: {param_value}")
                if params:
                    analysis_parts.append(f"Product parameters:\n" + "\n".join(params))

            # Category breadcrumbs
            breadcrumbs = soup.find('nav', class_='breadcrumb') or soup.find('ul', class_='breadcrumb')
            if breadcrumbs:
                categories = [elem.get_text(strip=True) for elem in breadcrumbs.find_all('a')]
                if categories:
                    analysis_parts.append(f"Category path: {' > '.join(categories)}")

            if analysis_parts:
                return "\n".join(analysis_parts)

            return None

        except requests.exceptions.RequestException as e:
            logging.warning(f"Failed to fetch Pincesobchod page {url}: {str(e)}")
            return None
        except Exception as e:
            logging.warning(f"Error analyzing Pincesobchod page {url}: {str(e)}", exc_info=True)
            return None

    def _confirm_ai_suggestion(self, field_name: str, ai_suggestion: str,
                                products: List[RepairedProduct]) -> str:
        """
        Show AI suggestion to user for confirmation or modification.

        Args:
            field_name: Name of the conflicting field
            ai_suggestion: AI's suggested value
            products: List of products with conflicting values

        Returns:
            str: User-confirmed or user-modified value
        """
        print(f"\n{'='*80}")
        print(f"🤖 AI SUGGESTION FOR MERGE CONFLICT: Field '{field_name}'")
        print(f"{'='*80}")

        # Display product context
        print(f"\nProduct name: {products[0].name}")
        print(f"\nOriginal conflicting values:")
        for i, product in enumerate(products, 1):
            value = getattr(product, field_name, '')
            if value and value.strip():
                print(f"  [{i}] {value}")
                print(f"      (from original_name: '{product.original_name}')")
                if hasattr(product, 'url') and product.url:
                    print(f"      (URL: {product.url})")

        # Display AI suggestion
        print(f"\n{'='*80}")
        print(f"🎯 AI Suggests: {ai_suggestion}")
        print(f"{'='*80}")

        try:
            response = input(f"✅ Press Enter to confirm AI suggestion or type new value: ").strip()

            # If user provided input (not just Enter to accept)
            if response:
                # User wants to use different value
                try:
                    sanitized = self._sanitize_user_input(response, field_name)
                    # Write AI suggestion to trash if user changed it
                    memory_prefix = self._get_memory_file_for_field(field_name)
                    if memory_prefix:
                        for product in products:
                            if product.original_name and ai_suggestion.strip().lower() != sanitized.strip().lower():
                                self._add_to_trash(memory_prefix, product.original_name, ai_suggestion)
                    return sanitized
                except ValueError as e:
                    print(f"ERROR: Invalid input - {str(e)}")
                    print("Using AI suggestion instead.")
                    return ai_suggestion
            else:
                # User accepted AI suggestion
                return ai_suggestion

        except KeyboardInterrupt:
            # User interrupted - use AI suggestion
            return ai_suggestion

    def _ask_user_for_conflict_resolution(self, field_name: str,
                                           products: List[RepairedProduct]) -> str:
        """
        Ask user to resolve merge conflict interactively.

        Args:
            field_name: Name of the conflicting field
            products: List of products with conflicting values

        Returns:
            str: User-chosen or user-entered value
        """
        print(f"\n{'='*80}")
        print(f"MERGE CONFLICT: Field '{field_name}' has multiple different values")
        print(f"{'='*80}")

        # Get values for this field from all products
        values = []
        for i, product in enumerate(products):
            value = getattr(product, field_name, '')
            if value and value.strip():
                values.append({
                    'index': i + 1,
                    'value': value,
                    'product': product
                })

        # Display options
        print(f"\nProduct name: {products[0].name}")
        print(f"\nConflicting values for field '{field_name}':")
        for item in values:
            print(f"  [{item['index']}] {item['value']}")
            print(f"      (from original_name: '{item['product'].original_name}')")
            if hasattr(item['product'], 'url') and item['product'].url:
                print(f"      (URL: {item['product'].url})")

        # Ask user to choose
        while True:
            user_input = input(f"\nChoose option number (1-{len(values)}), or press ENTER to enter custom value: ").strip()

            if user_input == "":
                # User wants to enter custom value
                custom_value = input(f"Enter correct value for '{field_name}': ").strip()
                if custom_value:
                    # Sanitize custom input
                    try:
                        sanitized = self._sanitize_user_input(custom_value, field_name)
                        return sanitized
                    except ValueError as e:
                        print(f"ERROR: Invalid input - {str(e)}")
                        print("Please try again.")
                        continue
                else:
                    print("ERROR: Value cannot be empty. Please try again.")
                    continue

            # Check if valid number
            try:
                choice = int(user_input)
                if 1 <= choice <= len(values):
                    # Pre-existing values are already in the system, but still validate
                    chosen_value = values[choice - 1]['value']
                    try:
                        sanitized = self._sanitize_user_input(chosen_value, field_name)
                        return sanitized
                    except ValueError as e:
                        logging.warning(f"Pre-existing value failed validation: {str(e)}. Using anyway.")
                        return chosen_value
                else:
                    print(f"ERROR: Invalid choice. Please enter number 1-{len(values)} or press ENTER.")
            except ValueError:
                print(f"ERROR: Invalid input. Please enter number 1-{len(values)} or press ENTER.")

    def _get_memory_file_for_field(self, field_name: str) -> Optional[str]:
        """
        Get memory file name for a given field.

        Args:
            field_name: Field name (e.g., 'type', 'brand', 'model', 'category')

        Returns:
            Optional[str]: Memory file name prefix (without language suffix)
        """
        field_to_memory = {
            'type': PRODUCT_TYPE_MEMORY_PREFIX,
            'brand': PRODUCT_BRAND_MEMORY_PREFIX,
            'model': PRODUCT_MODEL_MEMORY_PREFIX,
            'category': CATEGORY_MEMORY_PREFIX,
            'desc': DESC_MEMORY_PREFIX,
            'shortdesc': SHORT_DESC_MEMORY_PREFIX,
            'google_keywords': KEYWORDS_GOOGLE_PREFIX,
            'zbozi_keywords': KEYWORDS_ZBOZI_PREFIX,
        }

        return field_to_memory.get(field_name, None)

    def _validate_file_path(self, file_path: str) -> str:
        """
        Validate that file path is within memory_dir bounds.

        Args:
            file_path: File path to validate

        Returns:
            str: Validated absolute file path

        Raises:
            ValueError: If path escapes memory_dir
        """
        # Get absolute paths
        abs_memory_dir = os.path.abspath(self.memory_dir)
        abs_file_path = os.path.abspath(file_path)

        # Check if file path is within memory_dir
        if not abs_file_path.startswith(abs_memory_dir):
            raise ValueError(f"Path traversal detected: {file_path} is outside memory directory {abs_memory_dir}")

        return abs_file_path

    def _evict_lru_cache_if_needed(self):
        """
        Evict least recently used cache entry if cache is full.
        Only evicts clean (non-dirty) entries.
        """
        if len(self.memory_cache) < self.MAX_CACHE_SIZE:
            return

        # Try to evict oldest clean entry (FIFO for clean items)
        for cache_key in list(self.memory_cache.keys()):
            if cache_key not in self.memory_dirty:
                # Found a clean entry to evict
                self.memory_cache.pop(cache_key)
                logging.debug(f"Evicted {cache_key} from cache (LRU, clean)")
                return

        # If all entries are dirty, we can't evict any
        # This is acceptable - dirty entries will be saved at end
        logging.warning(f"Cache full ({len(self.memory_cache)} entries), but all are dirty. Cannot evict.")

    def _load_memory_file(self, memory_prefix: str) -> Dict[str, str]:
        """
        Load memory file from disk (with LRU caching).

        Args:
            memory_prefix: Memory file prefix (e.g., 'CategoryMemory')

        Returns:
            Dict[str, str]: Memory data (KEY -> VALUE mapping)
        """
        cache_key = f"{memory_prefix}_{self.language}"

        # Check cache first (and move to end for LRU)
        if cache_key in self.memory_cache:
            # Move to end (most recently used)
            self.memory_cache.move_to_end(cache_key)
            return self.memory_cache[cache_key]

        # Evict LRU entry if cache is full
        self._evict_lru_cache_if_needed()

        # Construct and validate file path
        file_path = os.path.join(self.memory_dir, f"{cache_key}.csv")
        file_path = self._validate_file_path(file_path)

        try:
            csv_data = load_csv_file(file_path)

            # Convert to dict (KEY -> VALUE)
            memory_dict = {}
            for row in csv_data:
                if 'KEY' in row and 'VALUE' in row:
                    memory_dict[row['KEY']] = row['VALUE']

            # Cache it (add to end)
            self.memory_cache[cache_key] = memory_dict
            logging.debug(f"Loaded memory file: {file_path} ({len(memory_dict)} entries)")
            return memory_dict

        except FileNotFoundError:
            # Recoverable: file doesn't exist yet, will be created on first save
            logging.info(f"Memory file not found: {file_path}. Will create new one on first save.")
            self.memory_cache[cache_key] = {}
            return {}
        except PermissionError as e:
            # Serious: cannot read file due to permissions
            logging.error(f"Permission denied reading memory file {file_path}: {str(e)}", exc_info=True)
            raise  # Re-raise, this is a fatal error
        except OSError as e:
            # Serious: disk error, corrupted filesystem, etc
            if e.errno == 28:  # ENOSPC - No space left on device
                logging.error(f"Disk full while reading memory file {file_path}", exc_info=True)
            else:
                logging.error(f"OS error reading memory file {file_path}: {str(e)}", exc_info=True)
            raise  # Re-raise, this is a fatal error
        except UnicodeDecodeError as e:
            # Recoverable but concerning: file encoding issue
            logging.error(f"Encoding error in memory file {file_path}: {str(e)}. File may be corrupted.", exc_info=True)
            # Try to continue with empty dict
            self.memory_cache[cache_key] = {}
            return {}
        except Exception as e:
            # Unknown error - log and continue with empty dict
            logging.error(f"Unexpected error loading memory file {file_path}: {str(e)}", exc_info=True)
            self.memory_cache[cache_key] = {}
            return {}

    def _save_memory_file(self, memory_prefix: str, force: bool = False):
        """
        Save memory file to disk if it has been modified (dirty flag).

        Args:
            memory_prefix: Memory file prefix (e.g., 'CategoryMemory')
            force: If True, save even if not marked as dirty
        """
        cache_key = f"{memory_prefix}_{self.language}"

        if cache_key not in self.memory_cache:
            logging.warning(f"Cannot save memory file {cache_key}: not in cache")
            return

        # Check if file needs saving
        if not force and cache_key not in self.memory_dirty:
            logging.debug(f"Skipping save of {cache_key}: no changes")
            return

        # Construct and validate file path
        file_path = os.path.join(self.memory_dir, f"{cache_key}.csv")
        file_path = self._validate_file_path(file_path)

        try:
            # Convert dict to CSV format (KEY, VALUE)
            csv_data = [{"KEY": key, "VALUE": value}
                       for key, value in self.memory_cache[cache_key].items()]

            save_csv_file(csv_data, file_path)
            logging.info(f"Saved memory file: {file_path} ({len(csv_data)} entries)")

            # Clear dirty flag after successful save
            self.memory_dirty.discard(cache_key)

        except Exception as e:
            logging.error(f"Error saving memory file {file_path}: {str(e)}", exc_info=True)
            # Keep dirty flag set so we can retry later
            raise

    def save_all_dirty_memory_files(self):
        """
        Save all memory files that have been modified (batch save at end).
        """
        if not self.memory_dirty:
            logging.debug("No dirty memory files to save")
            return

        logging.info(f"Saving {len(self.memory_dirty)} modified memory files...")

        # Get list of dirty files (copy to avoid modification during iteration)
        dirty_files = list(self.memory_dirty)

        for cache_key in dirty_files:
            # Extract prefix from cache_key (remove language suffix)
            memory_prefix = cache_key.rsplit('_', 1)[0]
            self._save_memory_file(memory_prefix, force=True)

        logging.info(f"All dirty memory files saved successfully")

    def _add_to_trash(self, memory_prefix: str, product_key: str, value: str):
        """
        Immediately append entry to trash file (fire-and-forget).

        Args:
            memory_prefix: Memory file prefix (e.g., "ProductBrandMemory")
            product_key: Product key (usually product.original_name)
            value: The incorrect value to trash (can be empty string)
        """
        if not memory_prefix or not product_key:
            return

        # Determine trash file path
        trash_filepath = os.path.join(self.trash_dir, f"{memory_prefix}_{self.language}_trash.csv")

        try:
            # Ensure trash directory exists
            os.makedirs(self.trash_dir, exist_ok=True)

            # Load existing trash file to check for duplicates
            existing_rows = set()
            if os.path.exists(trash_filepath):
                existing_entries = load_csv_file(trash_filepath)
                for entry in existing_entries:
                    row_id = (entry.get('KEY', ''), entry.get('VALUE', ''))
                    existing_rows.add(row_id)

            # Check if this exact row already exists
            new_row_id = (product_key, value)
            if new_row_id in existing_rows:
                logging.debug(f"Trash entry already exists: {memory_prefix} - KEY='{product_key}', VALUE='{value}'")
                return

            # Append new entry (no backup, true append mode)
            from shared.file_ops import append_to_csv_file
            new_entry = {'KEY': product_key, 'VALUE': value}
            append_to_csv_file(trash_filepath, new_entry)

            logging.debug(f"🗑️  Trash: {memory_prefix} - KEY='{product_key}', VALUE='{value}'")

        except Exception as e:
            logging.error(f"Error writing trash entry to {trash_filepath}: {str(e)}", exc_info=True)

    def _update_memory_for_field(self, field_name: str, products: List[RepairedProduct],
                                  new_value: str):
        """
        Update memory file for a given field with the chosen value.
        Also write incorrect (non-chosen) values to trash file.

        Args:
            field_name: Field name (e.g., 'type', 'brand', 'category')
            products: List of products that had conflicting values
            new_value: The chosen/entered value to save to memory
        """
        memory_prefix = self._get_memory_file_for_field(field_name)

        if not memory_prefix:
            logging.warning(f"No memory file mapped for field '{field_name}'. Skipping memory update.")
            return

        # Load memory file
        memory_dict = self._load_memory_file(memory_prefix)

        # Update all original_names from products to point to new value
        # Write incorrect (non-chosen) values to trash immediately (fire-and-forget)
        for product in products:
            if product.original_name:
                old_value = getattr(product, field_name, '')

                # If old value differs from chosen value, write to trash immediately
                if old_value and old_value.strip() and old_value.strip().lower() != new_value.strip().lower():
                    self._add_to_trash(memory_prefix, product.original_name, old_value)

                # Update memory with correct value
                memory_dict[product.original_name] = new_value

        # Update cache
        cache_key = f"{memory_prefix}_{self.language}"
        self.memory_cache[cache_key] = memory_dict

        # Mark as dirty (needs saving)
        self.memory_dirty.add(cache_key)

        logging.info(f"Updated {memory_prefix}_{self.language}.csv in memory: set {len(products)} entries to '{new_value}'")

    def _update_name_memory(self, products: List[RepairedProduct], type_val: str,
                            brand_val: str, model_val: str):
        """
        Update NameMemory based on type/brand/model values.

        Args:
            products: List of products to update
            type_val: Product type value
            brand_val: Product brand value
            model_val: Product model value
        """
        # Validate that we have at least type and model
        # (brand can be empty, but type and model are required for meaningful name)
        if not type_val or not type_val.strip():
            logging.warning(f"Cannot update NameMemory: type is empty for products {[p.original_name for p in products]}")
            return

        if not model_val or not model_val.strip():
            logging.warning(f"Cannot update NameMemory: model is empty for products {[p.original_name for p in products]}")
            return

        # Compose name from type + brand + model
        if brand_val and brand_val.strip():
            composed_name = f"{type_val} {brand_val} {model_val}".strip()
        else:
            composed_name = f"{type_val} {model_val}".strip()

        # Validate composed name is not empty
        if not composed_name or not composed_name.strip():
            logging.error(f"Cannot update NameMemory: composed name is empty after combining type/brand/model")
            return

        # Load NameMemory
        memory_dict = self._load_memory_file(NAME_MEMORY_PREFIX)

        # Update all original_names
        for product in products:
            if product.original_name:
                memory_dict[product.original_name] = composed_name

        # Update cache
        cache_key = f"{NAME_MEMORY_PREFIX}_{self.language}"
        self.memory_cache[cache_key] = memory_dict

        # Mark as dirty (needs saving)
        self.memory_dirty.add(cache_key)

        logging.info(f"Updated {NAME_MEMORY_PREFIX}_{self.language}.csv in memory: set {len(products)} entries to '{composed_name}'")

    def _get_variant_key(self, variant: Variant) -> str:
        """
        Generate a unique key for variant comparison.

        Variants are considered duplicate if all properties match:
        - current_price
        - basic_price
        - stock_status
        - key_value_pairs (order doesn't matter)

        The comparison is order-independent for key_value_pairs - variants with
        the same keys and values in different order are considered identical.

        Args:
            variant: Variant to generate key for

        Returns:
            String key for variant comparison
        """
        # Normalize and sort key_value_pairs to make order and case irrelevant
        # Convert to list of tuples, normalize both keys and values, then sort
        normalized_kvp = []
        if variant.key_value_pairs:
            for key, value in variant.key_value_pairs.items():
                # Normalize key: strip whitespace, convert to lowercase
                normalized_key = str(key).strip().lower()
                # Normalize value: strip whitespace, convert to string, lowercase
                normalized_value = str(value).strip().lower()
                normalized_kvp.append((normalized_key, normalized_value))
            # Sort by key to ensure consistent ordering
            normalized_kvp.sort()

        # Create comparison tuple (tuples are hashable and can be compared)
        key_data = (
            variant.current_price,
            variant.basic_price,
            variant.stock_status.strip().lower() if variant.stock_status else '',
            tuple(normalized_kvp)  # Convert list to tuple for hashability
        )

        # Convert to JSON string for consistent comparison
        return json.dumps({
            'current_price': key_data[0],
            'basic_price': key_data[1],
            'stock_status': key_data[2],
            'key_value_pairs': key_data[3]
        }, sort_keys=True, ensure_ascii=False)
