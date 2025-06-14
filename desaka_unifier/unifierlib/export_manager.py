"""
Export manager module for generating comprehensive product reports.

This module handles exporting combined products to various formats (CSV, XLS, XLSX)
and creating detailed reports organized by different criteria (type, category, brand).

Key functionality:
- Export to CSV, XLS, XLSX formats
- Create comprehensive reports (all products, new products only)
- Generate detailed reports by product type, category, brand
- Create combination reports (type-brand, type-category, category-brand, all three)
- Organize exports in timestamped directories
"""

import os
import logging
from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict
from .export_product import ExportProduct, ExportMainProduct
from shared.file_ops import save_csv_file, ensure_directory_exists


class ExportManager:
    """
    Handles comprehensive export of products to various formats and structures.
    """
    
    def __init__(self, export_dir: str):
        """
        Initialize export manager.
        
        Args:
            export_dir (str): Base export directory path
        """
        self.export_dir = export_dir
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.reports_dir = os.path.join(export_dir, f"Reporty_{self.timestamp}")
        
        # Ensure reports directory exists
        ensure_directory_exists(self.reports_dir)
        
    def export_comprehensive_reports(self, combined_products: List[ExportProduct], 
                                   new_products: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Export comprehensive reports in multiple formats and organizations.
        
        Args:
            combined_products: All combined products
            new_products: List of new product data for filtering
            
        Returns:
            Dictionary with paths to created files
        """
        logging.info("Starting comprehensive export process...")
        
        created_files = {}
        
        # Convert products to CSV data format
        all_products_data = self._products_to_csv_data(combined_products)
        
        # Filter new products data
        new_product_codes = {item['kod'] for item in new_products if 'kod' in item}
        new_products_data = [
            product for product in all_products_data 
            if product.get('kod', '') in new_product_codes
        ]
        
        # 1. Export main reports (all formats)
        created_files.update(self._export_main_reports(all_products_data, new_products_data))
        
        # 2. Export detailed reports by categories
        created_files.update(self._export_detailed_reports(all_products_data))
        
        logging.info(f"Comprehensive export completed. Created {len(created_files)} files.")
        return created_files
    
    def _products_to_csv_data(self, products: List[ExportProduct]) -> List[Dict[str, Any]]:
        """
        Convert ExportProduct objects to CSV-compatible data.
        
        Args:
            products: List of ExportProduct objects
            
        Returns:
            List of dictionaries for CSV export
        """
        csv_data = []
        
        for product in products:
            row = {}
            # Get all field names from the export product
            fieldnames = [attr for attr in dir(product) if not attr.startswith('_') and not callable(getattr(product, attr))]
            for field in fieldnames:
                value = getattr(product, field, '')
                row[field] = value
            csv_data.append(row)
        
        return csv_data
    
    def _export_main_reports(self, all_products_data: List[Dict[str, Any]], 
                           new_products_data: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Export main reports (Report-all and Report-new) in multiple formats.
        
        Args:
            all_products_data: All products data
            new_products_data: New products data only
            
        Returns:
            Dictionary with created file paths
        """
        created_files = {}
        
        # Export Report-all (all products)
        if all_products_data:
            # CSV format
            csv_path = os.path.join(self.reports_dir, f"Report-all_{self.timestamp}.csv")
            save_csv_file(all_products_data, csv_path)
            created_files['report_all_csv'] = csv_path
            logging.info(f"Report-all CSV saved: {csv_path}")
            
            # XLS and XLSX formats (using pandas if available)
            try:
                import pandas as pd
                df = pd.DataFrame(all_products_data)
                
                # XLS format
                xls_path = os.path.join(self.reports_dir, f"Report-all_{self.timestamp}.xls")
                df.to_excel(xls_path, index=False, engine='xlwt')
                created_files['report_all_xls'] = xls_path
                logging.info(f"Report-all XLS saved: {xls_path}")
                
                # XLSX format
                xlsx_path = os.path.join(self.reports_dir, f"Report-all_{self.timestamp}.xlsx")
                df.to_excel(xlsx_path, index=False, engine='openpyxl')
                created_files['report_all_xlsx'] = xlsx_path
                logging.info(f"Report-all XLSX saved: {xlsx_path}")
                
            except ImportError:
                logging.warning("pandas not available - skipping XLS/XLSX export for Report-all")
            except Exception as e:
                logging.error(f"Error creating Excel files for Report-all: {str(e)}")
        
        # Export Report-new (new products only)
        if new_products_data:
            # CSV format
            csv_path = os.path.join(self.reports_dir, f"Report-new_{self.timestamp}.csv")
            save_csv_file(new_products_data, csv_path)
            created_files['report_new_csv'] = csv_path
            logging.info(f"Report-new CSV saved: {csv_path}")
            
            # XLS and XLSX formats
            try:
                import pandas as pd
                df = pd.DataFrame(new_products_data)
                
                # XLS format
                xls_path = os.path.join(self.reports_dir, f"Report-new_{self.timestamp}.xls")
                df.to_excel(xls_path, index=False, engine='xlwt')
                created_files['report_new_xls'] = xls_path
                logging.info(f"Report-new XLS saved: {xls_path}")
                
                # XLSX format
                xlsx_path = os.path.join(self.reports_dir, f"Report-new_{self.timestamp}.xlsx")
                df.to_excel(xlsx_path, index=False, engine='openpyxl')
                created_files['report_new_xlsx'] = xlsx_path
                logging.info(f"Report-new XLSX saved: {xlsx_path}")
                
            except ImportError:
                logging.warning("pandas not available - skipping XLS/XLSX export for Report-new")
            except Exception as e:
                logging.error(f"Error creating Excel files for Report-new: {str(e)}")
        
        return created_files
    
    def _export_detailed_reports(self, all_products_data: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Export detailed reports organized by various criteria.
        
        Args:
            all_products_data: All products data
            
        Returns:
            Dictionary with created file paths
        """
        created_files = {}
        
        # Create Detail_reporty directory
        detail_dir = os.path.join(self.reports_dir, "Detailni_reporty")
        ensure_directory_exists(detail_dir)

        # Group products by different criteria
        products_by_type = self._group_by_field(all_products_data, 'typ')
        products_by_brand = self._group_by_field(all_products_data, 'vyrobce')
        products_by_category = self._group_by_category(all_products_data)

        # Export by product type - one file per type
        type_dir = os.path.join(detail_dir, "Podle_typu")
        ensure_directory_exists(type_dir)
        created_files.update(self._export_individual_reports(products_by_type, type_dir, "typ"))

        # Export by brand - one file per brand
        brand_dir = os.path.join(detail_dir, "Podle_znacky")
        ensure_directory_exists(brand_dir)
        created_files.update(self._export_individual_reports(products_by_brand, brand_dir, "znacka"))

        # Export by category - one file per category
        category_dir = os.path.join(detail_dir, "Podle_kategorie")
        ensure_directory_exists(category_dir)
        created_files.update(self._export_individual_reports(products_by_category, category_dir, "kategorie"))
        
        # Export combination reports
        created_files.update(self._export_combination_reports(all_products_data, detail_dir))
        
        return created_files

    def _export_individual_reports(self, grouped_data: Dict[str, List[Dict[str, Any]]],
                                  output_dir: str, group_type: str) -> Dict[str, str]:
        """
        Export individual reports - one file per group (brand, type, category).

        Args:
            grouped_data: Grouped products data
            output_dir: Output directory
            group_type: Type of grouping for filename

        Returns:
            Dictionary with created file paths
        """
        created_files = {}

        for group_name, products in grouped_data.items():
            if products:
                # Sanitize filename
                safe_name = self._sanitize_filename(group_name)
                filename = f"{safe_name}_{self.timestamp}.csv"
                filepath = os.path.join(output_dir, filename)

                save_csv_file(products, filepath)
                created_files[f"{group_type}_{safe_name}"] = filepath
                logging.info(f"Individual report saved: {filepath} ({len(products)} products)")

        return created_files

    def _group_by_field(self, products_data: List[Dict[str, Any]], field: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group products by a specific field.
        
        Args:
            products_data: Products data
            field: Field name to group by
            
        Returns:
            Dictionary mapping field values to product lists
        """
        grouped = defaultdict(list)
        
        for product in products_data:
            value = product.get(field, 'Unknown')
            if not value or value in ['', '#']:
                value = 'Unknown'
            grouped[str(value).strip()].append(product)
        
        return dict(grouped)
    
    def _group_by_category(self, products_data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group products by category (using last part of category name).
        
        Args:
            products_data: Products data
            
        Returns:
            Dictionary mapping category names to product lists
        """
        grouped = defaultdict(list)
        
        for product in products_data:
            category = product.get('kategorie_id', 'Unknown')
            if not category or category in ['', '#']:
                category = 'Unknown'
            else:
                # Use last part of category for naming
                category_parts = str(category).split('/')
                category = category_parts[-1].strip() if category_parts else 'Unknown'
            
            grouped[category].append(product)
        
        return dict(grouped)
    
    def _export_grouped_reports(self, grouped_data: Dict[str, List[Dict[str, Any]]], 
                              output_dir: str, group_type: str) -> Dict[str, str]:
        """
        Export grouped reports to files.
        
        Args:
            grouped_data: Grouped products data
            output_dir: Output directory
            group_type: Type of grouping for filename
            
        Returns:
            Dictionary with created file paths
        """
        created_files = {}
        
        for group_name, products in grouped_data.items():
            if products:
                # Sanitize filename
                safe_name = self._sanitize_filename(group_name)
                filename = f"Report_{safe_name}_{self.timestamp}.csv"
                filepath = os.path.join(output_dir, filename)

                save_csv_file(products, filepath)
                created_files[f"{group_type}_{safe_name}"] = filepath
                logging.debug(f"Grouped report saved: {filepath} ({len(products)} products)")
        
        return created_files
    
    def _export_combination_reports(self, all_products_data: List[Dict[str, Any]], 
                                  detail_dir: str) -> Dict[str, str]:
        """
        Export combination reports (type-brand, type-category, etc.).
        
        Args:
            all_products_data: All products data
            detail_dir: Detail reports directory
            
        Returns:
            Dictionary with created file paths
        """
        created_files = {}
        
        # Group by combinations
        combinations = [
            ('typ', 'vyrobce', 'Typ_Znacka'),
            ('typ', 'kategorie_id', 'Typ_Kategorie'),
            ('vyrobce', 'kategorie_id', 'Znacka_Kategorie'),
            ('typ', 'vyrobce', 'kategorie_id', 'Typ_Znacka_Kategorie')
        ]

        for combination in combinations:
            if len(combination) == 3:  # Two fields
                field1, field2, dir_name = combination
                combo_dir = os.path.join(detail_dir, f"Podle_{dir_name}")
                ensure_directory_exists(combo_dir)

                grouped = self._group_by_combination_two(all_products_data, field1, field2)
                created_files.update(self._export_grouped_reports(grouped, combo_dir, dir_name.lower()))

            elif len(combination) == 4:  # Three fields
                field1, field2, field3, dir_name = combination
                combo_dir = os.path.join(detail_dir, f"Podle_{dir_name}")
                ensure_directory_exists(combo_dir)

                grouped = self._group_by_combination_three(all_products_data, field1, field2, field3)
                created_files.update(self._export_grouped_reports(grouped, combo_dir, dir_name.lower()))
        
        return created_files
    
    def _group_by_combination_two(self, products_data: List[Dict[str, Any]], 
                                field1: str, field2: str) -> Dict[str, List[Dict[str, Any]]]:
        """Group products by combination of two fields."""
        grouped = defaultdict(list)
        
        for product in products_data:
            value1 = product.get(field1, 'Unknown')
            value2 = product.get(field2, 'Unknown')
            
            if not value1 or value1 in ['', '#']:
                value1 = 'Unknown'
            if not value2 or value2 in ['', '#']:
                value2 = 'Unknown'
            
            # For category, use last part
            if field2 == 'kategorie_id' and value2 != 'Unknown':
                category_parts = str(value2).split('/')
                value2 = category_parts[-1].strip() if category_parts else 'Unknown'
            
            combo_key = f"{value1}_{value2}"
            grouped[combo_key].append(product)
        
        return dict(grouped)
    
    def _group_by_combination_three(self, products_data: List[Dict[str, Any]], 
                                  field1: str, field2: str, field3: str) -> Dict[str, List[Dict[str, Any]]]:
        """Group products by combination of three fields."""
        grouped = defaultdict(list)
        
        for product in products_data:
            value1 = product.get(field1, 'Unknown')
            value2 = product.get(field2, 'Unknown')
            value3 = product.get(field3, 'Unknown')
            
            if not value1 or value1 in ['', '#']:
                value1 = 'Unknown'
            if not value2 or value2 in ['', '#']:
                value2 = 'Unknown'
            if not value3 or value3 in ['', '#']:
                value3 = 'Unknown'
            
            # For category, use last part
            if field3 == 'kategorie_id' and value3 != 'Unknown':
                category_parts = str(value3).split('/')
                value3 = category_parts[-1].strip() if category_parts else 'Unknown'
            
            combo_key = f"{value1}_{value2}_{value3}"
            grouped[combo_key].append(product)
        
        return dict(grouped)
    
    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize string for use in filename.
        
        Args:
            name: Original name
            
        Returns:
            Sanitized filename-safe string
        """
        # Replace problematic characters
        safe_name = str(name).replace('/', '_').replace('\\', '_').replace(':', '_')
        safe_name = safe_name.replace('<', '_').replace('>', '_').replace('|', '_')
        safe_name = safe_name.replace('?', '_').replace('*', '_').replace('"', '_')
        safe_name = safe_name.strip()
        
        # Limit length
        if len(safe_name) > 50:
            safe_name = safe_name[:50]
        
        return safe_name if safe_name else 'Unknown'
