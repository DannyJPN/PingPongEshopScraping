#!/usr/bin/env python3
"""
Memory Population Script v2 - Fixed Version

Fixes critical issues:
1. Removes "Ostatní" fallback - always identifies specific type
2. Strips variants (colors, sizes, thicknesses) from models
3. Removes brands and type keywords from models
"""

import csv
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Known table tennis brands
KNOWN_BRANDS = {
    'Adidas', 'Andro', 'Asics', 'Avalox', 'Barna', 'Bomb', 'Butterfly', 'Carlton',
    'Cornilleau', 'CTT', 'Dawei', 'Der Materialspezialist', 'DMS', 'Desaka', 'DHS',
    'Dingo Swiss', 'Donic', 'Dr. Neubauer', 'Friendship', 'Gambler', 'Gewo',
    'Giant Dragon', 'Globe', 'Hallmark', 'Hanno', 'Joola', 'Juic', 'Kokutaku',
    'KTL', 'Lear', 'Lion', 'Milky Way', 'Mizuno', 'Nexy', 'Nittaku', 'Palio',
    'PimplePark', 'Sanwei', 'Sauer&Troeger', 'Sauer & Troeger', 'Sauer&Tröger',
    'Sauer & Tröger', 'Schildkröt', 'Spinlord', 'SpinWay', 'SportSpin', 'Stiga',
    'Sword', 'Tibhar', 'TSP', 'Tuning', 'Turnier', 'Tuttle', 'Victas',
    'VseNaStolniTenis', 'Xiom', 'Xushaofa', 'Yasaka', 'Armstrong', 'Double Fish',
    'FastPong', 'YinHe', 'Blackstone', 'Contra', 'Enebe', 'Enlio', 'Exacto',
    'FS', 'Imperial', 'JapTec', 'SunFlex', 'Sunflex', 'Kingnik', 'Vulkan', 'LKT',
    'SoulSpin', 'vše na stolní tenis', 'MIZUNO', 'JOOLA', 'BUTTERFLY', 'DONIC',
    'STIGA', 'ANDRO', 'andro'
}

# Color variants (to remove from models)
COLOR_VARIANTS = [
    # German
    'schwarz', 'rot', 'blau', 'grün', 'gelb', 'weiß', 'weiss', 'orange',
    'grau', 'pink', 'lila', 'violett', 'silber', 'gold', 'braun', 'türkis',
    'hellblau', 'dunkelblau', 'hellgrau', 'dunkelgrau', 'hellgrün', 'multicolor',
    # English
    'black', 'red', 'blue', 'green', 'yellow', 'white', 'orange', 'grey', 'gray',
    'purple', 'violet', 'silver', 'gold', 'brown', 'turquoise', 'pink',
    # Czech
    'černý', 'červený', 'modrý', 'zelený', 'žlutý', 'bílý', 'oranžový',
    'šedý', 'růžový', 'fialový', 'stříbrný', 'zlatý', 'hnědý'
]

# Size variants (to remove from models)
SIZE_VARIANTS = [
    'XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL', 'XXXXL', 'XXXXXL', 'XXXXXXL',
    '3XL', '4XL', '5XL', '6XL', '7XL',
    'XXXS', 'XXXXS', 'XXXXXS'
]

# Thickness variants (to remove from models)
THICKNESS_PATTERNS = [
    r'\b\d+[,\.]\d+\s*mm\b',  # 1,5 mm, 2.0 mm
    r'\bOX\b',  # OX (no sponge)
    r'\b\d+°\b',  # 39°, 40°
    r'\b\d+[,\.]\d+mm\b',  # 1,5mm (no space)
]

# Type keywords (to remove from models)
TYPE_KEYWORDS = [
    # German
    'belag', 'holz', 'schläger', 'ball', 'bälle', 'hülle', 'tasche',
    'reiniger', 'schwamm', 'kleber', 'kantenschutz', 'kantenband',
    'shirt', 'trikot', 'hose', 'short', 'shorts', 'schuhe', 'netz',
    'tisch', 'roboter', 'handtuch', 'messlehre', 'jacke', 'trainingsjacke',
    'windbreaker', 'schweißband', 'socken', 'kappe', 'mütze',
    'versiegelung', 'fólie', 'folie', 'anzughose', 'anzugjacke',
    'hemd', 'hoodie', 'longsleeve', 'poloshirt', 'tanktop', 'weste',
    'andruckrolle', 'hardcase', 'softcase', 'tischtennisschläger',
    # English
    'rubber', 'blade', 'racket', 'paddle', 'cleaner', 'sponge', 'glue',
    'edge tape', 'towel', 'net', 'table', 'gauge', 'jacket', 'cap',
    'socks', 'wristband', 'headband', 'case', 'bag', 'shirt',
    # Czech
    'potah', 'dřevo', 'pálka', 'míček', 'míčky', 'pouzdro', 'taška',
    'čistič', 'houba', 'lepidlo', 'ochranná páska', 'tričko', 'dres',
    'kraťasy', 'boty', 'síťka', 'stůl', 'robot', 'ručník', 'měrka',
    'bunda', 'potítko', 'ponožky', 'čepice', 'batoh', 'mikina',
    'obal na pálku', 'prkno'
]

