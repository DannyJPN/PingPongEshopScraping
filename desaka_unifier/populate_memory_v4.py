#!/usr/bin/env python3
"""
Memory Population Script v4 - Using Validated Files

Prioritizes validated memory files as the primary source of truth.
Falls back to automatic classification only when needed.
"""

import csv
import re
from pathlib import Path
from typing import Dict, Set
from populate_memory_v3 import MemoryReprocessor, KNOWN_BRANDS, COLOR_VARIANTS, SIZE_VARIANTS, THICKNESS_PATTERNS, TYPE_KEYWORDS, PRODUCT_TYPE_MAPPING

class MemoryReprocessorV4(MemoryReprocessor):
    def __init__(self, base_dir: Path):
        super().__init__(base_dir)
        
        # Load validated mappings as priority
        self.validated_brands: Dict[str, str] = {}
        self.validated_types: Dict[str, str] = {}
        
        self._load_validated_memory()
    
    def _load_validated_memory(self):
        """Load manually validated memory files."""
        print("Loading validated memory files...")
        
        # Load validated brands
        brand_validated = self.memory_dir / "productBrandMemoryValidated.csv"
        if brand_validated.exists():
            with open(brand_validated, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) >= 2 and row[1] != "UNKNOWN":
                        self.validated_brands[row[0]] = row[1]
        
        # Load validated types
        type_validated = self.memory_dir / "productTypeMemoryValidated.csv"
        if type_validated.exists():
            with open(type_validated, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) >= 2 and row[1] != "UNKNOWN":
                        self.validated_types[row[0]] = row[1]
        
        print(f"Loaded {len(self.validated_brands)} validated brands, {len(self.validated_types)} validated types")
    
    def extract_brand(self, product_name: str) -> str:
        """Extract brand - check validated first."""
        # Priority 1: Validated memory
        if product_name in self.validated_brands:
            return self.validated_brands[product_name]
        
        # Priority 2: Automatic detection (from parent class)
        return super().extract_brand(product_name)
    
    def extract_product_type(self, product_name: str) -> str:
        """Extract product type - check validated first."""
        # Priority 1: Validated memory
        if product_name in self.validated_types:
            return self.validated_types[product_name]
        
        # Priority 2: Automatic detection (from parent class)
        return super().extract_product_type(product_name)


def main():
    base_dir = Path("/home/user/PingPongEshopScraping/desaka_unifier")
    
    reprocessor = MemoryReprocessorV4(base_dir)
    reprocessor.reprocess_all()
    
    print("\n" + "="*60)
    print("Reprocessing complete with validated memory!")
    print("="*60)


if __name__ == "__main__":
    main()
