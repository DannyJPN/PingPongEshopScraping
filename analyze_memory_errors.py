#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Komplexní analýza Memory souborů pro nalezení sémantických chyb
"""

import csv
import re
from collections import defaultdict
from pathlib import Path

# Definice validních hodnot
VALID_PRODUCT_TYPES = {
    'Dřevo', 'Potah', 'Pálka', 'Míčky', 'Stůl', 'Síťka', 'Boty',
    'Obal', 'Robot', 'Taška', 'Batoh', 'Oblečení', 'Sada', 'Příslušenství',
    'Čistící prostředky', 'Lepidlo', 'Páska', 'Hranol', 'Ručník', 'Ponožky',
    'Čelenka', 'Podložka', 'Lajna', 'Stojánek', 'Pouzdro', 'DVD', 'Kniha',
    'Kraťasy', 'Mikina', 'Šortky', 'Tričko', 'Sukně', 'Tepláky', 'Rukavice'
}

# Německá slova, která by neměla být v hodnotách
GERMAN_WORDS = [
    'Schuh', 'Schuhe', 'Tisch', 'Netz', 'Netze', 'Set', 'Ball', 'Bälle',
    'Schläger', 'Hülle', 'Tasche', 'Stirnband', 'Handtuch', 'Shorts',
    'Hemd', 'Hose', 'Socken', 'Klebefolie', 'Kleber', 'Reiniger',
    'Belag', 'Holz', 'Roboter', 'Tischtennisplatte', 'Ersatz',
    'Trainingsball', 'Wettkampfball', 'blau', 'gelb', 'rot', 'grün',
    'schwarz', 'weiß', 'grau', 'orange', 'pink', 'lila', 'türkis',
    'mit', 'und', 'oder', 'für', 'von', 'zu', 'bei', 'nach',
    'Kugel', 'Schnur', 'Kette', 'alle', 'Universal'
]

# Slova označující sady (neměly by být v modelech ani typech samostatně)
SET_INDICATORS = ['Set', 'set', 'Sada', 'sada', 'Spar-set', 'Kit']

class MemoryAnalyzer:
    def __init__(self, memory_dir):
        self.memory_dir = Path(memory_dir)
        self.errors = defaultdict(list)

    def analyze_all(self):
        """Analyzuj všechny Memory soubory"""
        print("🔍 Spouštím komplexní analýzu Memory souborů...\n")

        # Analyzuj jednotlivé typy souborů
        self.analyze_product_models()
        self.analyze_product_types()
        self.analyze_categories()
        self.analyze_product_brands()

        # Vygeneruj report
        self.generate_report()

    def read_memory_csv(self, filename):
        """Načti CSV soubor s ošetřením chyb"""
        filepath = self.memory_dir / filename
        if not filepath.exists():
            return []

        data = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
        except Exception as e:
            print(f"⚠️  Chyba při čtení {filename}: {e}")

        return data

    def has_german_words(self, text):
        """Zkontroluj, zda text obsahuje německá slova"""
        if not text:
            return False, []
        found = []
        for word in GERMAN_WORDS:
            # Hledej samostatné slovo nebo jako součást složeného slova
            if re.search(r'\b' + re.escape(word) + r'\b', text, re.IGNORECASE):
                found.append(word)
        return len(found) > 0, found

    def has_product_type_in_value(self, text):
        """Zkontroluj, zda hodnota obsahuje typ produktu (neměl by být v modelu)"""
        if not text:
            return False, None
        for ptype in VALID_PRODUCT_TYPES:
            if ptype.lower() in text.lower():
                return True, ptype
        return False, None

    def has_set_indicator(self, text):
        """Zkontroluj, zda text obsahuje indikátor sady"""
        if not text:
            return False
        for indicator in SET_INDICATORS:
            if indicator in text:
                return True
        return False

    def analyze_product_models(self):
        """Analyzuj ProductModelMemory_CS.csv"""
        print("📋 Analyzuji ProductModelMemory_CS.csv...")
        data = self.read_memory_csv('ProductModelMemory_CS.csv')

        for idx, row in enumerate(data, start=2):
            key = row.get('KEY', '')
            value = row.get('VALUE', '')

            # Kontrola 1: Německá slova v hodnotě modelu
            has_german, german_words = self.has_german_words(value)
            if has_german:
                self.errors['ProductModelMemory'].append({
                    'line': idx,
                    'key': key,
                    'value': value,
                    'error': f'Němčina v modelu: {", ".join(german_words)}',
                    'severity': 'HIGH'
                })

            # Kontrola 2: Typ produktu v modelu
            has_type, ptype = self.has_product_type_in_value(value)
            if has_type:
                self.errors['ProductModelMemory'].append({
                    'line': idx,
                    'key': key,
                    'value': value,
                    'error': f'Typ produktu "{ptype}" v hodnotě modelu',
                    'severity': 'CRITICAL'
                })

            # Kontrola 3: Set v modelu
            if self.has_set_indicator(value):
                self.errors['ProductModelMemory'].append({
                    'line': idx,
                    'key': key,
                    'value': value,
                    'error': 'Set/Sada v modelu (měl by být samostatný produkt)',
                    'severity': 'MEDIUM'
                })

        print(f"   Nalezeno {len(self.errors['ProductModelMemory'])} chyb\n")

    def analyze_product_types(self):
        """Analyzuj ProductTypeMemory_CS.csv"""
        print("📋 Analyzuji ProductTypeMemory_CS.csv...")
        data = self.read_memory_csv('ProductTypeMemory_CS.csv')

        for idx, row in enumerate(data, start=2):
            key = row.get('KEY', '')
            value = row.get('VALUE', '')

            # Kontrola 1: Hodnota není validní typ
            if value and value not in VALID_PRODUCT_TYPES and not value.startswith('Potahy>') and not value.startswith('Dřeva>'):
                # Může to být platná hodnota se subkategorií, zkontroluj základní typ
                base_type = value.split('>')[0] if '>' in value else value
                if base_type not in VALID_PRODUCT_TYPES:
                    self.errors['ProductTypeMemory'].append({
                        'line': idx,
                        'key': key,
                        'value': value,
                        'error': f'Nevalidní typ produktu: "{value}"',
                        'severity': 'CRITICAL'
                    })

            # Kontrola 2: Německá slova v typu
            has_german, german_words = self.has_german_words(value)
            if has_german:
                self.errors['ProductTypeMemory'].append({
                    'line': idx,
                    'key': key,
                    'value': value,
                    'error': f'Němčina v typu: {", ".join(german_words)}',
                    'severity': 'HIGH'
                })

            # Kontrola 3: Čísla/kódy modelů v typu (např. "FF 2", "V15", atd.)
            if re.search(r'\b[A-Z]{1,3}\s*\d+\b', value):
                self.errors['ProductTypeMemory'].append({
                    'line': idx,
                    'key': key,
                    'value': value,
                    'error': 'Model/kód produktu v typu',
                    'severity': 'HIGH'
                })

        print(f"   Nalezeno {len(self.errors['ProductTypeMemory'])} chyb\n")

    def analyze_categories(self):
        """Analyzuj CategoryMemory_CS.csv"""
        print("📋 Analyzuji CategoryMemory_CS.csv...")
        data = self.read_memory_csv('CategoryMemory_CS.csv')

        # Definice logických kontrol kategorií
        category_rules = {
            'Síťky': ['síť', 'netz', 'net'],
            'Míčky': ['míč', 'ball', 'bälle'],
            'Boty': ['bot', 'schuh', 'shoe'],
            'Pálky': ['pálk', 'schläger', 'racket', 'bat'],
            'Dřeva': ['dřev', 'holz', 'blade', 'wood'],
            'Potahy': ['potah', 'belag', 'rubber', 'guma']
        }

        for idx, row in enumerate(data, start=2):
            key = row.get('KEY', '')
            value = row.get('VALUE', '')

            if not value or value == 'Vyřadit':
                continue

            # Kontrola 1: Německá slova v klíči (KEY obsahuje německý název produktu)
            has_german, german_words = self.has_german_words(key)
            if has_german and value != 'Vyřadit':
                # Zkontroluj, zda je kategorie správná podle klíče
                key_lower = key.lower()
                value_base = value.split('>')[0] if '>' in value else value

                # Heuristická kontrola - zda kategorie odpovídá klíči
                match_found = False
                for category, keywords in category_rules.items():
                    if value_base.startswith(category):
                        # Zkontroluj, zda klíč obsahuje příslušná klíčová slova
                        if any(kw in key_lower for kw in keywords):
                            match_found = True
                            break

                # Pokud klíč obsahuje německá slova specifická pro jinou kategorii
                mismatches = []
                for category, keywords in category_rules.items():
                    if not value_base.startswith(category):
                        if any(kw in key_lower for kw in keywords):
                            mismatches.append(category)

                if mismatches:
                    self.errors['CategoryMemory'].append({
                        'line': idx,
                        'key': key,
                        'value': value,
                        'error': f'Možná špatná kategorie - klíč indikuje: {", ".join(mismatches)}',
                        'severity': 'MEDIUM'
                    })

            # Kontrola 2: Německá slova v hodnotě kategorie
            has_german, german_words = self.has_german_words(value)
            if has_german:
                self.errors['CategoryMemory'].append({
                    'line': idx,
                    'key': key,
                    'value': value,
                    'error': f'Němčina v kategorii: {", ".join(german_words)}',
                    'severity': 'HIGH'
                })

        print(f"   Nalezeno {len(self.errors['CategoryMemory'])} chyb\n")

    def analyze_product_brands(self):
        """Analyzuj ProductBrandMemory_CS.csv"""
        print("📋 Analyzuji ProductBrandMemory_CS.csv...")
        data = self.read_memory_csv('ProductBrandMemory_CS.csv')

        for idx, row in enumerate(data, start=2):
            key = row.get('KEY', '')
            value = row.get('VALUE', '')

            # Kontrola 1: Typ produktu jako značka
            if value in VALID_PRODUCT_TYPES:
                self.errors['ProductBrandMemory'].append({
                    'line': idx,
                    'key': key,
                    'value': value,
                    'error': f'Typ produktu "{value}" použit jako značka',
                    'severity': 'CRITICAL'
                })

            # Kontrola 2: Německá běžná slova ve značce (ne názvy značek)
            common_german = ['Set', 'Tisch', 'Ball', 'Schuh', 'mit', 'und']
            if any(word in value for word in common_german):
                self.errors['ProductBrandMemory'].append({
                    'line': idx,
                    'key': key,
                    'value': value,
                    'error': f'Obecné německé slovo ve značce',
                    'severity': 'MEDIUM'
                })

        print(f"   Nalezeno {len(self.errors['ProductBrandMemory'])} chyb\n")

    def generate_report(self):
        """Vygeneruj detailní report"""
        print("\n" + "="*80)
        print("📊 KOMPLEXNÍ REPORT CHYB V MEMORY SOUBORECH")
        print("="*80 + "\n")

        total_errors = sum(len(errors) for errors in self.errors.values())

        if total_errors == 0:
            print("✅ Nebyly nalezeny žádné chyby!")
            return

        print(f"🔴 Celkem nalezeno: {total_errors} chyb\n")

        # Seskup chyby podle severity
        severity_counts = defaultdict(int)
        for file_errors in self.errors.values():
            for error in file_errors:
                severity_counts[error['severity']] += 1

        print("📈 Statistika podle závažnosti:")
        print(f"   🔴 CRITICAL: {severity_counts['CRITICAL']}")
        print(f"   🟠 HIGH:     {severity_counts['HIGH']}")
        print(f"   🟡 MEDIUM:   {severity_counts['MEDIUM']}")
        print()

        # Detailní výpis podle souborů
        for filename, file_errors in sorted(self.errors.items()):
            if not file_errors:
                continue

            print(f"\n{'='*80}")
            print(f"📁 {filename}.csv - {len(file_errors)} chyb")
            print(f"{'='*80}\n")

            # Seskup podle severity
            critical = [e for e in file_errors if e['severity'] == 'CRITICAL']
            high = [e for e in file_errors if e['severity'] == 'HIGH']
            medium = [e for e in file_errors if e['severity'] == 'MEDIUM']

            for severity, errors_list in [('CRITICAL', critical), ('HIGH', high), ('MEDIUM', medium)]:
                if not errors_list:
                    continue

                severity_icon = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡'}[severity]
                print(f"\n{severity_icon} {severity} ({len(errors_list)} chyb):")
                print("-" * 80)

                # Zobraz prvních 20 příkladů pro každou kategorii
                for error in errors_list[:20]:
                    print(f"\nŘádek {error['line']}:")
                    print(f"  KEY:   {error['key'][:70]}...")
                    print(f"  VALUE: {error['value']}")
                    print(f"  ERROR: {error['error']}")

                if len(errors_list) > 20:
                    print(f"\n... a dalších {len(errors_list) - 20} chyb stejného typu")

        # Závěrečné shrnutí
        print("\n" + "="*80)
        print("💡 DOPORUČENÍ")
        print("="*80)
        print("""
