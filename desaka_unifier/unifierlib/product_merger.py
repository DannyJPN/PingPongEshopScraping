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
        
        for name, products in products_by_name.items():
            if len(products) == 1:
                # No duplicates, keep as-is
                merged_products.append(products[0])
            else:
                # Merge duplicates
                logging.debug(f"Merging {len(products)} products with name: {name}")
                merged_product = self._merge_product_group(products)
                merged_products.append(merged_product)
        
        logging.info(f"Product merging completed. {len(repaired_products)} -> {len(merged_products)} products")
        return merged_products
    
    def _merge_product_group(self, products: List[RepairedProduct]) -> RepairedProduct:
        """
        Merge a group of products with the same name.
        
        Args:
            products: List of products to merge (all have same name)
            
        Returns:
            Single merged RepairedProduct
        """
        if not products:
            raise ValueError("Cannot merge empty product list")
        
        if len(products) == 1:
            return products[0]
        
        # Use first product as base
        base_product = products[0]
        
        # Merge all string properties
        merged_data = {
            'original_name': self._merge_string_values([p.original_name for p in products]),
            'name': base_product.name,  # Name should be the same for all
            'category': self._merge_string_values([p.category for p in products]),
            'brand': self._merge_string_values([p.brand for p in products]),
            'category_ids': self._merge_string_values([p.category_ids for p in products]),
            'code': self._merge_string_values([p.code for p in products]),
            'desc': self._merge_string_values([p.desc for p in products]),
            'glami_category': self._merge_string_values([p.glami_category for p in products]),
            'google_category': self._merge_string_values([p.google_category for p in products]),
            'google_keywords': self._merge_string_values([p.google_keywords for p in products]),
            'heureka_category': self._merge_string_values([p.heureka_category for p in products]),
            'price': self._merge_string_values([p.price for p in products]),
            'price_standard': self._merge_string_values([p.price_standard for p in products]),
            'shortdesc': self._merge_string_values([p.shortdesc for p in products]),
            'zbozi_category': self._merge_string_values([p.zbozi_category for p in products]),
            'zbozi_keywords': self._merge_string_values([p.zbozi_keywords for p in products]),
            'url': self._merge_string_values([p.url for p in products])
        }
        
        # Merge variants
        all_variants = []
        for product in products:
            if product.Variants:
                all_variants.extend(product.Variants)
        
        merged_variants = self._merge_variants(all_variants)
        merged_data['Variants'] = merged_variants
        
        # Create merged product
        merged_product = RepairedProduct(**merged_data)
        
        logging.debug(f"Merged {len(products)} products into one: {merged_product.name}")
        return merged_product
    
    def _merge_string_values(self, values: List[str]) -> str:
        """
        Merge string values by combining with '|' separator and removing duplicates.
        
        Args:
            values: List of string values to merge
            
        Returns:
            Merged string with unique values separated by '|'
        """
        # Filter out None and empty values
        valid_values = [v.strip() for v in values if v and v.strip()]
        
        if not valid_values:
            return ""
        
        # Split by '|' and collect all parts
        all_parts = []
        for value in valid_values:
            parts = [part.strip() for part in value.split('|') if part.strip()]
            all_parts.extend(parts)
        
        # Remove duplicates while preserving order
        unique_parts = []
        seen = set()
        for part in all_parts:
            if part.lower() not in seen:
                unique_parts.append(part)
                seen.add(part.lower())
        
        return '|'.join(unique_parts)
    
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
        
        Args:
            variant: Variant to generate key for
            
        Returns:
            String key for variant comparison
        """
        # Sort key_value_pairs to make order irrelevant
        sorted_kvp = {}
        if variant.key_value_pairs:
            sorted_kvp = dict(sorted(variant.key_value_pairs.items()))
        
        key_data = {
            'current_price': variant.current_price,
            'basic_price': variant.basic_price,
            'stock_status': variant.stock_status,
            'key_value_pairs': sorted_kvp
        }
        
        # Convert to JSON string for consistent comparison
        return json.dumps(key_data, sort_keys=True, ensure_ascii=False)
