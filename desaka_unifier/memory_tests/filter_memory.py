#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Filtrování memory souborů - automatické čištění podle pravidel

Skript provádí kaskádové filtrování memory souborů:
1. Načte CategoryNameMemory a identifikuje hierarchicky neúplné kategorie (pouze detekce, soubor se nemodifikuje)
2. Čistí CategoryMemory od neúplných a neexistujících kategorií
3. Čistí ProductBrandMemory od neznámých značek (načte seznam z BrandCodeList)
4. Odstraní značky z ProductType a ProductModel Memory
5. Odstraní modely z typů a slova typů z modelů
6. Odstraní variantní hodnoty z modelů
7. Odstraní nepovolené znaky
8. Čistí NameMemory od záznamů bez klíčů
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple
from tqdm import tqdm

# Import existing file operations
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.file_ops import load_csv_file, save_csv_file

# Type alias for removed records: List of (KEY, VALUE)
TrashData = List[Dict[str, str]]


def get_memory_filepath(filename: str, language: str) -> Path:
    """
    Získá cestu k memory souboru.

    Args:
        filename: Název souboru (bez přípony a jazyka)
        language: Jazykový kód (CS, SK)

    Returns:
        Path k memory souboru
    """
    filepath = Path(__file__).parent.parent / 'Memory' / f"{filename}_{language.upper()}.csv"

    if not filepath.exists():
        raise FileNotFoundError(f"Soubor nenalezen: {filepath}")

    return filepath


def get_brandcodelist_filepath() -> Path:
    """Získá cestu k BrandCodeList.csv."""
    filepath = Path(__file__).parent.parent / 'Memory' / 'BrandCodeList.csv'

    if not filepath.exists():
        raise FileNotFoundError(f"Soubor nenalezen: {filepath}")

    return filepath


def load_memory_as_dict(filepath: Path) -> Dict[str, str]:
    """
    Načte memory soubor jako slovník KEY→VALUE.

    Args:
        filepath: Cesta k memory souboru

    Returns:
        Slovník {KEY: VALUE}
    """
    csv_data = load_csv_file(str(filepath))
    return {row['KEY']: row['VALUE'] for row in csv_data}


def save_memory_dict(data: Dict[str, str], filepath: Path, dry_run: bool = False):
    """
    Uloží slovník do memory souboru.

    Args:
        data: Slovník {KEY: VALUE}
        filepath: Cesta k souboru
        dry_run: Pokud True, neuloží (suchý běh)
    """
    if dry_run:
        return

    csv_data = [{'KEY': key, 'VALUE': value} for key, value in sorted(data.items())]
    save_csv_file(csv_data, str(filepath))


def save_trash_data(trash_data: Dict[str, TrashData], language: str, dry_run: bool = False):
    """
    Přidá smazaná data do trash souborů (append mode).
    Kontroluje unikátnost celých řádků (KEY+VALUE), ne jen klíčů.

    Args:
        trash_data: Slovník {memory_name: list of trash records}
        language: Jazykový kód
        dry_run: Pokud True, neuloží
    """
    if dry_run:
        return

    # Trash složka je vedle Memory složky
    trash_dir = Path(__file__).parent.parent / 'Trash'
    trash_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n📦 Přidávání smazaných záznamů do: {trash_dir}")

    # Přidej do každého trash souboru (append mode)
    for memory_name, records in trash_data.items():
        if not records:
            continue

        trash_filepath = trash_dir / f"{memory_name}_{language}_trash.csv"

        # Build set of existing unique rows (KEY+VALUE)
        existing_rows = set()
        if trash_filepath.exists():
            existing_records = load_csv_file(str(trash_filepath))
            for rec in existing_records:
                row_id = (rec.get('KEY', ''), rec.get('VALUE', ''))
                existing_rows.add(row_id)

        # Filter out duplicate rows
        unique_new_records = []
        for rec in records:
            row_id = (rec.get('KEY', ''), rec.get('VALUE', ''))
            if row_id not in existing_rows:
                unique_new_records.append(rec)
                existing_rows.add(row_id)

        # Append unique records
        if unique_new_records:
            from shared.file_ops import append_to_csv_file
            # Use append mode - no backups
            append_to_csv_file(str(trash_filepath), unique_new_records)

            # Count total for reporting
            total_count = len(load_csv_file(str(trash_filepath)))
            print(f"   ✓ {memory_name}: přidáno {len(unique_new_records)} unikátních záznamů (celkem: {total_count})")
        else:
            print(f"   ○ {memory_name}: žádné nové unikátní záznamy")

    print(f"✅ Trash soubory aktualizovány v: {trash_dir}")


