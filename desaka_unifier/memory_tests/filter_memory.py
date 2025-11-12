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
from pathlib import Path
from typing import Dict, List, Set
from tqdm import tqdm

# Import existing file operations
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.file_ops import load_csv_file, save_csv_file


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
    valid_categories: Set[str]
) -> Dict[str, str]:
    """
    Odstraní záznamy s neúplnými a neexistujícími kategoriemi.

    Args:
        category_memory: CategoryMemory slovník
        incomplete_categories: Set neúplných kategorií
        valid_categories: Set platných kategorií (z CategoryNameMemory)

    Returns:
        Vyfiltrovaný slovník
    """
    print("\n🧹 Čištění CategoryMemory od neúplných a neexistujících kategorií...")
    filtered = {}
    removed_incomplete = 0
    removed_nonexistent = 0

    with tqdm(total=len(category_memory), desc="Filtrování CategoryMemory", unit="záznam") as pbar:
        for key, value in category_memory.items():
            if value in incomplete_categories:
                removed_incomplete += 1
            elif value not in valid_categories:
                removed_nonexistent += 1
            else:
                filtered[key] = value
            pbar.update(1)

    print(f"   ❌ Odstraněno neúplných: {removed_incomplete} záznamů")
    print(f"   ❌ Odstraněno neexistujících: {removed_nonexistent} záznamů")
    print(f"   ✓ Zbývá: {len(filtered)} záznamů")

    return filtered


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
    valid_brands: Set[str]
) -> Dict[str, str]:
    """
    Odstraní záznamy s neznámými značkami.

    Args:
        brand_memory: ProductBrandMemory slovník
        valid_brands: Set platných značek

    Returns:
        Vyfiltrovaný slovník
    """
    print("\n🧹 Čištění ProductBrandMemory od neznámých značek...")
    filtered = {}
    removed_count = 0

    with tqdm(total=len(brand_memory), desc="Filtrování ProductBrandMemory", unit="záznam") as pbar:
        for key, value in brand_memory.items():
            if value in valid_brands:
                filtered[key] = value
            else:
                removed_count += 1
            pbar.update(1)

    print(f"   ❌ Odstraněno: {removed_count} záznamů")
    print(f"   ✓ Zbývá: {len(filtered)} záznamů")

    return filtered


def filter_contains_brand(
    memory: Dict[str, str],
    brands: Set[str],
    memory_name: str
) -> Dict[str, str]:
    """
    Odstraní záznamy, jejichž VALUE obsahuje název značky.

    Args:
        memory: Memory slovník
        brands: Set značek
        memory_name: Název memory (pro výpis)

    Returns:
        Vyfiltrovaný slovník
    """
    print(f"\n🧹 Čištění {memory_name} od záznamů obsahujících značky...")
    filtered = {}
    removed_count = 0

    with tqdm(total=len(memory), desc=f"Filtrování {memory_name}", unit="záznam") as pbar:
        for key, value in memory.items():
            contains_brand = False
            for brand in brands:
                if brand.lower() in value.lower():
                    contains_brand = True
                    break

            if not contains_brand:
                filtered[key] = value
            else:
                removed_count += 1

            pbar.update(1)

    print(f"   ❌ Odstraněno: {removed_count} záznamů")
    print(f"   ✓ Zbývá: {len(filtered)} záznamů")

    return filtered


def filter_types_containing_models(
    type_memory: Dict[str, str],
    model_values: Set[str]
) -> Dict[str, str]:
    """
    Odstraní typy obsahující celou hodnotu nějakého modelu.

    Např. typ "Koš na míčky" bude odstraněn, pokud existuje model "na míčky".

    Args:
        type_memory: ProductTypeMemory slovník
        model_values: Set hodnot z ProductModelMemory

    Returns:
        Vyfiltrovaný slovník
    """
    print("\n🧹 Čištění ProductTypeMemory od záznamů obsahujících modely...")
    filtered = {}
    removed_count = 0

    with tqdm(total=len(type_memory), desc="Filtrování ProductTypeMemory", unit="záznam") as pbar:
        for key, value in type_memory.items():
            contains_model = False
            for model in model_values:
                if model in value:  # Celá hodnota modelu
                    contains_model = True
                    break

            if not contains_model:
                filtered[key] = value
            else:
                removed_count += 1

            pbar.update(1)

    print(f"   ❌ Odstraněno: {removed_count} záznamů")
    print(f"   ✓ Zbývá: {len(filtered)} záznamů")

    return filtered


