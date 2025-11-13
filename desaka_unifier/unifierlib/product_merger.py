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
from collections import defaultdict
import json
from tqdm import tqdm
from .repaired_product import RepairedProduct
from .variant import Variant
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
    KEYWORDS_ZBOZI_PREFIX
)


class ProductMerger:
    """Handles merging of duplicate RepairedProducts."""

    def __init__(self, language: str, memory_dir: str):
        """
        Initialize the ProductMerger.

        Args:
            language: Language code (e.g., 'CS', 'SK')
            memory_dir: Path to Memory directory
        """
        self.language = language
        self.memory_dir = memory_dir
        self.memory_cache = {}  # Cache for loaded memory files
    
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
            'category_ids': self._merge_string_values([p.category_ids for p in products],
                                                      'category_ids', products),
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
            'variantcode': self._merge_string_values([p.variantcode for p in products],
                                                     'variantcode', products),
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

        # Update NameMemory if type/brand/model were resolved
        # This ensures NameMemory stays consistent with the chosen values
        if merged_data.get('type') or merged_data.get('brand') or merged_data.get('model'):
            self._update_name_memory(
                products,
                merged_data.get('type', ''),
                merged_data.get('brand', ''),
                merged_data.get('model', '')
            )

        logging.debug(f"Successfully merged {len(products)} products into one: {merged_product.name}")
        return merged_product
    
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

        # For all other fields, ask user to resolve conflict
        logging.warning(f"Conflict detected in field '{field_name}' - asking user to resolve")

        # Ask user interactively
        chosen_value = self._ask_user_for_conflict_resolution(field_name, products)

        # Update memory file for this field
        self._update_memory_for_field(field_name, products, chosen_value)

        logging.info(f"User resolved conflict for field '{field_name}': chose '{chosen_value}'")

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

    def _load_memory_file(self, memory_prefix: str) -> Dict[str, str]:
        """
        Load memory file from disk (with caching).

        Args:
            memory_prefix: Memory file prefix (e.g., 'CategoryMemory')

        Returns:
            Dict[str, str]: Memory data (KEY -> VALUE mapping)
        """
        cache_key = f"{memory_prefix}_{self.language}"

        # Check cache first
        if cache_key in self.memory_cache:
            return self.memory_cache[cache_key]

        # Load from disk
        file_path = os.path.join(self.memory_dir, f"{cache_key}.csv")

        try:
            csv_data = load_csv_file(file_path)

            # Convert to dict (KEY -> VALUE)
            memory_dict = {}
            for row in csv_data:
                if 'KEY' in row and 'VALUE' in row:
                    memory_dict[row['KEY']] = row['VALUE']

            # Cache it
            self.memory_cache[cache_key] = memory_dict
            logging.debug(f"Loaded memory file: {file_path} ({len(memory_dict)} entries)")
            return memory_dict

        except FileNotFoundError:
            logging.warning(f"Memory file not found: {file_path}. Will create new one.")
            self.memory_cache[cache_key] = {}
            return {}
        except Exception as e:
            logging.error(f"Error loading memory file {file_path}: {str(e)}", exc_info=True)
            self.memory_cache[cache_key] = {}
            return {}

    def _save_memory_file(self, memory_prefix: str):
        """
        Save memory file to disk.

        Args:
            memory_prefix: Memory file prefix (e.g., 'CategoryMemory')
        """
        cache_key = f"{memory_prefix}_{self.language}"

        if cache_key not in self.memory_cache:
            logging.warning(f"Cannot save memory file {cache_key}: not in cache")
            return

        file_path = os.path.join(self.memory_dir, f"{cache_key}.csv")

        try:
            # Convert dict to CSV format (KEY, VALUE)
            csv_data = [{"KEY": key, "VALUE": value}
                       for key, value in self.memory_cache[cache_key].items()]

            save_csv_file(csv_data, file_path)
            logging.debug(f"Saved memory file: {file_path} ({len(csv_data)} entries)")

        except Exception as e:
            logging.error(f"Error saving memory file {file_path}: {str(e)}", exc_info=True)

    def _update_memory_for_field(self, field_name: str, products: List[RepairedProduct],
                                  new_value: str):
        """
        Update memory file for a given field with the chosen value.

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
        for product in products:
            if product.original_name:
                memory_dict[product.original_name] = new_value

        # Update cache
        cache_key = f"{memory_prefix}_{self.language}"
        self.memory_cache[cache_key] = memory_dict

        # Save to disk
        self._save_memory_file(memory_prefix)

        logging.info(f"Updated {memory_prefix}_{self.language}.csv: set {len(products)} entries to '{new_value}'")

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
        # Compose name from type + brand + model
        if brand_val and brand_val.strip():
            composed_name = f"{type_val} {brand_val} {model_val}".strip()
        else:
            composed_name = f"{type_val} {model_val}".strip()

        # Load NameMemory
        memory_dict = self._load_memory_file(NAME_MEMORY_PREFIX)

        # Update all original_names
        for product in products:
            if product.original_name:
                memory_dict[product.original_name] = composed_name

        # Update cache
        cache_key = f"{NAME_MEMORY_PREFIX}_{self.language}"
        self.memory_cache[cache_key] = memory_dict

        # Save to disk
        self._save_memory_file(NAME_MEMORY_PREFIX)

        logging.info(f"Updated {NAME_MEMORY_PREFIX}_{self.language}.csv: set {len(products)} entries to '{composed_name}'")

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