def filter_incomplete_categories(category_name_memory: Dict[str, str]) -> Set[str]:
    """
    Najde hierarchicky neúplné kategorie.

    Kategorie je neúplná, pokud je podstringem jiné kategorie.
    Např. "Potahy" je neúplná, pokud existuje "Potahy>Softy".

    Args:
        category_name_memory: Slovník CategoryNameMemory

    Returns:
        Set neúplných kategorií (VALUE)
    """
    values = set(category_name_memory.values())
    incomplete = set()

    # Pro každou hodnotu zkontroluj, zda je podstringem jiné hodnoty
    print("\n🔍 Hledání hierarchicky neúplných kategorií...")
    with tqdm(total=len(values), desc="Kontrola kategorií", unit="cat") as pbar:
        for val1 in values:
            is_incomplete = False
            for val2 in values:
                if val1 != val2 and val2.startswith(val1 + ">"):
                    is_incomplete = True
                    break

            if is_incomplete:
                incomplete.add(val1)

            pbar.update(1)

    return incomplete


def filter_category_memory(
    category_memory: Dict[str, str],
    incomplete_categories: Set[str],
    valid_categories: Set[str],
    debug: bool = False
) -> Tuple[Dict[str, str], TrashData]:
    """
    Odstraní záznamy s neúplnými a neexistujícími kategoriemi.

    Args:
        category_memory: CategoryMemory slovník
        incomplete_categories: Set neúplných kategorií
        valid_categories: Set platných kategorií (z CategoryNameMemory)
        debug: Zobrazit detailní důvody odstranění

    Returns:
        Tuple (vyfiltrovaný slovník, smazaná data)
    """
    print("\n🧹 Čištění CategoryMemory od neúplných a neexistujících kategorií...")
    filtered = {}
    trash = []
    removed_incomplete = 0
    removed_nonexistent = 0

    with tqdm(total=len(category_memory), desc="Filtrování CategoryMemory", unit="záznam") as pbar:
        for key, value in category_memory.items():
            if value in incomplete_categories:
                trash.append({'KEY': key, 'VALUE': value})
                removed_incomplete += 1
                if debug:
                    print(f"  ❌ Odstraněn: KEY='{key}', VALUE='{value}'")
                    print(f"     Důvod: Hierarchicky neúplná kategorie (existuje podkategorie)")
            elif value not in valid_categories:
                trash.append({'KEY': key, 'VALUE': value})
                removed_nonexistent += 1
                if debug:
                    print(f"  ❌ Odstraněn: KEY='{key}', VALUE='{value}'")
                    print(f"     Důvod: Kategorie neexistuje v CategoryNameMemory")
            else:
                filtered[key] = value
            pbar.update(1)

    print(f"   ❌ Odstraněno neúplných: {removed_incomplete} záznamů")
    print(f"   ❌ Odstraněno neexistujících: {removed_nonexistent} záznamů")
    print(f"   ✓ Zbývá: {len(filtered)} záznamů")

    return filtered, trash


def get_brand_list(brandcodelist_filepath: Path) -> Set[str]:
    """
    Načte seznam značek z BrandCodeList.csv.

    Args:
        brandcodelist_filepath: Cesta k BrandCodeList.csv

    Returns:
        Set názvů značek (KEY sloupec)
    """
    csv_data = load_csv_file(str(brandcodelist_filepath))
    return {row['KEY'] for row in csv_data}