# Comprehensive product type mappings
PRODUCT_TYPE_MAPPING = {
    # Rubber/Potah
    'belag': 'Potah', 'rubber': 'Potah', 'potah': 'Potah',
    'noppen': 'Potah', 'anti': 'Potah', 'pips': 'Potah',

    # Blade/Dřevo
    'holz': 'Dřevo', 'blade': 'Dřevo', 'dřevo': 'Dřevo', 'prkno': 'Dřevo',
    'carbon': 'Dřevo', 'offensive': 'Dřevo', 'defensive': 'Dřevo',

    # Racket/Pálka
    'schläger': 'Pálka', 'tischtennisschläger': 'Pálka',
    'racket': 'Pálka', 'paddle': 'Pálka', 'pálka': 'Pálka',

    # Balls/Míčky
    'ball': 'Míček', 'bälle': 'Míčky', 'míček': 'Míček', 'míčky': 'Míčky',

    # Case/Pouzdro
    'hülle': 'Pouzdro', 'case': 'Pouzdro', 'pouzdro': 'Pouzdro',
    'hardcase': 'Pouzdro', 'softcase': 'Pouzdro', 'schlägerhülle': 'Pouzdro',

    # Bag/Taška/Batoh
    'tasche': 'Taška', 'bag': 'Taška', 'taška': 'Taška',
    'rucksack': 'Batoh', 'backpack': 'Batoh', 'batoh': 'Batoh',

    # Cleaner/Čistič
    'reiniger': 'Čistič', 'cleaner': 'Čistič', 'čistič': 'Čistič',
    'clean': 'Čistič', 'bioclean': 'Čistič', 'mist': 'Čistič',

    # Sponge/Houba
    'schwamm': 'Houba', 'sponge': 'Houba', 'houba': 'Houba',

    # Glue/Lepidlo
    'kleber': 'Lepidlo', 'glue': 'Lepidlo', 'lepidlo': 'Lepidlo',
    'cement': 'Lepidlo',

    # Edge Tape/Ochranná páska
    'kantenschutz': 'Ochranná páska', 'kantenband': 'Ochranná páska',
    'edge tape': 'Ochranná páska', 'ochranná páska': 'Ochranná páska',
    'páska': 'Ochranná páska',

    # Protective film/Ochranná fólie
    'versiegelung': 'Ochranná fólie', 'fólie': 'Ochranná fólie',
    'folie': 'Ochranná fólie', 'seal': 'Ochranná fólie',

    # Clothing - Shirt/Tričko/Dres
    'shirt': 'Tričko', 'trikot': 'Dres', 'tričko': 'Tričko', 'dres': 'Dres',
    'hemd': 'Tričko', 'poloshirt': 'Tričko', 'tanktop': 'Tričko',

    # Clothing - Shorts/Kraťasy
    'short': 'Kraťasy', 'shorts': 'Kraťasy', 'hose': 'Kraťasy',
    'kraťasy': 'Kraťasy',

    # Clothing - Shoes/Boty
    'schuhe': 'Boty', 'shoes': 'Boty', 'boty': 'Boty',

    # Clothing - Hoodie/Mikina
    'hoodie': 'Mikina', 'mikina': 'Mikina',

    # Clothing - Jacket/Bunda
    'jacke': 'Bunda', 'jacket': 'Bunda', 'bunda': 'Bunda',
    'trainingsjacke': 'Bunda', 'windbreaker': 'Bunda',
    'anzugjacke': 'Bunda', 'weste': 'Bunda',

    # Clothing - Pants/Kalhoty
    'anzughose': 'Kalhoty', 'pants': 'Kalhoty', 'kalhoty': 'Kalhoty',

    # Clothing - Longsleeve
    'longsleeve': 'Tričko',

    # Clothing - Socks/Ponožky
    'socken': 'Ponožky', 'socks': 'Ponožky', 'ponožky': 'Ponožky',

    # Clothing - Cap/Čepice
    'kappe': 'Čepice', 'mütze': 'Čepice', 'cap': 'Čepice', 'čepice': 'Čepice',

    # Accessories - Headband/Čelenka
    'schweißband': 'Potítko', 'wristband': 'Potítko', 'potítko': 'Potítko',
    'headband': 'Čelenka', 'čelenka': 'Čelenka', 'stirnband': 'Čelenka',

    # Net/Síťka
    'netz': 'Síťka', 'net': 'Síťka', 'síťka': 'Síťka',

    # Table/Stůl
    'tisch': 'Stůl', 'table': 'Stůl', 'stůl': 'Stůl',

    # Robot
    'roboter': 'Robot', 'robot': 'Robot',

    # Towel/Ručník
    'handtuch': 'Ručník', 'towel': 'Ručník', 'ručník': 'Ručník',

    # Gauge/Měrka
    'messlehre': 'Měrka', 'gauge': 'Měrka', 'měrka': 'Měrka',

    # Roller/Váleček
    'andruckrolle': 'Váleček', 'roller': 'Váleček',

    # Set/Sada
    'sada': 'Sada', 'set': 'Sada',

    # Coin/Mince
    'mince': 'Mince', 'coin': 'Mince', 'münze': 'Mince',

    # Chain/Řetízek
    'řetízek': 'Řetízek', 'kettchen': 'Řetízek', 'chain': 'Řetízek',
    'ersatzkettchen': 'Řetízek',

    # Varnish/Lak
    'lak': 'Lak', 'lackierung': 'Lak', 'varnish': 'Lak', 'lakování': 'Lak',

    # Medal/Medaile
    'medaile': 'Medaile', 'medaille': 'Medaile', 'medal': 'Medaile',

    # String/Schnur
    'schnur': 'Šňůra', 'ersatzschnur': 'Šňůra', 'string': 'Šňůra',

    # Skirt/Sukně
    'rock': 'Sukně', 'skirt': 'Sukně', 'sukně': 'Sukně',

    # Cover/Plachta
    'plachta': 'Plachta', 'abdeckung': 'Plachta', 'cover': 'Plachta',

    # Collector/Sběrač
    'sběrač': 'Sběrač', 'sammler': 'Sběrač', 'collector': 'Sběrač',

    # Umpire chair/Stolek pro rozhodčí
    'schiedsrichterstuhl': 'Stolek pro rozhodčí', 'stolek': 'Stolek pro rozhodčí',

    # Scoreboard/Počítadlo
    'počítadlo': 'Počítadlo', 'zählgerät': 'Počítadlo', 'scoreboard': 'Počítadlo',

    # Basket/Koš
    'koš': 'Koš', 'korb': 'Koš', 'basket': 'Koš',

    # Board/Deska
    'deska': 'Deska', 'brett': 'Deska', 'board': 'Deska',

    # Machine/Stroj
    'stroj': 'Stroj', 'maschine': 'Stroj', 'machine': 'Stroj',

    # Holder/Držák
    'držák': 'Držák', 'halter': 'Držák', 'holder': 'Držák',

    # Service/Lepení/Lakování (services)
    'lepení': 'Lepení', 'gluing': 'Lepení',

    # Weight/Závaží
    'balancer': 'Vyvažovací závaží', 'ausgleichgewicht': 'Vyvažovací závaží',
    'weight': 'Vyvažovací závaží',

    # Mini table
    'mini stůl': 'Mini stůl', 'mini table': 'Mini stůl',

    # Voucher/Poukaz
    'voucher': 'Poukaz', 'poukaz': 'Poukaz', 'gutschein': 'Poukaz',

    # Gift/Dárek
    'gift': 'Dárek', 'dárek': 'Dárek', 'geschenk': 'Dárek',
}


