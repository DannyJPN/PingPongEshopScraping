#!/usr/bin/env python3
"""
Memory Population Script v3 - Complete Reprocessing

This version reprocesses ALL existing entries through the new logic to fix:
1. Remove "Ostatní" from types
2. Strip variants from models
3. Clean up all entries
"""

import csv
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set

# [Previous constants remain the same]
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

COLOR_VARIANTS = [
    'schwarz', 'rot', 'blau', 'grün', 'gelb', 'weiß', 'weiss', 'orange',
    'grau', 'pink', 'lila', 'violett', 'silber', 'gold', 'braun', 'türkis',
    'hellblau', 'dunkelblau', 'hellgrau', 'dunkelgrau', 'hellgrün', 'multicolor',
    'black', 'red', 'blue', 'green', 'yellow', 'white', 'orange', 'grey', 'gray',
    'purple', 'violet', 'silver', 'gold', 'brown', 'turquoise', 'pink',
    'černý', 'červený', 'modrý', 'zelený', 'žlutý', 'bílý', 'oranžový',
    'šedý', 'růžový', 'fialový', 'stříbrný', 'zlatý', 'hnědý'
]

SIZE_VARIANTS = [
    'XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL', 'XXXXL', 'XXXXXL', 'XXXXXXL',
    '3XL', '4XL', '5XL', '6XL', '7XL', 'XXXS', 'XXXXS', 'XXXXXS'
]

THICKNESS_PATTERNS = [
    r'\b\d+[,\.]\d+\s*mm\b',
    r'\bOX\b',
    r'\b\d+°\b',
    r'\b\d+[,\.]\d+mm\b',
]

TYPE_KEYWORDS = [
    'belag', 'holz', 'schläger', 'ball', 'bälle', 'hülle', 'tasche',
    'reiniger', 'schwamm', 'kleber', 'kantenschutz', 'kantenband',
    'shirt', 'trikot', 'hose', 'short', 'shorts', 'schuhe', 'netz',
    'tisch', 'roboter', 'handtuch', 'messlehre', 'jacke', 'trainingsjacke',
    'windbreaker', 'schweißband', 'socken', 'kappe', 'mütze',
    'versiegelung', 'fólie', 'folie', 'anzughose', 'anzugjacke',
    'hemd', 'hoodie', 'longsleeve', 'poloshirt', 'tanktop', 'weste',
    'andruckrolle', 'hardcase', 'softcase', 'tischtennisschläger',
    'rubber', 'blade', 'racket', 'paddle', 'cleaner', 'sponge', 'glue',
    'edge tape', 'towel', 'net', 'table', 'gauge', 'jacket', 'cap',
    'socks', 'wristband', 'headband', 'case', 'bag', 'shirt',
    'potah', 'dřevo', 'pálka', 'míček', 'míčky', 'pouzdro', 'taška',
    'čistič', 'houba', 'lepidlo', 'ochranná páska', 'tričko', 'dres',
    'kraťasy', 'boty', 'síťka', 'stůl', 'robot', 'ručník', 'měrka',
    'bunda', 'potítko', 'ponožky', 'čepice', 'batoh', 'mikina',
    'obal na pálku', 'prkno', 'sukně', 'rock', 'skirt'
]

