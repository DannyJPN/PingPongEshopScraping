"""
Product filtering module for desaka_unifier project.

This module handles filtering of products based on various criteria
including category rules and ItemFilter configurations.
"""

import os
import logging
from typing import List, Tuple, Dict, Any
from datetime import datetime
from tqdm import tqdm
from .repaired_product import RepairedProduct
from .constants import WRONGS_FILE


class ProductFilter:
    """
    Handles filtering of products based on various criteria.
    """
    
    def __init__(self, memory_data: Dict[str, Any] = None):
        """
        Initialize product filter.
        
        Args:
            memory_data (Dict[str, Any]): Memory data containing filter configurations
        """
        self.memory = memory_data or {}
        
    def filter_by_category_and_item_filter(self, repaired_products: List[RepairedProduct]) -> Tuple[List[RepairedProduct], List[RepairedProduct]]:
        """
        Filter products by category "Vyřadit" and ItemFilter rules.
        
        Args:
            repaired_products (List[RepairedProduct]): List of repaired products
            
        Returns:
            Tuple[List[RepairedProduct], List[RepairedProduct]]: (filtered_products, rejected_products)
        """
        filtered_products = []
        rejected_products = []
        
        # Load ItemFilter data
        item_filter_data = self.memory.get('ItemFilter', [])
        
        # Convert to list of allowed combinations
        allowed_combinations = []
        for row in item_filter_data:
            if isinstance(row, dict) and 'typ_produktu' in row and 'znacka' in row and 'eshop_url' in row:
                allowed_combinations.append({
                    'typ': row['typ_produktu'].strip().lower(),
                    'znacka': row['znacka'].strip().lower(),
                    'url': row['eshop_url'].strip().lower()
                })
        
        with tqdm(total=len(repaired_products), desc="Filtering products", unit="product", miniters=1, mininterval=0.01) as pbar:
            for product in repaired_products:
                # Check if category is "Vyřadit"
                if product.category and product.category.strip().lower() == "vyřadit":
                    rejected_products.append(product)
                    pbar.update(1)
                    continue

                # Check ItemFilter if we have filter data
                if allowed_combinations:
                    # Extract product type from category (first part before >)
                    product_type = ""
                    if product.category:
                        category_parts = product.category.split('>')
                        if category_parts:
                            product_type = category_parts[0].strip().lower()

                    # Check if combination is allowed
                    is_allowed = False
                    for combo in allowed_combinations:
                        if (combo['typ'] == product_type and
                            combo['znacka'] == product.brand.strip().lower() and
                            combo['url'] in product.url.strip().lower()):
                            is_allowed = True
                            break

                    if is_allowed:
                        filtered_products.append(product)
                    else:
                        rejected_products.append(product)
                else:
                    # No filter data, allow all products that are not "Vyřadit"
                    filtered_products.append(product)
                pbar.update(1)
        
        return filtered_products, rejected_products
    
    def save_rejected_products_to_wrongs(self, rejected_products: List[RepairedProduct], wrongs_file_path: str = None):
        """
        Save rejected products to Wrongs.txt file.
        
        Args:
            rejected_products (List[RepairedProduct]): List of rejected products
            wrongs_file_path (str): Path to Wrongs.txt file (default: Memory/Wrongs.txt)
        """
        if wrongs_file_path is None:
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            wrongs_file_path = os.path.join(script_dir, "Memory", WRONGS_FILE)
        
        try:
            with open(wrongs_file_path, 'a', encoding='utf-8') as f:
                for product in rejected_products:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    reason = "Category: Vyřadit" if product.category and product.category.strip().lower() == "vyřadit" else "ItemFilter: Not allowed"
                    f.write(f"{timestamp} - {product.name} ({product.url}) - {reason}\n")
            
            logging.info(f"Saved {len(rejected_products)} rejected products to {wrongs_file_path}")

        except Exception as e:
            logging.error(f"Error saving rejected products to {WRONGS_FILE}: {str(e)}")
    
    def process_products_with_filtering(self, repaired_products: List[RepairedProduct]) -> Tuple[List[RepairedProduct], List[RepairedProduct]]:
        """
        Process repaired products with filtering and save rejected ones.
        
        Args:
            repaired_products (List[RepairedProduct]): List of repaired products
            
        Returns:
            Tuple[List[RepairedProduct], List[RepairedProduct]]: (filtered_products, rejected_products)
        """
        # Filter products
        filtered_products, rejected_products = self.filter_by_category_and_item_filter(repaired_products)
        
        # Save rejected products to Wrongs.txt
        if rejected_products:
            self.save_rejected_products_to_wrongs(rejected_products)
        
        return filtered_products, rejected_products
    
    def filter_by_category(self, products: List[RepairedProduct], excluded_categories: List[str] = None) -> Tuple[List[RepairedProduct], List[RepairedProduct]]:
        """
        Filter products by excluding specific categories.
        
        Args:
            products (List[RepairedProduct]): List of products to filter
            excluded_categories (List[str]): List of categories to exclude (default: ["Vyřadit"])
            
        Returns:
            Tuple[List[RepairedProduct], List[RepairedProduct]]: (filtered_products, rejected_products)
        """
        if excluded_categories is None:
            excluded_categories = ["vyřadit"]
        
        # Convert to lowercase for case-insensitive comparison
        excluded_categories_lower = [cat.strip().lower() for cat in excluded_categories]
        
        filtered_products = []
        rejected_products = []
        
        for product in products:
            if product.category and product.category.strip().lower() in excluded_categories_lower:
                rejected_products.append(product)
            else:
                filtered_products.append(product)
        
        return filtered_products, rejected_products
    
    def filter_by_brand(self, products: List[RepairedProduct], allowed_brands: List[str]) -> Tuple[List[RepairedProduct], List[RepairedProduct]]:
        """
        Filter products by allowing only specific brands.
        
        Args:
            products (List[RepairedProduct]): List of products to filter
            allowed_brands (List[str]): List of allowed brands
            
        Returns:
            Tuple[List[RepairedProduct], List[RepairedProduct]]: (filtered_products, rejected_products)
        """
        allowed_brands_lower = [brand.strip().lower() for brand in allowed_brands]
        
        filtered_products = []
        rejected_products = []
        
        for product in products:
            if product.brand and product.brand.strip().lower() in allowed_brands_lower:
                filtered_products.append(product)
            else:
                rejected_products.append(product)
        
        return filtered_products, rejected_products
    
    def filter_by_url_pattern(self, products: List[RepairedProduct], allowed_url_patterns: List[str]) -> Tuple[List[RepairedProduct], List[RepairedProduct]]:
        """
        Filter products by URL patterns.
        
        Args:
            products (List[RepairedProduct]): List of products to filter
            allowed_url_patterns (List[str]): List of allowed URL patterns
            
        Returns:
            Tuple[List[RepairedProduct], List[RepairedProduct]]: (filtered_products, rejected_products)
        """
        filtered_products = []
        rejected_products = []
        
        for product in products:
            is_allowed = False
            for pattern in allowed_url_patterns:
                if pattern.lower() in product.url.lower():
                    is_allowed = True
                    break
            
            if is_allowed:
                filtered_products.append(product)
            else:
                rejected_products.append(product)
        
        return filtered_products, rejected_products
    
    def get_filter_statistics(self, original_count: int, filtered_count: int, rejected_count: int) -> Dict[str, Any]:
        """
        Get filtering statistics.
        
        Args:
            original_count (int): Original number of products
            filtered_count (int): Number of filtered products
            rejected_count (int): Number of rejected products
            
        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        return {
            'original_count': original_count,
            'filtered_count': filtered_count,
            'rejected_count': rejected_count,
            'filter_rate': (filtered_count / original_count * 100) if original_count > 0 else 0,
            'rejection_rate': (rejected_count / original_count * 100) if original_count > 0 else 0
        }