def filter_models_containing_type_words(
    model_memory: Dict[str, str],
    type_values: Set[str]
) -> Dict[str, str]:
    """
    Odstraní modely obsahující slova z typů.

    Oddělovač slov je mezera a pomlčka.

    Args:
        model_memory: ProductModelMemory slovník
        type_values: Set hodnot z ProductTypeMemory

    Returns:
        Vyfiltrovaný slovník
    """
    print("\n🧹 Čištění ProductModelMemory od záznamů obsahujících slova typů...")

    # Extrahuj všechna slova z typů
    type_words = set()
    for type_value in type_values:
        # Rozdělení podle mezery a pomlčky
        words = re.split(r'[\s\-]+', type_value)
        type_words.update(word.lower() for word in words if word)

    filtered = {}
    removed_count = 0

    with tqdm(total=len(model_memory), desc="Filtrování ProductModelMemory", unit="záznam") as pbar:
        for key, value in model_memory.items():
            # Rozdělení hodnoty na slova
            model_words = re.split(r'[\s\-]+', value.lower())

            contains_type_word = any(word in type_words for word in model_words)

            if not contains_type_word:
                filtered[key] = value
            else:
                removed_count += 1

            pbar.update(1)

    print(f"   ❌ Odstraněno: {removed_count} záznamů")
    print(f"   ✓ Zbývá: {len(filtered)} záznamů")

    return filtered


def filter_models_containing_variant_values(
    model_memory: Dict[str, str],
    variant_values: Set[str]
) -> Dict[str, str]:
    """
    Odstraní modely obsahující VariantValue delší než 2 znaky.

    Args:
        model_memory: ProductModelMemory slovník
        variant_values: Set hodnot z VariantValueMemory

    Returns:
        Vyfiltrovaný slovník
    """
    print("\n🧹 Čištění ProductModelMemory od záznamů obsahujících variantní hodnoty...")

    # Filtruj pouze hodnoty delší než 2 znaky
    long_variant_values = {v for v in variant_values if len(v) > 2}

    filtered = {}
    removed_count = 0

    with tqdm(total=len(model_memory), desc="Filtrování variant hodnot", unit="záznam") as pbar:
        for key, value in model_memory.items():
            contains_variant = False
            for variant in long_variant_values:
                if variant in value:
                    contains_variant = True
                    break

            if not contains_variant:
                filtered[key] = value
            else:
                removed_count += 1

            pbar.update(1)

    print(f"   ❌ Odstraněno: {removed_count} záznamů")
    print(f"   ✓ Zbývá: {len(filtered)} záznamů")

    return filtered


def filter_invalid_characters(
    memory: Dict[str, str],
    memory_name: str
) -> Dict[str, str]:
    """
    Odstraní záznamy s nepovolenými znaky (znaky nepoužívané v češtině).

    Povolené jsou české znaky: á,č,ď,é,ě,í,ň,ó,ř,š,ť,ú,ů,ý,ž
    Nepovolené jsou např.: ü,ß,ľ,ä,ö atd.

    Args:
        memory: Memory slovník
        memory_name: Název memory (pro výpis)

    Returns:
        Vyfiltrovaný slovník
    """
    print(f"\n🧹 Čištění {memory_name} od záznamů s nepovolenými znaky...")

    # Regex pro detekci nepovolených znaků
    # Povolené: a-z, A-Z, 0-9, české znaky, běžné znaky jako mezera, čárka, tečka atd.
    czech_pattern = re.compile(r'^[a-zA-Z0-9áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ\s\-.,;:!?()\/+%&@°#\[\]{}><„"\'\"]+$')

    filtered = {}
    removed_count = 0

    with tqdm(total=len(memory), desc=f"Filtrování {memory_name}", unit="záznam") as pbar:
        for key, value in memory.items():
            # Kontrola VALUE
            if czech_pattern.match(value):
                filtered[key] = value
            else:
                removed_count += 1

            pbar.update(1)

    print(f"   ❌ Odstraněno: {removed_count} záznamů")
    print(f"   ✓ Zbývá: {len(filtered)} záznamů")

    return filtered