def filter_brand_memory(
    brand_memory: Dict[str, str],
    valid_brands: Set[str],
    debug: bool = False
) -> Tuple[Dict[str, str], TrashData]:
    """
    Odstraní záznamy s neznámými značkami.

    Args:
        brand_memory: ProductBrandMemory slovník
        valid_brands: Set platných značek
        debug: Zobrazit detailní důvody odstranění

    Returns:
        Tuple (vyfiltrovaný slovník, smazaná data)
    """
    print("\n🧹 Čištění ProductBrandMemory od neznámých značek...")
    filtered = {}
    trash = []
    removed_count = 0

    with tqdm(total=len(brand_memory), desc="Filtrování ProductBrandMemory", unit="záznam") as pbar:
        for key, value in brand_memory.items():
            if value in valid_brands:
                filtered[key] = value
            else:
                trash.append({'KEY': key, 'VALUE': value})
                removed_count += 1
                if debug:
                    print(f"  ❌ Odstraněn: KEY='{key}', VALUE='{value}'")
                    print(f"     Důvod: Značka neexistuje v BrandCodeList")
            pbar.update(1)

    print(f"   ❌ Odstraněno: {removed_count} záznamů")
    print(f"   ✓ Zbývá: {len(filtered)} záznamů")

    return filtered, trash


def filter_contains_brand(
    memory: Dict[str, str],
    brands: Set[str],
    memory_name: str,
    debug: bool = False
) -> Tuple[Dict[str, str], TrashData]:
    """
    Odstraní záznamy, jejichž VALUE obsahuje název značky jako celé slovo.

    Slova jsou oddělena mezerou nebo pomlčkou.

    Args:
        memory: Memory slovník
        brands: Set značek
        memory_name: Název memory (pro výpis)
        debug: Zobrazit detailní důvody odstranění

    Returns:
        Tuple (vyfiltrovaný slovník, smazaná data)
    """
    print(f"\n🧹 Čištění {memory_name} od záznamů obsahujících značky...")
    filtered = {}
    trash = []
    removed_count = 0

    with tqdm(total=len(memory), desc=f"Filtrování {memory_name}", unit="záznam") as pbar:
        for key, value in memory.items():
            # Rozdělení hodnoty na slova (podle mezery a pomlčky)
            value_words = set(word.lower() for word in re.split(r'[\s\-]+', value) if word)

            contains_brand = False
            found_brand = None
            for brand in brands:
                # Hledáme pouze značky delší než 3 znaky jako celá slova
                if len(brand) >= 3 and brand.lower() in value_words:
                    contains_brand = True
                    found_brand = brand
                    break

            if not contains_brand:
                filtered[key] = value
            else:
                trash.append({'KEY': key, 'VALUE': value})
                removed_count += 1
                if debug:
                    print(f"  ❌ Odstraněn: KEY='{key}', VALUE='{value}'")
                    print(f"     Důvod: Obsahuje značku '{found_brand}' jako celé slovo")

            pbar.update(1)

    print(f"   ❌ Odstraněno: {removed_count} záznamů")
    print(f"   ✓ Zbývá: {len(filtered)} záznamů")

    return filtered, trash


def filter_types_containing_models(
    type_memory: Dict[str, str],
    model_values: Set[str],
    debug: bool = False
) -> Tuple[Dict[str, str], TrashData]:
    """
    Odstraní typy obsahující model jako celé slovo nebo sekvenci slov.

    Např. typ "Koš na míčky" bude odstraněn, pokud existuje model "na míčky".
    Slova jsou oddělena mezerou nebo pomlčkou.

    Args:
        type_memory: ProductTypeMemory slovník
        model_values: Set hodnot z ProductModelMemory
        debug: Zobrazit detailní důvody odstranění

    Returns:
        Tuple (vyfiltrovaný slovník, smazaná data)
    """
    print("\n🧹 Čištění ProductTypeMemory od záznamů obsahujících modely...")
    filtered = {}
    trash = []
    removed_count = 0

    with tqdm(total=len(type_memory), desc="Filtrování ProductTypeMemory", unit="záznam") as pbar:
        for key, value in type_memory.items():
            contains_model = False
            found_model = None

            # Rozdělení hodnoty typu na slova
            value_words = set(word.lower() for word in re.split(r'[\s\-]+', value) if word)

            for model in model_values:
                # Hledáme pouze modely delší než 3 znaky
                if len(model) >= 3:
                    # Rozdělení modelu na slova
                    model_words = set(word.lower() for word in re.split(r'[\s\-]+', model) if word)

                    # Kontrola, zda všechna slova z modelu jsou v typu jako celá slova
                    if model_words and model_words.issubset(value_words):
                        contains_model = True
                        found_model = model
                        break

            if not contains_model:
                filtered[key] = value
            else:
                trash.append({'KEY': key, 'VALUE': value})
                removed_count += 1
                if debug:
                    print(f"  ❌ Odstraněn: KEY='{key}', VALUE='{value}'")
                    print(f"     Důvod: Obsahuje slova z modelu '{found_model}'")

            pbar.update(1)

    print(f"   ❌ Odstraněno: {removed_count} záznamů")
    print(f"   ✓ Zbývá: {len(filtered)} záznamů")

    return filtered, trash