1. KRITICKÉ chyby (CRITICAL) - opravit prioritně:
   - Typy produktů v modelech
   - Modely v typech
   - Nevalidní typy produktů

2. VYSOKÁ priorita (HIGH):
   - Německá slova v hodnotách
   - Modely/kódy v typech

3. STŘEDNÍ priorita (MEDIUM):
   - Set indikátory v modelech
   - Možné špatné kategorizace

4. Implementovat validační pravidla do unifieru
5. Přidat post-processing kontroly před exportem
6. Rozšířit AI fine-tuning o tyto edge cases
        """)

        # Uložení do souboru
        report_file = self.memory_dir / 'memory_analysis_report.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"CELKEM CHYB: {total_errors}\n\n")
            for filename, file_errors in sorted(self.errors.items()):
                f.write(f"\n{'='*80}\n")
                f.write(f"{filename}.csv - {len(file_errors)} chyb\n")
                f.write(f"{'='*80}\n\n")
                for error in file_errors:
                    f.write(f"Line {error['line']} [{error['severity']}]\n")
                    f.write(f"KEY: {error['key']}\n")
                    f.write(f"VALUE: {error['value']}\n")
                    f.write(f"ERROR: {error['error']}\n\n")

        print(f"\n📄 Detailní report uložen do: {report_file}")

if __name__ == '__main__':
    analyzer = MemoryAnalyzer('/home/user/PingPongEshopScraping/desaka_unifier/Memory')
    analyzer.analyze_all()
