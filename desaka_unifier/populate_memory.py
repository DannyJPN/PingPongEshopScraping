#!/usr/bin/env python3
"""
Memory Population Script

Populates missing entries in Czech memory CSV files based on MISSINGDETECTOR output.
Handles ProductBrandMemory_CS.csv, ProductModelMemory_CS.csv, and ProductTypeMemory_CS.csv.
"""

import csv
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
import unicodedata

# Known table tennis brands (from BrandCodeList.csv + common knowledge)
KNOWN_BRANDS = {
    'Adidas', 'Andro', 'Asics', 'Avalox', 'Barna', 'Bomb', 'Butterfly', 'Carlton',
    'Cornilleau', 'CTT', 'Dawei', 'Der Materialspezialist', 'DMS', 'Desaka', 'DHS',
    'Dingo Swiss', 'Donic', 'Dr. Neubauer', 'Friendship', 'Gambler', 'Gewo',
    'Giant Dragon', 'Globe', 'Hallmark', 'Hanno', 'Joola', 'Juic', 'Kokutaku',
    'KTL', 'Lear', 'Lion', 'Milky Way', 'Mizuno', 'Nexy', 'Nittaku', 'Palio',
    'PimplePark', 'Sanwei', 'Sauer&Troeger', 'Sauer & Troeger', 'Schildkröt',
    'Spinlord', 'SpinWay', 'SportSpin', 'Stiga', 'Sword', 'Tibhar', 'TSP',
    'Tuning', 'Turnier', 'Tuttle', 'Victas', 'VseNaStolniTenis', 'Xiom',
    'Xushaofa', 'Yasaka', 'Armstrong', 'Double Fish', 'FastPong', 'YinHe',
    'Blackstone', 'Contra', 'Enebe', 'Enlio', 'Exacto', 'FS', 'Imperial',
    'JapTec', 'SunFlex', 'Kingnik', 'Vulkan', 'LKT', 'SoulSpin', 'Sunflex',
    'vše na stolní tenis', 'MIZUNO'
}

# Product type terminology (German -> Czech)
PRODUCT_TYPE_MAPPING = {
    # German terms
    'belag': 'Potah',
    'holz': 'Dřevo',
    'schläger': 'Pálka',
    'ball': 'Míček',
    'bälle': 'Míčky',
    'hülle': 'Pouzdro',
    'tasche': 'Taška',
    'reiniger': 'Čistič',
    'schwamm': 'Houba',
    'kleber': 'Lepidlo',
    'kantenschutz': 'Ochranná páska',
    'shirt': 'Tričko',
    'trikot': 'Dres',
    'hose': 'Kraťasy',
    'short': 'Kraťasy',
    'shorts': 'Kraťasy',
    'schuhe': 'Boty',
    'netz': 'Síťka',
    'tisch': 'Stůl',
    'roboter': 'Robot',
    'handtuch': 'Ručník',
    'messlehre': 'Měrka',
    'jacke': 'Bunda',
    'trainingsjacke': 'Bunda',
    'windbreaker': 'Bunda',
    'schweißband': 'Potítko',
    'socken': 'Ponožky',
    'kappe': 'Čepice',
    'mütze': 'Čepice',
    'versiegelung': 'Ochranná fólie',
    'fólie': 'Ochranná fólie',
    'folie': 'Ochranná fólie',
    'case': 'Pouzdro',
    'bag': 'Taška',
    'batoh': 'Batoh',
    'rucksack': 'Batoh',
    'backpack': 'Batoh',

    # Czech terms (already correct)
    'potah': 'Potah',
    'dřevo': 'Dřevo',
    'pálka': 'Pálka',
    'míček': 'Míček',
    'míčky': 'Míčky',
    'pouzdro': 'Pouzdro',
    'taška': 'Taška',
    'čistič': 'Čistič',
    'houba': 'Houba',
    'lepidlo': 'Lepidlo',
    'ochranná páska': 'Ochranná páska',
    'tričko': 'Tričko',
    'dres': 'Dres',
    'kraťasy': 'Kraťasy',
    'boty': 'Boty',
    'síťka': 'Síťka',
    'stůl': 'Stůl',
    'robot': 'Robot',
    'ručník': 'Ručník',
    'měrka': 'Měrka',
    'bunda': 'Bunda',
    'potítko': 'Potítko',
    'ponožky': 'Ponožky',
    'čepice': 'Čepice',
    'batoh': 'Batoh',
    'sada': 'Sada',
    'set': 'Sada',
    'mince': 'Mince',
    'řetízek': 'Řetízek',
    'prkno': 'Dřevo',

    # English terms
    'rubber': 'Potah',
    'blade': 'Dřevo',
    'racket': 'Pálka',
    'paddle': 'Pálka',
    'cleaner': 'Čistič',
    'sponge': 'Houba',
    'glue': 'Lepidlo',
    'edge tape': 'Ochranná páska',
    'towel': 'Ručník',
    'net': 'Síťka',
    'table': 'Stůl',
    'gauge': 'Měrka',
    'jacket': 'Bunda',
    'cap': 'Čepice',
    'socks': 'Ponožky',
    'wristband': 'Potítko',
    'headband': 'Čelenka',
    'medaile': 'Medaile',
    'coin': 'Mince',
    'lak': 'Lak',
    'cement': 'Lepidlo',
    'sprej': 'Čistič',
    'bioclean': 'Čistič',
}