PRODUCT_TYPE_MAPPING = {
    'belag': 'Potah', 'rubber': 'Potah', 'potah': 'Potah',
    'noppen': 'Potah', 'anti': 'Potah', 'pips': 'Potah',
    'holz': 'Dřevo', 'blade': 'Dřevo', 'dřevo': 'Dřevo', 'prkno': 'Dřevo',
    'carbon': 'Dřevo', 'offensive': 'Dřevo', 'defensive': 'Dřevo',
    'schläger': 'Pálka', 'tischtennisschläger': 'Pálka',
    'racket': 'Pálka', 'paddle': 'Pálka', 'pálka': 'Pálka',
    'ball': 'Míček', 'bälle': 'Míčky', 'míček': 'Míček', 'míčky': 'Míčky',
    'hülle': 'Pouzdro', 'case': 'Pouzdro', 'pouzdro': 'Pouzdro',
    'hardcase': 'Pouzdro', 'softcase': 'Pouzdro', 'schlägerhülle': 'Pouzdro',
    'tasche': 'Taška', 'bag': 'Taška', 'taška': 'Taška',
    'rucksack': 'Batoh', 'backpack': 'Batoh', 'batoh': 'Batoh',
    'reiniger': 'Čistič', 'cleaner': 'Čistič', 'čistič': 'Čistič',
    'clean': 'Čistič', 'bioclean': 'Čistič', 'mist': 'Čistič',
    'schwamm': 'Houba', 'sponge': 'Houba', 'houba': 'Houba',
    'kleber': 'Lepidlo', 'glue': 'Lepidlo', 'lepidlo': 'Lepidlo', 'cement': 'Lepidlo',
    'kantenschutz': 'Ochranná páska', 'kantenband': 'Ochranná páska',
    'edge tape': 'Ochranná páska', 'ochranná páska': 'Ochranná páska', 'páska': 'Ochranná páska',
    'versiegelung': 'Ochranná fólie', 'fólie': 'Ochranná fólie',
    'folie': 'Ochranná fólie', 'seal': 'Ochranná fólie',
    'shirt': 'Tričko', 'trikot': 'Dres', 'tričko': 'Tričko', 'dres': 'Dres',
    'hemd': 'Tričko', 'poloshirt': 'Tričko', 'tanktop': 'Tričko',
    'short': 'Kraťasy', 'shorts': 'Kraťasy', 'hose': 'Kraťasy', 'kraťasy': 'Kraťasy',
    'schuhe': 'Boty', 'shoes': 'Boty', 'boty': 'Boty',
    'hoodie': 'Mikina', 'mikina': 'Mikina',
    'jacke': 'Bunda', 'jacket': 'Bunda', 'bunda': 'Bunda',
    'trainingsjacke': 'Bunda', 'windbreaker': 'Bunda',
    'anzugjacke': 'Bunda', 'weste': 'Bunda',
    'anzughose': 'Kalhoty', 'pants': 'Kalhoty', 'kalhoty': 'Kalhoty',
    'longsleeve': 'Tričko',
    'socken': 'Ponožky', 'socks': 'Ponožky', 'ponožky': 'Ponožky',
    'kappe': 'Čepice', 'mütze': 'Čepice', 'cap': 'Čepice', 'čepice': 'Čepice',
    'schweißband': 'Potítko', 'wristband': 'Potítko', 'potítko': 'Potítko',
    'headband': 'Čelenka', 'čelenka': 'Čelenka', 'stirnband': 'Čelenka',
    'netz': 'Síťka', 'net': 'Síťka', 'síťka': 'Síťka',
    'tisch': 'Stůl', 'table': 'Stůl', 'stůl': 'Stůl',
    'roboter': 'Robot', 'robot': 'Robot',
    'handtuch': 'Ručník', 'towel': 'Ručník', 'ručník': 'Ručník',
    'messlehre': 'Měrka', 'gauge': 'Měrka', 'měrka': 'Měrka',
    'andruckrolle': 'Váleček', 'roller': 'Váleček',
    'sada': 'Sada', 'set': 'Sada',
    'mince': 'Mince', 'coin': 'Mince', 'münze': 'Mince',
    'řetízek': 'Řetízek', 'kettchen': 'Řetízek', 'chain': 'Řetízek',
    'ersatzkettchen': 'Řetízek',
    'lak': 'Lak', 'lackierung': 'Lak', 'varnish': 'Lak', 'lakování': 'Lak',
    'medaile': 'Medaile', 'medaille': 'Medaile', 'medal': 'Medaile',
    'schnur': 'Šňůra', 'ersatzschnur': 'Šňůra', 'string': 'Šňůra',
    'rock': 'Sukně', 'skirt': 'Sukně', 'sukně': 'Sukně',
    'plachta': 'Plachta', 'abdeckung': 'Plachta', 'cover': 'Plachta',
    'sběrač': 'Sběrač', 'sammler': 'Sběrač', 'collector': 'Sběrač',
    'schiedsrichterstuhl': 'Stolek pro rozhodčí', 'stolek': 'Stolek pro rozhodčí',
    'počítadlo': 'Počítadlo', 'zählgerät': 'Počítadlo', 'scoreboard': 'Počítadlo',
    'koš': 'Koš', 'korb': 'Koš', 'basket': 'Koš',
    'deska': 'Deska', 'brett': 'Deska', 'board': 'Deska',
    'stroj': 'Stroj', 'maschine': 'Stroj', 'machine': 'Stroj',
    'držák': 'Držák', 'halter': 'Držák', 'holder': 'Držák',
    'lepení': 'Lepení', 'gluing': 'Lepení',
    'balancer': 'Vyvažovací závaží', 'ausgleichgewicht': 'Vyvažovací závaží',
    'weight': 'Vyvažovací závaží',
    'mini stůl': 'Mini stůl', 'mini table': 'Mini stůl',
    'voucher': 'Poukaz', 'poukaz': 'Poukaz', 'gutschein': 'Poukaz',
    'gift': 'Dárek', 'dárek': 'Dárek', 'geschenk': 'Dárek',
}