def filter_name_memory(
    name_memory: Dict[str, str],
    type_memory: Dict[str, str],
    brand_memory: Dict[str, str],
    model_memory: Dict[str, str]
) -> Dict[str, str]:
    """
    Odstraní záznamy z NameMemory, které nemají klíč ve všech třech souborech.

    Args:
        name_memory: NameMemory slovník
        type_memory: ProductTypeMemory slovník
        brand_memory: ProductBrandMemory slovník
        model_memory: ProductModelMemory slovník

    Returns:
        Vyfiltrovaný slovník
    """
    print("\n🧹 Čištění NameMemory od záznamů bez klíčů v Type/Brand/Model...")

    filtered = {}
    removed_count = 0

    with tqdm(total=len(name_memory), desc="Filtrování NameMemory", unit="záznam") as pbar:
        for key, value in name_memory.items():
            # Klíč musí být ve všech třech souborech
            if key in type_memory and key in brand_memory and key in model_memory:
                filtered[key] = value
            else:
                removed_count += 1

            pbar.update(1)

    print(f"   ❌ Odstraněno: {removed_count} záznamů")
    print(f"   ✓ Zbývá: {len(filtered)} záznamů")

    return filtered


def main():
    """Hlavní funkce."""
    parser = argparse.ArgumentParser(
        description='Filtrování memory souborů - automatické čištění podle pravidel',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Příklady použití:
  python filter_memory.py --language CS
  python filter_memory.py --language SK --dry-run
  python filter_memory.py -l CS

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
        """
    )

    parser.add_argument('-l', '--language', default='CS',
                       help='Jazyk (CS nebo SK, default: CS)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Suchý běh - pouze spočítá změny, neuloží')

    args = parser.parse_args()

    try:
        language = args.language.upper()
        dry_run = args.dry_run

        if dry_run:
            print("\n⚠️  SUCHÝ BĚH - změny nebudou uloženy")

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

        category_memory = filter_category_memory(category_memory, incomplete_categories, valid_categories)
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

        brand_memory = filter_brand_memory(brand_memory, valid_brands)
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

        type_memory = filter_contains_brand(type_memory, valid_brands, "ProductTypeMemory")
        model_memory = filter_contains_brand(model_memory, valid_brands, "ProductModelMemory")

        save_memory_dict(type_memory, type_filepath, dry_run)
        save_memory_dict(model_memory, model_filepath, dry_run)

        # ===== 7. Odstranit modely z typů =====
        print("\n" + "="*80)
        print("KROK 7: Odstranění modelů z ProductType")
        print("="*80)

        model_values = set(model_memory.values())
        type_memory = filter_types_containing_models(type_memory, model_values)
        save_memory_dict(type_memory, type_filepath, dry_run)

        # ===== 8. Odstranit slova typů z modelů =====
        print("\n" + "="*80)
        print("KROK 8: Odstranění slov typů z ProductModel")
        print("="*80)

        type_values = set(type_memory.values())
        model_memory = filter_models_containing_type_words(model_memory, type_values)
        save_memory_dict(model_memory, model_filepath, dry_run)

        # ===== 9. Odstranit VariantValue z modelů =====
        print("\n" + "="*80)
        print("KROK 9: Odstranění VariantValue z ProductModel")
        print("="*80)

        variant_value_filepath = get_memory_filepath('VariantValueMemory', language)
        variant_value_memory = load_memory_as_dict(variant_value_filepath)
        print(f"✓ Načteno {len(variant_value_memory)} záznamů z VariantValueMemory")

        variant_values = set(variant_value_memory.values())
        model_memory = filter_models_containing_variant_values(model_memory, variant_values)
        save_memory_dict(model_memory, model_filepath, dry_run)

        # ===== 10. Odstranit nepovolené znaky =====
        print("\n" + "="*80)
        print("KROK 10: Odstranění nepovolených znaků")
        print("="*80)

        type_memory = filter_invalid_characters(type_memory, "ProductTypeMemory")
        model_memory = filter_invalid_characters(model_memory, "ProductModelMemory")

        variant_name_filepath = get_memory_filepath('VariantNameMemory', language)
        variant_name_memory = load_memory_as_dict(variant_name_filepath)
        print(f"✓ Načteno {len(variant_name_memory)} záznamů z VariantNameMemory")

        variant_name_memory = filter_invalid_characters(variant_name_memory, "VariantNameMemory")
        variant_value_memory = filter_invalid_characters(variant_value_memory, "VariantValueMemory")

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

        name_memory = filter_name_memory(name_memory, type_memory, brand_memory, model_memory)
        save_memory_dict(name_memory, name_filepath, dry_run)

        # ===== Závěrečný report =====
        print("\n" + "="*80)
        print("SHRNUTÍ FILTROVÁNÍ")
        print("="*80)
        print(f"\nJazyk: {language}")
        print(f"Režim: {'SUCHÝ BĚH (změny neuloženy)' if dry_run else 'ŽIVÝ BĚH (změny uloženy)'}")
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

        print("="*80)

        return 0

    except Exception as e:
        print(f"\n❌ Chyba: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