def filter_models_containing_type_words(
    model_memory: Dict[str, str],
    type_values: Set[str],
    debug: bool = False
) -> Tuple[Dict[str, str], TrashData]:
    """
    Odstraní modely obsahující slova z typů.

    Oddělovač slov je mezera a pomlčka.

    Args:
        model_memory: ProductModelMemory slovník
        type_values: Set hodnot z ProductTypeMemory
        debug: Zobrazit detailní důvody odstranění

    Returns:
        Tuple (vyfiltrovaný slovník, smazaná data)
    """
    print("\n🧹 Čištění ProductModelMemory od záznamů obsahujících slova typů...")

    # Extrahuj všechna slova z typů (pouze slova delší než 3 znaky)
    type_words = set()
    for type_value in type_values:
        # Rozdělení podle mezery a pomlčky
        words = re.split(r'[\s\-]+', type_value)
        type_words.update(word.lower() for word in words if word and len(word) >= 3)

    filtered = {}
    trash = []
    removed_count = 0

    with tqdm(total=len(model_memory), desc="Filtrování ProductModelMemory", unit="záznam") as pbar:
        for key, value in model_memory.items():
            # Rozdělení hodnoty na slova
            model_words = re.split(r'[\s\-]+', value.lower())

            found_words = [word for word in model_words if word in type_words]
            contains_type_word = bool(found_words)

            if not contains_type_word:
                filtered[key] = value
            else:
                trash.append({'KEY': key, 'VALUE': value})
                removed_count += 1
                if debug:
                    print(f"  ❌ Odstraněn: KEY='{key}', VALUE='{value}'")
                    print(f"     Důvod: Obsahuje slova z typu: {', '.join(found_words)}")

            pbar.update(1)

    print(f"   ❌ Odstraněno: {removed_count} záznamů")
    print(f"   ✓ Zbývá: {len(filtered)} záznamů")

    return filtered, trash


def filter_models_containing_variant_values(
    model_memory: Dict[str, str],
    variant_values: Set[str],
    debug: bool = False
) -> Tuple[Dict[str, str], TrashData]:
    """
    Odstraní modely obsahující VariantValue delší než 2 znaky jako celé slovo.

    Slova jsou oddělena mezerou nebo pomlčkou.

    Args:
        model_memory: ProductModelMemory slovník
        variant_values: Set hodnot z VariantValueMemory
        debug: Zobrazit detailní důvody odstranění

    Returns:
        Tuple (vyfiltrovaný slovník, smazaná data)
    """
    print("\n🧹 Čištění ProductModelMemory od záznamů obsahujících variantní hodnoty...")

    # Filtruj pouze hodnoty delší než 2 znaky
    long_variant_values = {v for v in variant_values if len(v) > 2}

    filtered = {}
    trash = []
    removed_count = 0

    with tqdm(total=len(model_memory), desc="Filtrování variant hodnot", unit="záznam") as pbar:
        for key, value in model_memory.items():
            # Rozdělení hodnoty na slova
            value_words = set(word.lower() for word in re.split(r'[\s\-]+', value) if word)

            contains_variant = False
            found_variant = None
            for variant in long_variant_values:
                # Kontrola, zda variantní hodnota je v modelu jako celé slovo
                if len(variant) >= 3 and variant.lower() in value_words:
                    contains_variant = True
                    found_variant = variant
                    break

            if not contains_variant:
                filtered[key] = value
            else:
                trash.append({'KEY': key, 'VALUE': value})
                removed_count += 1
                if debug:
                    print(f"  ❌ Odstraněn: KEY='{key}', VALUE='{value}'")
                    print(f"     Důvod: Obsahuje variantní hodnotu '{found_variant}' jako celé slovo")

            pbar.update(1)

    print(f"   ❌ Odstraněno: {removed_count} záznamů")
    print(f"   ✓ Zbývá: {len(filtered)} záznamů")

    return filtered, trash