class MemoryPopulatorV2:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.memory_dir = base_dir / "Memory"
        self.consolidated_dir = self.memory_dir / "Consolidated"

        self.existing_brands: Dict[str, str] = {}
        self.existing_models: Dict[str, str] = {}
        self.existing_types: Dict[str, str] = {}

        self._load_existing_memory()

    def _load_existing_memory(self):
        """Load existing memory files."""
        print("Loading existing memory files...")

        brand_file = self.memory_dir / "ProductBrandMemory_CS.csv"
        if brand_file.exists():
            with open(brand_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    if len(row) == 2:
                        self.existing_brands[row[0]] = row[1]

        model_file = self.memory_dir / "ProductModelMemory_CS.csv"
        if model_file.exists():
            with open(model_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    if len(row) == 2:
                        self.existing_models[row[0]] = row[1]

        type_file = self.memory_dir / "ProductTypeMemory_CS.csv"
        if type_file.exists():
            with open(type_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    if len(row) == 2:
                        self.existing_types[row[0]] = row[1]

        print(f"Loaded {len(self.existing_brands)} brands, {len(self.existing_models)} models, {len(self.existing_types)} types")

    def read_missing_file(self, file_path: Path) -> List[str]:
        """Read UTF-16LE encoded MISSING file."""
        try:
            with open(file_path, 'r', encoding='utf-16-le') as f:
                lines = [line.strip() for line in f if line.strip()]
                if lines and lines[0].startswith('\ufeff'):
                    lines[0] = lines[0][1:]
                return lines
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return []

    def extract_brand(self, product_name: str) -> str:
        """Extract brand from product name."""
        if product_name in self.existing_brands:
            return self.existing_brands[product_name]

        # Handle "Brand-Product" format
        if '-' in product_name:
            parts = product_name.split('-', 1)
            brand_candidate = parts[0].strip()
            if brand_candidate in KNOWN_BRANDS or brand_candidate.lower() in [b.lower() for b in KNOWN_BRANDS]:
                # Find the actual brand with correct casing
                for brand in KNOWN_BRANDS:
                    if brand.lower() == brand_candidate.lower():
                        return brand
                return brand_candidate

        product_lower = product_name.lower()
        sorted_brands = sorted(KNOWN_BRANDS, key=len, reverse=True)

        for brand in sorted_brands:
            brand_lower = brand.lower()
            if brand_lower in product_lower:
                pattern = r'\b' + re.escape(brand_lower) + r'\b'
                if re.search(pattern, product_lower):
                    return brand

        return "Desaka"

    def strip_variants(self, text: str) -> str:
        """Remove color, size, and thickness variants from text."""
        result = text

        # Remove thickness patterns (1,5 mm, OX, etc.)
        for pattern in THICKNESS_PATTERNS:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)

        # Remove colors
        for color in COLOR_VARIANTS:
            pattern = r'\b' + re.escape(color) + r'\b'
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)

        # Remove sizes (must be whole word to avoid removing X from model names)
        for size in SIZE_VARIANTS:
            # Only remove if it's at the end or followed by space/punctuation
            pattern = r'\b' + re.escape(size) + r'\b'
            result = re.sub(pattern, '', result)

        # Clean up multiple spaces and trim
        result = re.sub(r'\s+', ' ', result).strip()
        result = result.strip('- ,/')

        return result

    def extract_model(self, product_name: str, brand: str) -> str:
        """Extract clean model name without brand, type, or variants."""
        if product_name in self.existing_models:
            return self.existing_models[product_name]

        model = product_name

        # Remove brand name (case insensitive)
        if brand and brand != "Desaka":
            pattern = r'\b' + re.escape(brand) + r'\b'
            model = re.sub(pattern, '', model, flags=re.IGNORECASE)

        # Handle "Brand-Model" format
        if '-' in product_name:
            parts = product_name.split('-', 1)
            if len(parts) == 2:
                brand_candidate = parts[0].strip()
                if brand_candidate in KNOWN_BRANDS or brand_candidate.lower() in [b.lower() for b in KNOWN_BRANDS]:
                    model = parts[1].strip()

        # Remove type keywords
        for keyword in TYPE_KEYWORDS:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            model = re.sub(pattern, '', model, flags=re.IGNORECASE)

        # Strip variants (colors, sizes, thicknesses)
        model = self.strip_variants(model)

        # Clean up
        model = re.sub(r'\s+', ' ', model).strip()
        model = model.strip('- ,/')

        return model if model else product_name

    def extract_product_type(self, product_name: str) -> str:
        """Extract product type in Czech - NO FALLBACK to Ostatní."""
        if product_name in self.existing_types:
            return self.existing_types[product_name]

        product_lower = product_name.lower()

        # Direct keyword matching (longest first)
        sorted_keywords = sorted(PRODUCT_TYPE_MAPPING.keys(), key=len, reverse=True)
        for keyword in sorted_keywords:
            if keyword in product_lower:
                return PRODUCT_TYPE_MAPPING[keyword]

        # Special multi-word patterns
        if 'obal na pálku' in product_lower or 'schlägerhülle' in product_lower:
            return 'Pouzdro'

        if 'stolek pro rozhodčí' in product_lower or 'schiedsrichterstuhl' in product_lower:
            return 'Stolek pro rozhodčí'

        if 'vyvažovací závaží' in product_lower or 'ausgleichgewicht' in product_lower:
            return 'Vyvažovací závaží'

        if 'mini stůl' in product_lower or 'mini table' in product_lower:
            return 'Mini stůl'

        # Specific product patterns
        if any(x in product_lower for x in ['narucross', 'fastarc', 'hurricane', 'tenergy', 'dignics']):
            return 'Potah'

        if any(x in product_lower for x in ['acoustic', 'viscaria', 'timo boll alc', 'innerforce']):
            return 'Dřevo'

        # If no match found, this is an error - return empty to flag for manual review
        print(f"  WARNING: Could not determine type for: {product_name}")
        return "UNKNOWN_TYPE"

    def process_missing_file(self, missing_file: Path, memory_type: str) -> List[Tuple[str, str]]:
        """Process a MISSING file and return KEY-VALUE pairs."""
        print(f"\nProcessing {missing_file.name}...")

        keys = self.read_missing_file(missing_file)
        print(f"Found {len(keys)} missing entries")

        results = []
        unknown_count = 0

        for key in keys:
            if not key or key.startswith('\ufeff'):
                continue

            key = key.lstrip('\ufeff')

            if memory_type == 'ProductBrandMemory_CS.csv':
                value = self.extract_brand(key)
            elif memory_type == 'ProductModelMemory_CS.csv':
                brand = self.extract_brand(key)
                value = self.extract_model(key, brand)
            elif memory_type == 'ProductTypeMemory_CS.csv':
                value = self.extract_product_type(key)
                if value == "UNKNOWN_TYPE":
                    unknown_count += 1
                    continue  # Skip unknown types
            else:
                continue

            results.append((key, value))

        if unknown_count > 0:
            print(f"  Skipped {unknown_count} entries with unknown type (need manual review)")

        return results

    def write_memory_file(self, memory_file: Path, entries: List[Tuple[str, str]]):
        """Write entries to memory CSV file (overwrite mode)."""
        if not entries:
            return

        print(f"Writing {len(entries)} entries to {memory_file.name}...")

        with open(memory_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerow(['KEY', 'VALUE'])
            for key, value in entries:
                writer.writerow([key, value])

        print(f"Wrote {len(entries)} entries")

    def process_all(self):
        """Process all memory types."""
        memory_types = [
            'ProductBrandMemory_CS.csv',
            'ProductModelMemory_CS.csv',
            'ProductTypeMemory_CS.csv'
        ]

        for memory_type in memory_types:
            print(f"\n{'='*60}")
            print(f"Processing {memory_type}")
            print(f"{'='*60}")

            # Collect ALL entries (existing + new)
            all_entries = {}

            # Add existing entries first
            if memory_type == 'ProductBrandMemory_CS.csv':
                all_entries.update(self.existing_brands)
            elif memory_type == 'ProductModelMemory_CS.csv':
                all_entries.update(self.existing_models)
            elif memory_type == 'ProductTypeMemory_CS.csv':
                all_entries.update(self.existing_types)

            # Process MISSING files
            consolidated_dir = self.consolidated_dir / memory_type
            if consolidated_dir.exists():
                missing_files = list(consolidated_dir.glob("*_MISSING.txt"))
                print(f"Found {len(missing_files)} MISSING files")

                for missing_file in sorted(missing_files):
                    new_entries = self.process_missing_file(missing_file, memory_type)
                    for key, value in new_entries:
                        all_entries[key] = value  # Update or add

            # Write complete file
            memory_file = self.memory_dir / memory_type
            entries_list = [(k, v) for k, v in all_entries.items()]
            self.write_memory_file(memory_file, entries_list)

            print(f"\nTotal entries in {memory_type}: {len(entries_list)}")


def main():
    base_dir = Path("/home/user/PingPongEshopScraping/desaka_unifier")

    populator = MemoryPopulatorV2(base_dir)
    populator.process_all()

    print("\n" + "="*60)
    print("Memory population complete!")
    print("="*60)


if __name__ == "__main__":
    main()
