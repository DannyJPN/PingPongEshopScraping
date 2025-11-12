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
from typing import List, Dict, Any
from collections import defaultdict
import json
from tqdm import tqdm
from .repaired_product import RepairedProduct
from .variant import Variant


class ProductMerger:
    """Handles merging of duplicate RepairedProducts."""
    
    def __init__(self):
        """Initialize the ProductMerger."""
        pass
    
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
                                             'url', products)
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

        logging.debug(f"Successfully merged {len(products)} products into one: {merged_product.name}")
        return merged_product
    
    def _merge_string_values(self, values: List[str], field_name: str,
                             products: List[RepairedProduct], allow_multiple: bool = False) -> str:
        """
        Merge string values - raises exception if multiple different values exist.

        Args:
            values: List of string values to merge
            field_name: Name of the field being merged (for error messages)
            products: Original products (for detailed error reporting)
            allow_multiple: If True, allows multiple values (for original_name field only)

        Returns:
            Single merged value (or combined with '|' if allow_multiple=True)

        Raises:
            ValueError: If multiple conflicting values exist and allow_multiple=False
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

        # For all other fields, this is an error that must be resolved manually
        # TODO: Implement user interface to resolve conflicts
        # For now, raise an exception to force manual resolution
        error_msg = f"\nMERGE CONFLICT: Field '{field_name}' has multiple different values:\n"
        for i, product in enumerate(products):
            value = getattr(product, field_name, '')
            error_msg += f"  Product {i+1} (original_name='{product.original_name}'): {field_name}='{value}'\n"
        error_msg += "\nUser must resolve this conflict in the source data before merging can proceed."

        logging.error(error_msg)
        raise ValueError(error_msg)

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