def filter_invalid_characters(
    memory: Dict[str, str],
    memory_name: str,
    debug: bool = False
) -> Tuple[Dict[str, str], TrashData]:
    """
    Odstraní záznamy s nepovolenými znaky (znaky nepoužívané v češtině).

    Povolené jsou české znaky: á,č,ď,é,ě,í,ň,ó,ř,š,ť,ú,ů,ý,ž
    Nepovolené jsou např.: ü,ß,ľ,ä,ö atd.

    Args:
        memory: Memory slovník
        memory_name: Název memory (pro výpis)
        debug: Zobrazit detailní důvody odstranění

    Returns:
        Tuple (vyfiltrovaný slovník, smazaná data)
    """
    print(f"\n🧹 Čištění {memory_name} od záznamů s nepovolenými znaky...")

    # Regex pro detekci nepovolených znaků v celém řetězci
    # Povolené: a-z, A-Z, 0-9, české znaky, běžné znaky jako mezera, čárka, tečka atd.
    czech_pattern = re.compile(r'^[a-zA-Z0-9áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ\s\-.,;:!?()\/+%&@°#\[\]{}><„"\'\"]+$')

    # Regex pro kontrolu jednotlivých znaků (bez ^ a $)
    char_pattern = re.compile(r'[a-zA-Z0-9áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ\s\-.,;:!?()\/+%&@°#\[\]{}><„"\'\"]')

    filtered = {}
    trash = []
    removed_count = 0

    with tqdm(total=len(memory), desc=f"Filtrování {memory_name}", unit="záznam") as pbar:
        for key, value in memory.items():
            # Kontrola VALUE
            if czech_pattern.match(value):
                filtered[key] = value
            else:
                trash.append({'KEY': key, 'VALUE': value})
                removed_count += 1
                if debug:
                    # Find invalid characters - znaky, které neodpovídají povoleným
                    invalid_chars = set(c for c in value if not char_pattern.match(c))
                    print(f"  ❌ Odstraněn: KEY='{key}', VALUE='{value}'")
                    print(f"     Důvod: Obsahuje nepovolené znaky: {invalid_chars}")

            pbar.update(1)

    print(f"   ❌ Odstraněno: {removed_count} záznamů")
    print(f"   ✓ Zbývá: {len(filtered)} záznamů")

    return filtered, trash


def filter_name_memory(
    name_memory: Dict[str, str],
    type_memory: Dict[str, str],
    brand_memory: Dict[str, str],
    model_memory: Dict[str, str],
    debug: bool = False
) -> Tuple[Dict[str, str], TrashData]:
    """
    Odstraní záznamy z NameMemory, které nemají klíč ve všech třech souborech.

    Args:
        name_memory: NameMemory slovník
        type_memory: ProductTypeMemory slovník
        brand_memory: ProductBrandMemory slovník
        model_memory: ProductModelMemory slovník
        debug: Zobrazit detailní důvody odstranění

    Returns:
        Tuple (vyfiltrovaný slovník, smazaná data)
    """
    print("\n🧹 Čištění NameMemory od záznamů bez klíčů v Type/Brand/Model...")

    filtered = {}
    trash = []
    removed_count = 0

    with tqdm(total=len(name_memory), desc="Filtrování NameMemory", unit="záznam") as pbar:
        for key, value in name_memory.items():
            # Klíč musí být ve všech třech souborech
            missing = []
            if key not in type_memory:
                missing.append('Type')
            if key not in brand_memory:
                missing.append('Brand')
            if key not in model_memory:
                missing.append('Model')

            if not missing:
                filtered[key] = value
            else:
                trash.append({'KEY': key, 'VALUE': value})
                removed_count += 1
                if debug:
                    print(f"  ❌ Odstraněn: KEY='{key}', VALUE='{value}'")
                    print(f"     Důvod: Chybí klíč v: {', '.join(missing)}")

            pbar.update(1)

    print(f"   ❌ Odstraněno: {removed_count} záznamů")
    print(f"   ✓ Zbývá: {len(filtered)} záznamů")

    return filtered, trash


