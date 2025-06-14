"""
Product combiner module for combining ExportProducts from different sources.

This module handles combining ExportProducts that come from JSON files (pincesobchod)
with ExportProducts converted from RepairedProducts. The combination is based on
product name (case-insensitive comparison).

Key functionality:
- Combine products with same name (case-insensitive) - JSON vs RepairedProducts
- Generate reports for new products, old products, code changes, price changes
- Save all reports to ExportDir/Výsledky using file_ops methods

Note: This is different from ProductMerger which merges RepairedProducts with same name.
ProductCombiner combines ExportProducts from different sources (JSON vs Repaired).
"""

import os
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime
from collections import defaultdict
from .export_product import ExportProduct, ExportMainProduct, ExportProductVariant
from shared.file_ops import save_csv_file, ensure_directory_exists


class ProductCombiner:
    """
    Handles combining ExportProducts from different sources and generating reports.
    """
    
    def __init__(self, export_dir: str):
        """
        Initialize product combiner.
        
        Args:
            export_dir (str): Base export directory path
        """
        self.export_dir = export_dir
        self.results_dir = os.path.join(export_dir, "Výsledky")
        
        # Ensure results directory exists
        ensure_directory_exists(self.results_dir)
        
    def combine_products(self, json_export_products: List[ExportProduct], 
                        repaired_export_products: List[ExportProduct]) -> Tuple[List[ExportProduct], Dict[str, Any]]:
        """
        Combine ExportProducts from JSON and RepairedProducts sources.
        
        Args:
            json_export_products: Products from JSON files (pincesobchod)
            repaired_export_products: Products converted from RepairedProducts
            
        Returns:
            Tuple of (combined_products, reports_data)
        """
        logging.info("Starting product combination process...")
        
        # Create name-based indexes (case-insensitive)
        json_products_by_name = self._create_name_index(json_export_products)
        repaired_products_by_name = self._create_name_index(repaired_export_products)
        
        # Track processed products
        combined_products = []
        processed_json_names = set()
        
        # Reports data
        reports = {
            'new_products': [],      # Products in repaired but not in JSON
            'old_products': [],      # Products in JSON but not in repaired
            'code_changes': [],      # Products with same name but different codes
            'price_increases': [],   # Products with price increases
            'price_decreases': []    # Products with price decreases (discounts)
        }
        
        # Process repaired products (these take priority)
        for name_lower, repaired_products in repaired_products_by_name.items():
            if name_lower in json_products_by_name:
                # Product exists in both - merge and check for changes
                json_products = json_products_by_name[name_lower]
                merged_products = self._combine_product_groups(json_products, repaired_products, reports)
                combined_products.extend(merged_products)
                processed_json_names.add(name_lower)
            else:
                # New product - only in repaired
                combined_products.extend(repaired_products)
                for product in repaired_products:
                    if hasattr(product, 'kod') and hasattr(product, 'nazev'):
                        reports['new_products'].append({
                            'kod': product.kod,
                            'nazev': product.nazev,
                            'url': getattr(product, 'url', '')
                        })
        
        # Add remaining JSON products (old products)
        for name_lower, json_products in json_products_by_name.items():
            if name_lower not in processed_json_names:
                # Old product - only in JSON
                for product in json_products:
                    if hasattr(product, 'kod') and hasattr(product, 'nazev'):
                        reports['old_products'].append({
                            'kod': product.kod,
                            'nazev': product.nazev,
                            'url': getattr(product, 'url', '')
                        })
        
        # Generate and save reports
        self._save_reports(reports)
        
        logging.info(f"Product combination completed:")
        logging.info(f"  - Combined products: {len(combined_products)}")
        logging.info(f"  - New products: {len(reports['new_products'])}")
        logging.info(f"  - Old products: {len(reports['old_products'])}")
        logging.info(f"  - Code changes: {len(reports['code_changes'])}")
        logging.info(f"  - Price increases: {len(reports['price_increases'])}")
        logging.info(f"  - Price decreases: {len(reports['price_decreases'])}")
        
        return combined_products, reports
    
    def _create_name_index(self, products: List[ExportProduct]) -> Dict[str, List[ExportProduct]]:
        """
        Create case-insensitive name index for products.
        
        Args:
            products: List of ExportProducts
            
        Returns:
            Dictionary mapping lowercase names to product lists
        """
        index = defaultdict(list)
        
        for product in products:
            if hasattr(product, 'nazev') and product.nazev:
                name_lower = product.nazev.strip().lower()
                index[name_lower].append(product)
        
        return dict(index)
    
    def _combine_product_groups(self, json_products: List[ExportProduct],
                               repaired_products: List[ExportProduct],
                               reports: Dict[str, Any]) -> List[ExportProduct]:
        """
        Merge products with same name, prioritizing repaired products.
        
        Args:
            json_products: Products from JSON
            repaired_products: Products from repaired conversion
            reports: Reports dictionary to update
            
        Returns:
            List of merged products
        """
        # Use repaired products as base (they have priority)
        merged_products = repaired_products.copy()
        
        # Check for code and price changes
        if json_products and repaired_products:
            json_main = self._find_main_product(json_products)
            repaired_main = self._find_main_product(repaired_products)
            
            if json_main and repaired_main:
                # Check code changes
                if (hasattr(json_main, 'kod') and hasattr(repaired_main, 'kod') and
                    json_main.kod != repaired_main.kod):
                    reports['code_changes'].append({
                        'nazev': repaired_main.nazev,
                        'old_kod': json_main.kod,
                        'new_kod': repaired_main.kod,
                        'url': getattr(repaired_main, 'url', '')
                    })
                
                # Check price changes
                if (hasattr(json_main, 'cena') and hasattr(repaired_main, 'cena')):
                    try:
                        old_price = float(json_main.cena) if json_main.cena else 0.0
                        new_price = float(repaired_main.cena) if repaired_main.cena else 0.0
                        
                        if old_price > 0 and new_price > 0 and old_price != new_price:
                            price_change = {
                                'nazev': repaired_main.nazev,
                                'kod': repaired_main.kod,
                                'old_price': old_price,
                                'new_price': new_price,
                                'difference': new_price - old_price,
                                'percentage': ((new_price - old_price) / old_price) * 100,
                                'url': getattr(repaired_main, 'url', '')
                            }
                            
                            if new_price > old_price:
                                reports['price_increases'].append(price_change)
                            else:
                                reports['price_decreases'].append(price_change)
                    except (ValueError, TypeError):
                        logging.warning(f"Could not compare prices for product: {repaired_main.nazev}")
        
        return merged_products
    
    def _find_main_product(self, products: List[ExportProduct]) -> ExportProduct:
        """
        Find main product in a list (ExportMainProduct or typ='produkt').
        
        Args:
            products: List of products
            
        Returns:
            Main product or None
        """
        for product in products:
            if isinstance(product, ExportMainProduct):
                return product
            elif hasattr(product, 'typ') and product.typ == 'produkt':
                return product
        
        # If no main product found, return first one
        return products[0] if products else None
    
    def _save_reports(self, reports: Dict[str, Any]):
        """
        Save all reports to CSV files in results directory.
        
        Args:
            reports: Dictionary containing report data
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save new products report
        if reports['new_products']:
            filename = f"nove_produkty_{timestamp}.csv"
            filepath = os.path.join(self.results_dir, filename)
            save_csv_file(reports['new_products'], filepath)
            logging.info(f"New products report saved: {filepath}")

        # Save old products report
        if reports['old_products']:
            filename = f"stare_produkty_{timestamp}.csv"
            filepath = os.path.join(self.results_dir, filename)
            save_csv_file(reports['old_products'], filepath)
            logging.info(f"Old products report saved: {filepath}")

        # Save code changes report
        if reports['code_changes']:
            filename = f"zmeny_kodu_{timestamp}.csv"
            filepath = os.path.join(self.results_dir, filename)
            save_csv_file(reports['code_changes'], filepath)
            logging.info(f"Code changes report saved: {filepath}")

        # Save price increases report
        if reports['price_increases']:
            filename = f"zdrazeni_{timestamp}.csv"
            filepath = os.path.join(self.results_dir, filename)
            save_csv_file(reports['price_increases'], filepath)
            logging.info(f"Price increases report saved: {filepath}")

        # Save price decreases report
        if reports['price_decreases']:
            filename = f"slevy_{timestamp}.csv"
            filepath = os.path.join(self.results_dir, filename)
            save_csv_file(reports['price_decreases'], filepath)
            logging.info(f"Price decreases report saved: {filepath}")