class MemoryReprocessor:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.memory_dir = base_dir / "Memory"
        self.consolidated_dir = self.memory_dir / "Consolidated"
        self.all_keys: Set[str] = set()

    def collect_all_keys(self):
        """Collect ALL keys from both existing memory and MISSING files."""
        print("Collecting all keys from existing memory and MISSING files...")

        # Load from backup files (these have ALL entries including old ones)
        for memory_type in ['ProductBrandMemory_CS.csv', 'ProductModelMemory_CS.csv', 'ProductTypeMemory_CS.csv']:
            backup_file = self.memory_dir / f"{memory_type}.backup"
            if backup_file.exists():
                with open(backup_file, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader)  # Skip header
                    for row in reader:
                        if len(row) >= 1:
                            self.all_keys.add(row[0])

            # Also add keys from MISSING files
            consolidated_dir = self.consolidated_dir / memory_type
            if consolidated_dir.exists():
                for missing_file in consolidated_dir.glob("*_MISSING.txt"):
                    try:
                        with open(missing_file, 'r', encoding='utf-16-le') as f:
                            for line in f:
                                key = line.strip().lstrip('\ufeff')
                                if key:
                                    self.all_keys.add(key)
                    except Exception as e:
                        print(f"Error reading {missing_file}: {e}")

        print(f"Collected {len(self.all_keys)} unique keys")

    def extract_brand(self, product_name: str) -> str:
        """Extract brand from product name."""
        if '-' in product_name:
            parts = product_name.split('-', 1)
            brand_candidate = parts[0].strip()
            for brand in KNOWN_BRANDS:
                if brand.lower() == brand_candidate.lower():
                    return brand

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

        # Remove thickness patterns
        for pattern in THICKNESS_PATTERNS:
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)

        # Remove colors
        for color in COLOR_VARIANTS:
            pattern = r'\b' + re.escape(color) + r'\b'
            result = re.sub(pattern, '', result, flags=re.IGNORECASE)

        # Remove sizes
        for size in SIZE_VARIANTS:
            pattern = r'\b' + re.escape(size) + r'\b'
            result = re.sub(pattern, '', result)

        result = re.sub(r'\s+', ' ', result).strip()
        result = result.strip('- ,/')

        return result

    def extract_model(self, product_name: str, brand: str) -> str:
        """Extract clean model name without brand, type, or variants."""
        model = product_name

        # Remove brand name
        if brand and brand != "Desaka":
            pattern = r'\b' + re.escape(brand) + r'\b'
            model = re.sub(pattern, '', model, flags=re.IGNORECASE)

        # Handle "Brand-Model" format
        if '-' in product_name:
            parts = product_name.split('-', 1)
            if len(parts) == 2:
                brand_candidate = parts[0].strip()
                for known_brand in KNOWN_BRANDS:
                    if known_brand.lower() == brand_candidate.lower():
                        model = parts[1].strip()
                        break

        # Remove type keywords
        for keyword in TYPE_KEYWORDS:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            model = re.sub(pattern, '', model, flags=re.IGNORECASE)

        # Strip variants
        model = self.strip_variants(model)

        # Clean up
        model = re.sub(r'\s+', ' ', model).strip()
        model = model.strip('- ,/')

        return model if model else product_name

    def extract_product_type(self, product_name: str) -> str:
        """Extract product type in Czech - NO FALLBACK."""
        product_lower = product_name.lower()

        # Direct keyword matching
        sorted_keywords = sorted(PRODUCT_TYPE_MAPPING.keys(), key=len, reverse=True)
        for keyword in sorted_keywords:
            if keyword in product_lower:
                return PRODUCT_TYPE_MAPPING[keyword]

        # Specific patterns
        if any(x in product_lower for x in ['narucross', 'fastarc', 'hurricane', 'tenergy', 'dignics', 'evolution']):
            return 'Potah'

        if any(x in product_lower for x in ['acoustic', 'viscaria', 'innerforce', 'ma lin', 'primorac']):
            return 'Dřevo'

        print(f"  WARNING: Unknown type for: {product_name}")
        return None  # Return None for unknown

    def reprocess_all(self):
        """Reprocess all entries."""
        print("\n" + "="*60)
        print("REPROCESSING ALL ENTRIES")
        print("="*60)

        self.collect_all_keys()

        # Process each memory type
        for memory_type in ['ProductBrandMemory_CS.csv', 'ProductModelMemory_CS.csv', 'ProductTypeMemory_CS.csv']:
            print(f"\n{'='*60}")
            print(f"Processing {memory_type}")
            print(f"{'='*60}")

            results = []
            skipped = 0

            for key in sorted(self.all_keys):
                if memory_type == 'ProductBrandMemory_CS.csv':
                    value = self.extract_brand(key)
                elif memory_type == 'ProductModelMemory_CS.csv':
                    brand = self.extract_brand(key)
                    value = self.extract_model(key, brand)
                elif memory_type == 'ProductTypeMemory_CS.csv':
                    value = self.extract_product_type(key)
                    if value is None:
                        skipped += 1
                        continue

                results.append((key, value))

            # Write to file
            memory_file = self.memory_dir / memory_type
            with open(memory_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f, quoting=csv.QUOTE_ALL)
                writer.writerow(['KEY', 'VALUE'])
                for key, value in results:
                    writer.writerow([key, value])

            print(f"Wrote {len(results)} entries")
            if skipped > 0:
                print(f"Skipped {skipped} entries with unknown type")


def main():
    base_dir = Path("/home/user/PingPongEshopScraping/desaka_unifier")

    reprocessor = MemoryReprocessor(base_dir)
    reprocessor.reprocess_all()

    print("\n" + "="*60)
    print("Reprocessing complete!")
    print("="*60)


if __name__ == "__main__":
    main()