def main():
    """Hlavní funkce."""
    parser = argparse.ArgumentParser(
        description='Filtrování memory souborů - automatické čištění podle pravidel',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Příklady použití:
  python filter_memory.py --language CS
  python filter_memory.py --language SK --dry-run
  python filter_memory.py --language CS --debug

Debug mód:
  --debug zapne detailní výpisy pro každý odstraněný záznam včetně:
  - KEY a VALUE odstraněného záznamu
  - Konkrétní důvod odstranění (jaká hodnota způsobila vyřazení)
  - Užitečné pro pochopení, proč byla konkrétní data odfiltrována

Skript provádí kaskádové filtrování:
1. Načte CategoryNameMemory a najde neúplné kategorie (pouze zdrojový soubor, nemodifikuje se)
2. Čistí CategoryMemory od neúplných a neexistujících kategorií
3. Načte BrandCodeList a čistí ProductBrandMemory od neznámých značek
4. Odstraní značky z ProductType a ProductModel Memory
5. Odstraní modely z typů a slova typů z modelů
6. Odstraní variantní hodnoty z modelů
7. Odstraní nepovolené znaky
8. Čistí NameMemory od záznamů bez klíčů

Poznámka: CategoryNameMemory a BrandCodeList jsou pouze zdrojové soubory
          pro detekci pravidel - nejsou modifikovány ani ukládány.

Trash soubory:
  Všechny smazané záznamy jsou automaticky přidány do desaka_unifier/Trash/
  do persistentních souborů (např. CategoryMemory_CS_trash.csv).
  Každý záznam obsahuje KEY a VALUE (bez REASON).
  Záznamy se PŘIDÁVAJÍ (append), kontroluje se unikátnost celého řádku.
  Tyto soubory slouží pro fine-tuning AI modelů.
        """
    )

    parser.add_argument('-l', '--language', default='CS',
                       help='Jazyk (CS nebo SK, default: CS)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Suchý běh - pouze spočítá změny, neuloží')
    parser.add_argument('--debug', action='store_true',
                       help='Debug mód - zobrazí detailní důvody odstranění každého záznamu')

    args = parser.parse_args()

    try:
        language = args.language.upper()
        dry_run = args.dry_run

        # Slovník pro ukládání smazaných záznamů (automaticky se ukládají pro fine-tuning)
        all_trash_data: Dict[str, TrashData] = {}

        if dry_run:
            print("\n⚠️  SUCHÝ BĚH - změny nebudou uloženy")

        if args.debug:
            print("\n🐛 DEBUG MÓD - budou zobrazeny detailní důvody odstranění každého záznamu")

        print(f"\n{'='*80}")
        print(f"FILTROVÁNÍ MEMORY SOUBORŮ - {language}")
        print(f"{'='*80}")

        # ===== 1. CategoryNameMemory - najít neúplné kategorie (pouze zdrojový soubor) =====
        print("\n" + "="*80)
        print("KROK 1: Načítání CategoryNameMemory (zdrojový soubor - nebude modifikován)")
        print("="*80)

        category_name_filepath = get_memory_filepath('CategoryNameMemory', language)
        category_name_memory = load_memory_as_dict(category_name_filepath)
        print(f"✓ Načteno {len(category_name_memory)} záznamů z CategoryNameMemory")

        incomplete_categories = filter_incomplete_categories(category_name_memory)
        valid_categories = set(category_name_memory.values())
        print(f"\n📊 Nalezeno {len(incomplete_categories)} hierarchicky neúplných kategorií")
        print(f"📊 Celkem {len(valid_categories)} platných kategorií v CategoryNameMemory")
        print(f"ℹ️  CategoryNameMemory zůstává beze změny - použije se jen pro filtrování CategoryMemory")

        # ===== 2. CategoryMemory - vyčistit neúplné a neexistující kategorie =====
        print("\n" + "="*80)
        print("KROK 2: Čištění CategoryMemory")
        print("="*80)

        category_filepath = get_memory_filepath('CategoryMemory', language)
        category_memory = load_memory_as_dict(category_filepath)
        print(f"✓ Načteno {len(category_memory)} záznamů z CategoryMemory")

        category_memory, trash = filter_category_memory(category_memory, incomplete_categories, valid_categories, debug=args.debug)
        all_trash_data['CategoryMemory'] = trash
        save_memory_dict(category_memory, category_filepath, dry_run)

        # ===== 3. BrandCodeList - načíst seznam značek =====
        print("\n" + "="*80)
        print("KROK 3: Načítání BrandCodeList")
        print("="*80)

        brandcodelist_filepath = get_brandcodelist_filepath()
        valid_brands = get_brand_list(brandcodelist_filepath)
        print(f"✓ Načteno {len(valid_brands)} značek z BrandCodeList")

        # ===== 4. ProductBrandMemory - vyčistit neznámé značky =====
        print("\n" + "="*80)
        print("KROK 4: Čištění ProductBrandMemory")
        print("="*80)

        brand_filepath = get_memory_filepath('ProductBrandMemory', language)
        brand_memory = load_memory_as_dict(brand_filepath)
        print(f"✓ Načteno {len(brand_memory)} záznamů z ProductBrandMemory")

        brand_memory, trash = filter_brand_memory(brand_memory, valid_brands, debug=args.debug)
        all_trash_data['ProductBrandMemory'] = trash
        save_memory_dict(brand_memory, brand_filepath, dry_run)

        # ===== 5. ProductType a ProductModel - načíst =====
        print("\n" + "="*80)
        print("KROK 5: Načítání ProductType a ProductModel Memory")
        print("="*80)

        type_filepath = get_memory_filepath('ProductTypeMemory', language)
        model_filepath = get_memory_filepath('ProductModelMemory', language)

        type_memory = load_memory_as_dict(type_filepath)
        model_memory = load_memory_as_dict(model_filepath)

        print(f"✓ Načteno {len(type_memory)} záznamů z ProductTypeMemory")
        print(f"✓ Načteno {len(model_memory)} záznamů z ProductModelMemory")

        # ===== 6. Odstranit značky z Type a Model =====
        print("\n" + "="*80)
        print("KROK 6: Odstranění značek z ProductType a ProductModel")
        print("="*80)

        type_memory, trash = filter_contains_brand(type_memory, valid_brands, "ProductTypeMemory", debug=args.debug)
        all_trash_data.setdefault('ProductTypeMemory', []).extend(trash)

        model_memory, trash = filter_contains_brand(model_memory, valid_brands, "ProductModelMemory", debug=args.debug)
        all_trash_data.setdefault('ProductModelMemory', []).extend(trash)

        save_memory_dict(type_memory, type_filepath, dry_run)
        save_memory_dict(model_memory, model_filepath, dry_run)

        # ===== 7. Odstranit modely z typů =====
        print("\n" + "="*80)
        print("KROK 7: Odstranění modelů z ProductType")
        print("="*80)

        model_values = set(model_memory.values())
        type_memory, trash = filter_types_containing_models(type_memory, model_values, debug=args.debug)
        all_trash_data['ProductTypeMemory'].extend(trash)
        save_memory_dict(type_memory, type_filepath, dry_run)

        # ===== 8. Odstranit slova typů z modelů =====
        print("\n" + "="*80)
        print("KROK 8: Odstranění slov typů z ProductModel")
        print("="*80)

        type_values = set(type_memory.values())
        model_memory, trash = filter_models_containing_type_words(model_memory, type_values, debug=args.debug)
        all_trash_data['ProductModelMemory'].extend(trash)
        save_memory_dict(model_memory, model_filepath, dry_run)

        # ===== 9. Odstranit VariantValue z modelů =====
        print("\n" + "="*80)
        print("KROK 9: Odstranění VariantValue z ProductModel")
        print("="*80)

        variant_value_filepath = get_memory_filepath('VariantValueMemory', language)
        variant_value_memory = load_memory_as_dict(variant_value_filepath)
        print(f"✓ Načteno {len(variant_value_memory)} záznamů z VariantValueMemory")

        variant_values = set(variant_value_memory.values())
        model_memory, trash = filter_models_containing_variant_values(model_memory, variant_values, debug=args.debug)
        all_trash_data['ProductModelMemory'].extend(trash)
        save_memory_dict(model_memory, model_filepath, dry_run)

        # ===== 10. Odstranit nepovolené znaky =====
        print("\n" + "="*80)
        print("KROK 10: Odstranění nepovolených znaků")
        print("="*80)

        type_memory, trash = filter_invalid_characters(type_memory, "ProductTypeMemory", debug=args.debug)
        all_trash_data['ProductTypeMemory'].extend(trash)

        model_memory, trash = filter_invalid_characters(model_memory, "ProductModelMemory", debug=args.debug)
        all_trash_data['ProductModelMemory'].extend(trash)

        variant_name_filepath = get_memory_filepath('VariantNameMemory', language)
        variant_name_memory = load_memory_as_dict(variant_name_filepath)
        print(f"✓ Načteno {len(variant_name_memory)} záznamů z VariantNameMemory")

        variant_name_memory, trash = filter_invalid_characters(variant_name_memory, "VariantNameMemory", debug=args.debug)
        all_trash_data['VariantNameMemory'] = trash

        variant_value_memory, trash = filter_invalid_characters(variant_value_memory, "VariantValueMemory", debug=args.debug)
        all_trash_data['VariantValueMemory'] = trash

        save_memory_dict(type_memory, type_filepath, dry_run)
        save_memory_dict(model_memory, model_filepath, dry_run)
        save_memory_dict(variant_name_memory, variant_name_filepath, dry_run)
        save_memory_dict(variant_value_memory, variant_value_filepath, dry_run)

        # ===== 11. Čištění NameMemory =====
        print("\n" + "="*80)
        print("KROK 11: Čištění NameMemory")
        print("="*80)

        name_filepath = get_memory_filepath('NameMemory', language)
        name_memory = load_memory_as_dict(name_filepath)
        print(f"✓ Načteno {len(name_memory)} záznamů z NameMemory")

        name_memory, trash = filter_name_memory(name_memory, type_memory, brand_memory, model_memory, debug=args.debug)
        all_trash_data['NameMemory'] = trash
        save_memory_dict(name_memory, name_filepath, dry_run)

        # ===== Závěrečný report =====
        print("\n" + "="*80)
        print("SHRNUTÍ FILTROVÁNÍ")
        print("="*80)
        print(f"\nJazyk: {language}")
        print(f"Režim: {'SUCHÝ BĚH (změny neuloženy)' if dry_run else 'ŽIVÝ BĚH (změny uloženy)'}")
        print(f"Debug: {'ZAPNUT (detailní výpisy důvodů)' if args.debug else 'VYPNUT'}")
        print(f"\nVýsledný počet záznamů:")
        print(f"  • CategoryMemory:       {len(category_memory):>8,} záznamů")
        print(f"  • ProductBrandMemory:   {len(brand_memory):>8,} záznamů")
        print(f"  • ProductTypeMemory:    {len(type_memory):>8,} záznamů")
        print(f"  • ProductModelMemory:   {len(model_memory):>8,} záznamů")
        print(f"  • VariantNameMemory:    {len(variant_name_memory):>8,} záznamů")
        print(f"  • VariantValueMemory:   {len(variant_value_memory):>8,} záznamů")
        print(f"  • NameMemory:           {len(name_memory):>8,} záznamů")

        if not dry_run:
            print(f"\n✅ Všechny soubory byly úspěšně vyčištěny a uloženy!")
            print(f"✅ Zálohy byly vytvořeny automaticky (.csv_old)")
        else:
            print(f"\n⚠️  Suchý běh dokončen - žádné změny nebyly provedeny")
            print(f"💡 Spusťte bez --dry-run pro aplikování změn")

        # ===== Uložení trash souborů =====
        # Trash soubory se ukládají VŽDY (pokud není dry_run) - jsou součást fine-tuning systému
        if not dry_run and all_trash_data:
            print("\n" + "="*80)
            print("UKLÁDÁNÍ TRASH SOUBORŮ")
            print("="*80)
            save_trash_data(all_trash_data, language, dry_run=False)

        print("="*80)

        return 0

    except Exception as e:
        print(f"\n❌ Chyba: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