class MemoryPopulator:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.memory_dir = base_dir / "Memory"
        self.consolidated_dir = self.memory_dir / "Consolidated"

        # Load existing memory data
        self.existing_brands: Dict[str, str] = {}
        self.existing_models: Dict[str, str] = {}
        self.existing_types: Dict[str, str] = {}

        self._load_existing_memory()

    def _load_existing_memory(self):
        """Load existing memory files to understand patterns."""
        print("Loading existing memory files...")

        # Load brands
        brand_file = self.memory_dir / "ProductBrandMemory_CS.csv"
        if brand_file.exists():
            with open(brand_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) == 2:
                        self.existing_brands[row[0]] = row[1]

        # Load models
        model_file = self.memory_dir / "ProductModelMemory_CS.csv"
        if model_file.exists():
            with open(model_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) == 2:
                        self.existing_models[row[0]] = row[1]

        # Load types
        type_file = self.memory_dir / "ProductTypeMemory_CS.csv"
        if type_file.exists():
            with open(type_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) == 2:
                        self.existing_types[row[0]] = row[1]

        print(f"Loaded {len(self.existing_brands)} brands, {len(self.existing_models)} models, {len(self.existing_types)} types")

    def read_missing_file(self, file_path: Path) -> List[str]:
        """Read UTF-16LE encoded MISSING file."""
        try:
            with open(file_path, 'r', encoding='utf-16-le') as f:
                lines = [line.strip() for line in f if line.strip()]
                # Remove BOM if present
                if lines and lines[0].startswith('\ufeff'):
                    lines[0] = lines[0][1:]
                return lines
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return []

    def extract_brand(self, product_name: str) -> str:
        """Extract brand from product name."""
        # Check if already in memory
        if product_name in self.existing_brands:
            return self.existing_brands[product_name]

        # Handle "Brand-Product" format (VseNaStolniTenis pattern)
        if '-' in product_name:
            parts = product_name.split('-', 1)
            if parts[0].strip() in KNOWN_BRANDS:
                return parts[0].strip()

        # Try to find brand name in the product name
        product_lower = product_name.lower()

        # Sort brands by length (longest first) to match "Der Materialspezialist" before "Der"
        sorted_brands = sorted(KNOWN_BRANDS, key=len, reverse=True)

        for brand in sorted_brands:
            brand_lower = brand.lower()
            # Check if brand appears as a word in the product name
            if brand_lower in product_lower:
                # Verify it's a whole word match (not substring)
                pattern = r'\b' + re.escape(brand_lower) + r'\b'
                if re.search(pattern, product_lower):
                    return brand

        # Default to Desaka if no brand found
        return "Desaka"

    def extract_model(self, product_name: str, brand: str) -> str:
        """Extract model from product name."""
        # Check if already in memory
        if product_name in self.existing_models:
            return self.existing_models[product_name]

        # Remove brand name
        model = product_name
        if brand and brand != "Desaka":
            # Case-insensitive removal
            pattern = r'\b' + re.escape(brand) + r'\b'
            model = re.sub(pattern, '', model, flags=re.IGNORECASE)

        # Handle "Brand-Model" format
        if '-' in product_name:
            parts = product_name.split('-', 1)
            if len(parts) == 2 and parts[0].strip() in KNOWN_BRANDS:
                model = parts[1].strip()

        # Remove common product type prefixes/suffixes
        type_keywords = [
            'potah', 'dřevo', 'pálka', 'míček', 'míčky', 'pouzdro', 'taška',
            'belag', 'holz', 'schläger', 'ball', 'bälle', 'hülle', 'case',
            'rubber', 'blade', 'racket', 'paddle', 'sada', 'set', 'boty',
            'shoes', 'shirt', 'tričko', 'short', 'shorts', 'kraťasy', 'hose',
            'čistič', 'reiniger', 'cleaner', 'houba', 'schwamm', 'sponge',
            'batoh', 'bag', 'rucksack', 'backpack', 'bunda', 'jacket',
            'trainingsjacke', 'handtuch', 'towel', 'ručník', 'síťka', 'netz',
            'net', 'obal na pálku', 'schlägerhülle', 'medaile', 'mince'
        ]

        for keyword in type_keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            model = re.sub(pattern, '', model, flags=re.IGNORECASE)

        # Clean up extra spaces and punctuation
        model = re.sub(r'\s+', ' ', model).strip()
        model = model.strip('- ')

        return model if model else product_name

    def extract_product_type(self, product_name: str) -> str:
        """Extract product type in Czech."""
        # Check if already in memory
        if product_name in self.existing_types:
            return self.existing_types[product_name]

        product_lower = product_name.lower()

        # Direct keyword matching
        for keyword, czech_type in PRODUCT_TYPE_MAPPING.items():
            if keyword in product_lower:
                return czech_type

        # Special patterns
        if any(x in product_lower for x in ['noppen', 'pips', 'long pips', 'anti']):
            return 'Potah'

        if any(x in product_lower for x in ['carbon', 'offensive', 'defensive', 'all+', 'off+', 'off-', 'def']):
            return 'Dřevo'

        if 'cement' in product_lower or 'glue' in product_lower:
            return 'Lepidlo'

        if 'clean' in product_lower and 'mist' in product_lower:
            return 'Čistič'

        if any(x in product_lower for x in ['ausgleichgewicht', 'balancer', 'weight']):
            return 'Vyvažovací závaží'

        if 'čelenka' in product_lower or 'headband' in product_lower:
            return 'Čelenka'

        if 'lakování' in product_lower or 'varnish' in product_lower:
            return 'Lakování'

        if 'lepení' in product_lower and 'potah' in product_lower:
            return 'Lepení'

        # Default fallback
        return 'Ostatní'

    def process_missing_file(self, missing_file: Path, memory_type: str) -> List[Tuple[str, str]]:
        """Process a MISSING file and return KEY-VALUE pairs."""
        print(f"\nProcessing {missing_file.name}...")

        keys = self.read_missing_file(missing_file)
        print(f"Found {len(keys)} missing entries")

        results = []

        for key in keys:
            if not key or key.startswith('\ufeff'):
                continue

            # Clean BOM if present
            key = key.lstrip('\ufeff')

            if memory_type == 'ProductBrandMemory_CS.csv':
                value = self.extract_brand(key)
            elif memory_type == 'ProductModelMemory_CS.csv':
                brand = self.extract_brand(key)
                value = self.extract_model(key, brand)
            elif memory_type == 'ProductTypeMemory_CS.csv':
                value = self.extract_product_type(key)
            else:
                continue

            results.append((key, value))

        return results

    def append_to_memory_file(self, memory_file: Path, entries: List[Tuple[str, str]]):
        """Append entries to memory CSV file."""
        if not entries:
            return

        print(f"Appending {len(entries)} entries to {memory_file.name}...")

        # Read existing entries to avoid duplicates
        existing_keys = set()
        if memory_file.exists():
            with open(memory_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) >= 1:
                        existing_keys.add(row[0])

        # Filter out duplicates
        new_entries = [(k, v) for k, v in entries if k not in existing_keys]

        if not new_entries:
            print(f"No new entries to add (all already exist)")
            return

        # Append to file
        with open(memory_file, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            for key, value in new_entries:
                writer.writerow([key, value])

        print(f"Added {len(new_entries)} new entries")

    def process_all(self):
        """Process all MISSING files."""
        memory_types = [
            'ProductBrandMemory_CS.csv',
            'ProductModelMemory_CS.csv',
            'ProductTypeMemory_CS.csv'
        ]

        for memory_type in memory_types:
            print(f"\n{'='*60}")
            print(f"Processing {memory_type}")
            print(f"{'='*60}")

            consolidated_dir = self.consolidated_dir / memory_type
            if not consolidated_dir.exists():
                print(f"Directory not found: {consolidated_dir}")
                continue

            missing_files = list(consolidated_dir.glob("*_MISSING.txt"))
            print(f"Found {len(missing_files)} MISSING files")

            all_entries = []

            for missing_file in sorted(missing_files):
                entries = self.process_missing_file(missing_file, memory_type)
                all_entries.extend(entries)

            # Append to memory file
            memory_file = self.memory_dir / memory_type
            self.append_to_memory_file(memory_file, all_entries)

            print(f"\nTotal entries processed for {memory_type}: {len(all_entries)}")


def main():
    base_dir = Path("/home/user/PingPongEshopScraping/desaka_unifier")

    populator = MemoryPopulator(base_dir)
    populator.process_all()

    print("\n" + "="*60)
    print("Memory population complete!")
    print("="*60)


if __name__ == "__main__":
    main()
