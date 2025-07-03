#!/usr/bin/env python3
"""
Memory Checker pro projekt desaka_unifier.

Tento skript kontroluje a opravuje paměťové soubory:
1. Kontroluje správnost hodnot v ProductBrandMemory oproti BrandCodeList
2. Kontroluje, že hodnoty ProductTypeMemory a ProductModelMemory neobsahují značky
3. Kontroluje, že hodnoty neobsahují varianty z VariantNameMemory a VariantValueMemory
4. Ověřuje formát klíčových slov (Google: 5, Zbozi: 2)
5. Aktualizuje NameMemory podle opravených hodnot Type, Brand a Model

Používá původní strukturu souborů, ale implementuje požadovanou novou logiku kontrol a oprav.
"""

import os
import sys
import json
import logging
import csv
import re
import datetime
import shutil
import argparse
from tqdm import tqdm
from typing import Dict, List, Set, Tuple, Optional, Any, Union
from unifierlib.constants import (
    SCRIPT_DIR, DEFAULT_MEMORY_DIR,
    PRODUCT_MODEL_MEMORY_PREFIX, PRODUCT_BRAND_MEMORY_PREFIX,
    NAME_MEMORY_PREFIX, DEFAULT_LANGUAGE,
    MEMORY_KEY_PRODUCT_TYPE_MEMORY, MEMORY_KEY_PRODUCT_MODEL_MEMORY,
    MEMORY_KEY_PRODUCT_BRAND_MEMORY, MEMORY_KEY_VARIANT_NAME_MEMORY,
    MEMORY_KEY_VARIANT_VALUE_MEMORY, MEMORY_KEY_NAME_MEMORY,
    MEMORY_KEY_KEYWORDS_GOOGLE, MEMORY_KEY_KEYWORDS_ZBOZI,
    MEMORY_KEY_CATEGORY_MEMORY
)
from shared.file_ops import load_csv_file, save_csv_file
from shared.logging_config import setup_logging

# Konstanty pro skript
MAX_ITERATIONS = 10  # Maximální počet iterací při řešení překrývajících se hodnot

def parse_arguments() -> argparse.Namespace:
    """Zpracuje argumenty příkazové řádku."""
    parser = argparse.ArgumentParser(description="Memory Checker pro Desaka Unifier.")
    parser.add_argument("--language", "-l", type=str, default=DEFAULT_LANGUAGE,
                        help=f"Kód jazyka (výchozí: {DEFAULT_LANGUAGE})")
    parser.add_argument("--memory-dir", "-m", type=str, default=DEFAULT_MEMORY_DIR,
                        help=f"Adresář s paměťovými soubory (výchozí: {DEFAULT_MEMORY_DIR})")
    parser.add_argument("--debug", "-d", action="store_true",
                        help="Povolit detailní výpisy")
    parser.add_argument("--no-save", "-n", action="store_true",
                        help="Neukládat změny (jen zkontrolovat a nahlásit problémy)")
    parser.add_argument("--fix", "-f", action="store_true",
                        help="Povolit opravy záznamů (výchozí: mazat vadné záznamy)")

    return parser.parse_args()


def load_memory_file(memory_dir: str, filename: str) -> List[Dict[str, str]]:
    """
    Načte paměťový soubor z daného adresáře.

    Args:
        memory_dir: Adresář s paměťovými soubory
        filename: Název souboru k načtení

    Returns:
        Seznam záznamů ze souboru
    """
    file_path = os.path.join(memory_dir, filename)
    if os.path.exists(file_path):
        try:
            data = load_csv_file(file_path)
            logging.debug(f"Načten soubor {filename} s {len(data)} záznamy")
            return data
        except Exception as e:
            logging.error(f"Chyba při načítání souboru {filename}: {str(e)}")
            return []
    else:
        logging.warning(f"Soubor {filename} nenalezen, vytvářím prázdný seznam")
        return []


def save_memory_file(data: List[Dict[str, str]], memory_dir: str, filename: str, no_save: bool = False) -> None:
    """
    Uloží paměťový soubor do daného adresáře.

    Args:
        data: Seznam záznamů k uložení
        memory_dir: Adresář pro uložení souboru
        filename: Název souboru
        no_save: True pokud se nemají ukládat změny, False jinak
    """
    if no_save:
        logging.info(f"Soubor {filename} by byl uložen, ale ukládání je vypnuto (--no-save)")
        return

    file_path = os.path.join(memory_dir, filename)
    try:
        logging.info(f"Ukládám soubor {filename}")
        save_csv_file(data, file_path)
    except Exception as e:
        logging.error(f"Chyba při ukládání souboru {filename}: {str(e)}")


def get_brand_info(memory_dir: str) -> Tuple[Set[str], Dict[str, str]]:
    """
    Extrahuje informace o značkách z BrandCodeList.

    Args:
        memory_dir: Adresář s paměťovými soubory

    Returns:
        Tuple obsahující množinu platných značek a slovník jejich mapování
    """
    brand_code_list = load_memory_file(memory_dir, "BrandCodeList.csv")
    valid_brands = set()
    brand_mapping = {}

    for item in brand_code_list:
        if 'KEY' in item:
            brand_name = item['KEY']
            valid_brands.add(brand_name)

            # Vytvoříme také mapování pro případné alternativní názvy
            if 'VALUE' in item and item['VALUE']:
                brand_mapping[item['KEY']] = item['VALUE']

    return valid_brands, brand_mapping


def check_and_fix_product_brand_memory(memory_dir: str, language: str, no_save: bool = False, fix_mode: bool = False) -> bool:
    """
    Kontroluje hodnoty v ProductBrandMemory podle pravidel:
    1) Každá VALUE musí být v KEY sloupci BrandCodeList
    2) KEY nemá obsahovat hodnotu z KEY sloupce BrandCodeList, pokud ta hodnota není současně ve VALUE

    Pokud fix_mode=True, provádí opravy, jinak vadné záznamy maže.

    Args:
        memory_dir: Adresář s paměťovými soubory
        language: Kód jazyka
        no_save: True pokud se nemají ukládat změny, False jinak
        fix_mode: True pro režim oprav, False pro režim mazání vadných záznamů

    Returns:
        True pokud byly provedeny změny, False jinak
    """
    if fix_mode:
        logging.info("Kontroluji a opravuji soubor ProductBrandMemory...")
    else:
        logging.info("Kontroluji soubor ProductBrandMemory a odstraňuji vadné záznamy...")

    # Načtení potřebných souborů
    filename = f"ProductBrandMemory_{language}.csv"
    brand_memory = load_memory_file(memory_dir, filename)

    if not brand_memory:
        logging.warning(f"ProductBrandMemory_{language} je prázdný nebo chybí")
        return False

    # Získáme platné značky z BrandCodeList
    valid_brands, _ = get_brand_info(memory_dir)

    if not valid_brands:
        logging.error("BrandCodeList je prázdný nebo neobsahuje platné značky")
        return False

    changes_made = False
    items_to_remove = []
    fixed_items_count = 0

    # Kontrola a oprava každého záznamu s progress barem
    for i, item in enumerate(tqdm(brand_memory, desc="Kontrola značek produktů")):
        if 'KEY' not in item or 'VALUE' not in item:
            continue

        product_key = item['KEY']
        brand_value = item['VALUE']

        # Najdeme všechny značky obsažené v KEY produktu
        brands_in_key = [brand for brand in valid_brands if brand in product_key]

        # Konsolidovaná kontrola značek
        needs_correction = False
        suggested_brand = None

        # Kontrola 1: VALUE musí být platná značka
        if brand_value and brand_value not in valid_brands:
            logging.info(f"Neplatná značka: '{brand_value}' pro produkt '{product_key}'")
            needs_correction = True

        # Kontrola 2: Pokud KEY obsahuje značky, VALUE musí být jedna z nich
        if brands_in_key and (not brand_value or brand_value not in brands_in_key):
            logging.info(f"KEY '{product_key}' obsahuje značky {brands_in_key}, ale VALUE je '{brand_value}'")
            needs_correction = True

        # Pokud je potřeba oprava, určíme způsob opravy nebo záznam smažeme
        if needs_correction:
            if fix_mode:
                # Režim oprav - chováme se jako původně
                if len(brands_in_key) == 1:
                    # Jasný případ - v KEY je přesně jedna značka
                    suggested_brand = brands_in_key[0]
                    item['VALUE'] = suggested_brand
                    logging.info(f"Automaticky opravena značka produktu '{product_key}' z '{brand_value}' na '{suggested_brand}'")
                    changes_made = True
                    fixed_items_count += 1
                elif len(brands_in_key) > 1:
                    # V KEY je více značek - vyžaduje manuální opravu
                    logging.info(f"KEY '{product_key}' obsahuje více značek {brands_in_key}")
                    tqdm.write("\n\n")  # Přidáme prázdné řádky pro oddělení od progress baru
                    tqdm.write("=" * 80)  # Výraznější oddělovač
                    tqdm.write("PROBLÉM SE ZNAČKOU PRODUKTU")
                    tqdm.write("-" * 80)
                    tqdm.write(f"Produkt: '{product_key}'")
                    tqdm.write(f"Současná značka: '{brand_value}'")
                    tqdm.write(f"V názvu produktu bylo nalezeno více značek: {', '.join(brands_in_key)}")
                    tqdm.write(f"Je potřeba ručně vybrat správnou značku.")
                    tqdm.write("-" * 80)
                    new_value = input(f"Zadejte správnou značku z: {', '.join(brands_in_key)}: ")
                    tqdm.write("=" * 80)
                    tqdm.write("\n")  # Přidáme prázdný řádek pro oddělení od dalšího progress baru
                    if new_value:
                        item['VALUE'] = new_value
                        logging.info(f"Ručně opravena značka produktu '{product_key}' na '{new_value}'")
                        changes_made = True
                        fixed_items_count += 1
                else:
                    # V KEY není žádná značka - potřebujeme vybrat z platných značek
                    tqdm.write("\n\n")  # Přidáme prázdné řádky pro oddělení od progress baru
                    tqdm.write("=" * 80)  # Výraznější oddělovač
                    tqdm.write("PROBLÉM SE ZNAČKOU PRODUKTU")
                    tqdm.write("-" * 80)
                    tqdm.write(f"Produkt: '{product_key}'")
                    tqdm.write(f"Současná značka: '{brand_value}' není platná nebo není obsažena v názvu produktu")
                    tqdm.write(f"V názvu produktu nebyla nalezena žádná známá značka.")
                    tqdm.write("-" * 80)
                    new_value = input(f"Zadejte platnou značku (prázdný řádek = ponechat stávající): ")
                    tqdm.write("=" * 80)
                    tqdm.write("\n")  # Přidáme prázdný řádek pro oddělení od dalšího progress baru
                    if new_value:
                        item['VALUE'] = new_value
                        logging.info(f"Ručně opravena značka produktu '{product_key}' na '{new_value}'")
                        changes_made = True
                        fixed_items_count += 1
            else:
                # Režim mazání - zaznamenáme položku k odstranění
                items_to_remove.append(i)
                logging.info(f"Označuji k odstranění vadný záznam pro produkt '{product_key}' se značkou '{brand_value}'")
                changes_made = True

    # Odstraníme označené položky (od konce, aby se zachovaly indexy)
    if not fix_mode and items_to_remove:
        for index in sorted(items_to_remove, reverse=True):
            removed_item = brand_memory.pop(index)
            logging.info(f"Odstraněn vadný záznam pro produkt '{removed_item.get('KEY', '')}' se značkou '{removed_item.get('VALUE', '')}'")

        logging.info(f"Celkem odstraněno {len(items_to_remove)} vadných záznamů ze souboru ProductBrandMemory_{language}")

    if changes_made:
        if fix_mode:
            logging.info(f"Bylo provedeno celkem {fixed_items_count} oprav v ProductBrandMemory_{language}")
        else:
            logging.info(f"Bylo odstraněno celkem {len(items_to_remove)} vadných záznamů z ProductBrandMemory_{language}")
        save_memory_file(brand_memory, memory_dir, filename, no_save)
    else:
        logging.info(f"Žádné změny v ProductBrandMemory_{language} nebyly potřeba")

    return changes_made


def check_type_model_contains_brand(memory_dir: str, language: str, no_save: bool = False, fix_mode: bool = False) -> bool:
    """
    Kontroluje hodnoty v ProductTypeMemory a ProductModelMemory, aby neobsahovaly značky.

    Pokud fix_mode=True, provádí opravy (odstraňuje značky z hodnot),
    jinak maže záznamy, které obsahují značky.

    Args:
        memory_dir: Adresář s paměťovými soubory
        language: Kód jazyka
        no_save: True pokud se nemají ukládat změny, False jinak
        fix_mode: True pro režim oprav, False pro režim mazání vadných záznamů

    Returns:
        True pokud byly provedeny změny, False jinak
    """
    if fix_mode:
        logging.info("Kontroluji a opravuji hodnoty v Type a Model, které obsahují značky...")
    else:
        logging.info("Kontroluji hodnoty v Type a Model a odstraňuji záznamy obsahující značky...")

    # Načtení potřebných souborů
    type_filename = f"ProductTypeMemory_{language}.csv"
    model_filename = f"ProductModelMemory_{language}.csv"

    type_memory = load_memory_file(memory_dir, type_filename)
    model_memory = load_memory_file(memory_dir, model_filename)

    # Získáme platné značky z BrandCodeList
    valid_brands, _ = get_brand_info(memory_dir)

    if not valid_brands:
        logging.error("BrandCodeList je prázdný nebo neobsahuje platné značky")
        return False

    type_changes = False
    model_changes = False
    type_items_to_remove = []
    model_items_to_remove = []
    type_fixed_count = 0
    model_fixed_count = 0

    # Kontrola TYPE hodnot s progress barem
    for i, item in enumerate(tqdm(type_memory, desc="Kontrola typů - kontrola značek")):
        if 'KEY' not in item or 'VALUE' not in item or not item['VALUE']:
            continue

        product_key = item['KEY']
        type_value = item['VALUE']

        original_value = type_value
        modified_value = type_value
        contains_brand = False

        # Kontrola, zda typ obsahuje nějakou značku
        for brand in valid_brands:
            # Pouze pokud je značka delší než 1 znak (aby nedocházelo k chybám s jednopísmenými značkami)
            if len(brand) > 1 and re.search(r'\b' + re.escape(brand) + r'\b', type_value, flags=re.IGNORECASE):
                contains_brand = True
                # Pokud jsme v režimu mazání, nemusíme dále kontrolovat
                if not fix_mode:
                    break
                # V režimu oprav odstraníme značku
                modified_value = re.sub(r'\b' + re.escape(brand) + r'\b', '', modified_value, flags=re.IGNORECASE)

        # Pokud hodnota obsahuje značku
        if contains_brand:
            if fix_mode:
                # Režim oprav - vyčistíme a upravíme hodnotu
                modified_value = ' '.join(modified_value.split()).strip()  # Odstranění vícenásobných mezer a trimování

                # Pokud je výsledný řetězec prázdný nebo příliš krátký, zeptáme se uživatele
                if not modified_value or len(modified_value) <= 2:
                    tqdm.write("\n\n")  # Přidáme prázdné řádky pro oddělení od progress baru
                    tqdm.write("=" * 80)  # Výraznější oddělovač
                    tqdm.write("PROBLÉM S TYPEM PRODUKTU - OBSAHUJE ZNAČKU")
                    tqdm.write("-" * 80)
                    tqdm.write(f"Produkt: '{product_key}'")
                    tqdm.write(f"Původní typ: '{original_value}'")
                    tqdm.write(f"Po odstranění značek: '{modified_value}' (příliš krátký nebo prázdný)")
                    tqdm.write(f"Značky nalezené v typu: {', '.join([b for b in valid_brands if re.search(r'\b' + re.escape(b) + r'\b', original_value, re.IGNORECASE)])}")
                    tqdm.write("-" * 80)
                    new_value = input(f"Zadejte novou hodnotu typu (prázdný řádek = ponechat '{original_value}'): ")
                    tqdm.write("=" * 80)
                    tqdm.write("\n")  # Přidáme prázdný řádek pro oddělení od dalšího progress baru
                    if new_value:
                        item['VALUE'] = new_value
                        logging.info(f"Ručně opraven typ produktu '{product_key}' z '{original_value}' na '{new_value}'")
                        type_changes = True
                        type_fixed_count += 1
                else:
                    item['VALUE'] = modified_value
                    logging.info(f"Automaticky odstraněny značky z typu produktu '{product_key}' z '{original_value}' na '{modified_value}'")
                    type_changes = True
                    type_fixed_count += 1
            else:
                # Režim mazání - zaznamenáme položku k odstranění
                type_items_to_remove.append(i)
                logging.info(f"Označuji k odstranění vadný záznam typu pro produkt '{product_key}' s hodnotou '{original_value}' (obsahuje značku)")
                type_changes = True

    # Kontrola MODEL hodnot s progress barem
    for i, item in enumerate(tqdm(model_memory, desc="Kontrola modelů - kontrola značek")):
        if 'KEY' not in item or 'VALUE' not in item or not item['VALUE']:
            continue

        product_key = item['KEY']
        model_value = item['VALUE']

        original_value = model_value
        modified_value = model_value
        contains_brand = False

        # Kontrola, zda model obsahuje nějakou značku
        for brand in valid_brands:
            # Pouze pokud je značka delší než 1 znak (aby nedocházelo k chybám s jednopísmenými značkami)
            if len(brand) > 1 and re.search(r'\b' + re.escape(brand) + r'\b', model_value, flags=re.IGNORECASE):
                contains_brand = True
                # Pokud jsme v režimu mazání, nemusíme dále kontrolovat
                if not fix_mode:
                    break
                # V režimu oprav odstraníme značku
                modified_value = re.sub(r'\b' + re.escape(brand) + r'\b', '', modified_value, flags=re.IGNORECASE)

        # Pokud hodnota obsahuje značku
        if contains_brand:
            if fix_mode:
                # Režim oprav - vyčistíme a upravíme hodnotu
                modified_value = ' '.join(modified_value.split()).strip()  # Odstranění vícenásobných mezer a trimování

                # Pokud je výsledný řetězec prázdný nebo příliš krátký, zeptáme se uživatele
                if not modified_value or len(modified_value) <= 2:
                    tqdm.write("\n\n")  # Přidáme prázdné řádky pro oddělení od progress baru
                    tqdm.write("=" * 80)  # Výraznější oddělovač
                    tqdm.write("PROBLÉM S MODELEM PRODUKTU - OBSAHUJE ZNAČKU")
                    tqdm.write("-" * 80)
                    tqdm.write(f"Produkt: '{product_key}'")
                    tqdm.write(f"Původní model: '{original_value}'")
                    tqdm.write(f"Po odstranění značek: '{modified_value}' (příliš krátký nebo prázdný)")
                    tqdm.write(f"Značky nalezené v modelu: {', '.join([b for b in valid_brands if re.search(r'\b' + re.escape(b) + r'\b', original_value, re.IGNORECASE)])}")
                    tqdm.write("-" * 80)
                    new_value = input(f"Zadejte novou hodnotu modelu (prázdný řádek = ponechat '{original_value}'): ")
                    tqdm.write("=" * 80)
                    tqdm.write("\n")  # Přidáme prázdný řádek pro oddělení od dalšího progress baru
                    if new_value:
                        item['VALUE'] = new_value
                        logging.info(f"Ručně opraven model produktu '{product_key}' z '{original_value}' na '{new_value}'")
                        model_changes = True
                        model_fixed_count += 1
                else:
                    item['VALUE'] = modified_value
                    logging.info(f"Automaticky odstraněny značky z modelu produktu '{product_key}' z '{original_value}' na '{modified_value}'")
                    model_changes = True
                    model_fixed_count += 1
            else:
                # Režim mazání - zaznamenáme položku k odstranění
                model_items_to_remove.append(i)
                logging.info(f"Označuji k odstranění vadný záznam modelu pro produkt '{product_key}' s hodnotou '{original_value}' (obsahuje značku)")
                model_changes = True

    # Odstraníme označené položky (od konce, aby se zachovaly indexy)
    if not fix_mode:
        if type_items_to_remove:
            for index in sorted(type_items_to_remove, reverse=True):
                removed_item = type_memory.pop(index)
                logging.info(f"Odstraněn vadný záznam typu pro produkt '{removed_item.get('KEY', '')}'")
            logging.info(f"Celkem odstraněno {len(type_items_to_remove)} vadných záznamů z ProductTypeMemory_{language}")

        if model_items_to_remove:
            for index in sorted(model_items_to_remove, reverse=True):
                removed_item = model_memory.pop(index)
                logging.info(f"Odstraněn vadný záznam modelu pro produkt '{removed_item.get('KEY', '')}'")
            logging.info(f"Celkem odstraněno {len(model_items_to_remove)} vadných záznamů z ProductModelMemory_{language}")

    # Uložíme změny pro TYPE soubor
    if type_changes:
        if fix_mode:
            logging.info(f"Bylo provedeno celkem {type_fixed_count} oprav v ProductTypeMemory_{language}")
        else:
            logging.info(f"Bylo odstraněno celkem {len(type_items_to_remove)} vadných záznamů z ProductTypeMemory_{language}")
        save_memory_file(type_memory, memory_dir, type_filename, no_save)
    else:
        logging.info(f"Žádné změny v ProductTypeMemory_{language} nebyly potřeba")

    # Uložíme změny pro MODEL soubor
    if model_changes:
        if fix_mode:
            logging.info(f"Bylo provedeno celkem {model_fixed_count} oprav v ProductModelMemory_{language}")
        else:
            logging.info(f"Bylo odstraněno celkem {len(model_items_to_remove)} vadných záznamů z ProductModelMemory_{language}")
        save_memory_file(model_memory, memory_dir, model_filename, no_save)
    else:
        logging.info(f"Žádné změny v ProductModelMemory_{language} nebyly potřeba")

    return type_changes or model_changes


def check_type_model_overlap(memory_dir: str, language: str, no_save: bool = False, fix_mode: bool = False) -> bool:
    """
    Kontroluje a opravuje překrývající se hodnoty mezi ProductTypeMemory a ProductModelMemory.

    Pokud fix_mode=True, provádí opravy překrývajících se hodnot,
    jinak maže záznamy, kde se hodnoty překrývají.

    Args:
        memory_dir: Adresář s paměťovými soubory
        language: Kód jazyka
        no_save: True pokud se nemají ukládat změny, False jinak
        fix_mode: True pro režim oprav, False pro režim mazání vadných záznamů

    Returns:
        True pokud byly provedeny změny, False jinak
    """
    if fix_mode:
        logging.info("Kontroluji a opravuji překrývající se hodnoty mezi typy a modely...")
    else:
        logging.info("Kontroluji překrývající se hodnoty mezi typy a modely a odstraňuji vadné záznamy...")

    # Načtení potřebných souborů
    type_filename = f"ProductTypeMemory_{language}.csv"
    model_filename = f"ProductModelMemory_{language}.csv"

    type_memory = load_memory_file(memory_dir, type_filename)
    model_memory = load_memory_file(memory_dir, model_filename)

    # Vytvoříme slovníky pro rychlé vyhledávání
    product_types = {}
    for item in type_memory:
        if 'KEY' in item and 'VALUE' in item and item['VALUE']:
            product_types[item['KEY']] = item['VALUE']

    product_models = {}
    for item in model_memory:
        if 'KEY' in item and 'VALUE' in item and item['VALUE']:
            product_models[item['KEY']] = item['VALUE']

    # Získání všech unikátních klíčů (produktů)
    all_products = set(product_types.keys()) | set(product_models.keys())

    changes_made = False
    total_type_changes = 0
    total_model_changes = 0

    if fix_mode:
        # Režim oprav - používáme iterativní algoritmus
        iteration_count = 0

        while iteration_count < MAX_ITERATIONS:
            iteration_count += 1
            current_changes = False

            # Dočasné slovníky pro aktualizované hodnoty v této iteraci
            updated_types = {}
            updated_models = {}

            for product_key in tqdm(all_products, desc=f"Kontrola překrývání typů a modelů - iterace {iteration_count}"):
                type_value = product_types.get(product_key, "")
                model_value = product_models.get(product_key, "")

                # Ukládáme výchozí hodnoty do aktualizovaných slovníků
                updated_types[product_key] = type_value
                updated_models[product_key] = model_value

                # Pokud jedna z hodnot chybí, nemůžeme kontrolovat překrývání
                if not type_value or not model_value:
                    continue

                # Kontrola, zda typ obsahuje model nebo model obsahuje typ
                type_contains_model = model_value.lower() in type_value.lower() if model_value else False
                model_contains_type = type_value.lower() in model_value.lower() if type_value else False

                # Pouze pokud dochází k překrytí, pokračujeme
                if not type_contains_model and not model_contains_type:
                    continue

                need_manual_fix = False
                new_type_value = type_value
                new_model_value = model_value

                if type_contains_model:
                    # Zcela jasný případ - automaticky odstraníme model z typu
                    if model_value.strip() and len(model_value) > 2:
                        logging.info(f"Typ '{type_value}' obsahuje model '{model_value}' pro produkt '{product_key}'")
                        new_type_value = type_value.replace(model_value, "").strip()
                        new_type_value = ' '.join(new_type_value.split())  # Odstranění vícenásobných mezer
                        logging.info(f"Automaticky opravuji typ z '{type_value}' na '{new_type_value}'")
                        current_changes = True
                        updated_types[product_key] = new_type_value
                    else:
                        # Krátké nebo prázdné hodnoty - nabídneme manuální opravu
                        need_manual_fix = True

                if model_contains_type:
                    # Zcela jasný případ - automaticky odstraníme typ z modelu
                    if type_value.strip() and len(type_value) > 2:
                        logging.info(f"Model '{model_value}' obsahuje typ '{type_value}' pro produkt '{product_key}'")
                        new_model_value = model_value.replace(type_value, "").strip()
                        new_model_value = ' '.join(new_model_value.split())  # Odstranění vícenásobných mezer
                        logging.info(f"Automaticky opravuji model z '{model_value}' na '{new_model_value}'")
                        current_changes = True
                        updated_models[product_key] = new_model_value
                    else:
                        # Krátké nebo prázdné hodnoty - nabídneme manuální opravu
                        need_manual_fix = True

                # Pokud je potřeba ruční oprava
                if need_manual_fix:
                    tqdm.write("\n\n")  # Přidáme prázdné řádky pro oddělení od progress baru
                    tqdm.write("=" * 80)  # Výraznější oddělovač
                    tqdm.write("PROBLÉM S PŘEKRYTÍM TYPU A MODELU")
                    tqdm.write("-" * 80)
                    tqdm.write(f"Produkt: '{product_key}'")
                    tqdm.write(f"Typ: '{type_value}'")
                    tqdm.write(f"Model: '{model_value}'")

                    # Nabídneme opravu typu
                    if type_contains_model:
                        tqdm.write(f"PROBLÉM: Typ obsahuje model - doporučená oprava: odstranit '{model_value}' z typu")
                        action = input("Opravit typ? (a=automaticky, n=ručně, Enter=ponechat): ").lower()
                        if action == 'a':
                            new_type_value = type_value.replace(model_value, "").strip()
                            new_type_value = ' '.join(new_type_value.split())
                            tqdm.write(f"Typ opraven na: '{new_type_value}'")
                            current_changes = True
                            updated_types[product_key] = new_type_value
                        elif action == 'n':
                            new_type = input(f"Zadejte nový typ (původní: '{type_value}'): ")
                            if new_type:
                                new_type_value = new_type
                                tqdm.write(f"Typ ručně opraven na: '{new_type_value}'")
                                current_changes = True
                                updated_types[product_key] = new_type_value

                    # Nabídneme opravu modelu
                    if model_contains_type:
                        tqdm.write(f"PROBLÉM: Model obsahuje typ - doporučená oprava: odstranit '{type_value}' z modelu")
                        action = input("Opravit model? (a=automaticky, n=ručně, Enter=ponechat): ").lower()
                        if action == 'a':
                            new_model_value = model_value.replace(type_value, "").strip()
                            new_model_value = ' '.join(new_model_value.split())
                            tqdm.write(f"Model opraven na: '{new_model_value}'")
                            current_changes = True
                            updated_models[product_key] = new_model_value
                        elif action == 'n':
                            new_model = input(f"Zadejte nový model (původní: '{model_value}'): ")
                            if new_model:
                                new_model_value = new_model
                                tqdm.write(f"Model ručně opraven na: '{new_model_value}'")
                                current_changes = True
                                updated_models[product_key] = new_model_value

                    tqdm.write("=" * 80)
                    tqdm.write("\n")  # Přidáme prázdný řádek pro oddělení od dalšího progress baru

            # Aktualizujeme slovníky pro další iteraci
            product_types = updated_types
            product_models = updated_models

            # Aktualizujeme paměťové objekty po každé iteraci
            for item in type_memory:
                if 'KEY' in item and item['KEY'] in product_types:
                    if item['VALUE'] != product_types[item['KEY']]:
                        item['VALUE'] = product_types[item['KEY']]

                        current_type_changes += 1

            for item in model_memory:
                if 'KEY' in item and item['KEY'] in product_models:
                    if item['VALUE'] != product_models[item['KEY']]:
                        item['VALUE'] = product_models[item['KEY']]
                        current_model_changes += 1

            total_type_changes += current_type_changes
            total_model_changes += current_model_changes

            # Pokud nebyly provedeny žádné změny v této iteraci, končíme
            if not current_changes:
                break

            changes_made = True
            logging.info(f"Iterace {iteration_count}: Provedeno {current_type_changes} oprav typů a {current_model_changes} oprav modelů")

            # Pokud jsme dosáhli maximálního počtu iterací, upozorníme na to
            if iteration_count >= MAX_ITERATIONS:
                logging.warning(f"Dosažen maximální počet iterací ({MAX_ITERATIONS}), ukončuji opravy překrývajících se hodnot")

    else:
        # Režim mazání - identifikujeme a odstraníme záznamy s překrývajícími se hodnotami
        type_items_to_remove = []
        model_items_to_remove = []

        # Procházíme všechny produkty a kontrolujeme překrývání
        for product_key in tqdm(all_products, desc="Kontrola překrytí typů a modelů"):
            type_value = product_types.get(product_key, "")
            model_value = product_models.get(product_key, "")

            if not type_value or not model_value:
                # Pokud jedna z hodnot chybí, nemůžeme kontrolovat překrývání
                continue

            # Kontrola, zda typ obsahuje model nebo model obsahuje typ
            type_contains_model = model_value.lower() in type_value.lower()
            model_contains_type = type_value.lower() in model_value.lower()

            if type_contains_model or model_contains_type:
                # Najdeme odpovídající položky v paměťových souborech a označíme je k odstranění
                for i, item in enumerate(type_memory):
                    if 'KEY' in item and item['KEY'] == product_key:
                        if i not in type_items_to_remove:  # Kontrola, zda už není označena k odstranění
                            type_items_to_remove.append(i)
                            logging.info(f"Označuji k odstranění záznam typu pro produkt '{product_key}' kvůli překrývání s modelem")
                            changes_made = True

                for i, item in enumerate(model_memory):
                    if 'KEY' in item and item['KEY'] == product_key:
                        if i not in model_items_to_remove:  # Kontrola, zda už není označena k odstranění
                            model_items_to_remove.append(i)
                            logging.info(f"Označuji k odstranění záznam modelu pro produkt '{product_key}' kvůli překrývání s typem")
                            changes_made = True

        # Odstraníme označené položky (od konce, aby se zachovaly indexy)
        if type_items_to_remove:
            for index in sorted(type_items_to_remove, reverse=True):
                removed_item = type_memory.pop(index)
                logging.info(f"Odstraněn záznam typu pro produkt '{removed_item.get('KEY', '')}' kvůli překrývání s modelem")
            logging.info(f"Celkem odstraněno {len(type_items_to_remove)} záznamů z ProductTypeMemory_{language} kvůli překrývání s modelem")
            total_type_changes = len(type_items_to_remove)

        if model_items_to_remove:
            for index in sorted(model_items_to_remove, reverse=True):
                removed_item = model_memory.pop(index)
                logging.info(f"Odstraněn záznam modelu pro produkt '{removed_item.get('KEY', '')}' kvůli překrývání s typem")
            logging.info(f"Celkem odstraněno {len(model_items_to_remove)} záznamů z ProductModelMemory_{language} kvůli překrývání s typem")
            total_model_changes = len(model_items_to_remove)

    # Uložíme změny
    if changes_made:
        if fix_mode:
            logging.info(f"Bylo provedeno celkem {total_type_changes} oprav v ProductTypeMemory_{language} a {total_model_changes} oprav v ProductModelMemory_{language} kvůli překrývání")
        else:
            logging.info(f"Bylo odstraněno celkem {total_type_changes} záznamů z ProductTypeMemory_{language} a {total_model_changes} záznamů z ProductModelMemory_{language} kvůli překrývání")
        # Uložíme opravené soubory
        save_memory_file(type_memory, memory_dir, type_filename, no_save)
        save_memory_file(model_memory, memory_dir, model_filename, no_save)
    else:
        logging.info("Žádné překrývající se hodnoty mezi typy a modely nebyly nalezeny")

    return changes_made


def check_keywords_format(memory_dir: str, language: str, no_save: bool = False, fix_mode: bool = False) -> bool:
    """
    Kontroluje a opravuje formát klíčových slov:
    - KeywordsGoogle má mít 5 čárkou oddělených hodnot
    - KeywordsZbozi má mít 2 čárkou oddělené hodnoty

    Pokud fix_mode=True, provádí opravy,
    jinak maže záznamy, které nemají správný počet klíčových slov.

    Args:
        memory_dir: Adresář s paměťovými soubory
        language: Kód jazyka
        no_save: True pokud se nemají ukládat změny, False jinak
        fix_mode: True pro režim oprav, False pro režim mazání vadných záznamů

    Returns:
        True pokud byly provedeny změny, False jinak
    """
    if fix_mode:
        logging.info("Kontroluji a opravuji formát klíčových slov...")
    else:
        logging.info("Kontroluji formát klíčových slov a odstraňuji záznamy s nesprávným počtem hodnot...")

    # Načtení potřebných souborů
    google_keywords_filename = f"KeywordsGoogle_{language}.csv"
    zbozi_keywords_filename = f"KeywordsZbozi_{language}.csv"

    google_keywords = load_memory_file(memory_dir, google_keywords_filename)
    zbozi_keywords = load_memory_file(memory_dir, zbozi_keywords_filename)

    google_changes = False
    zbozi_changes = False
    google_items_to_remove = []
    zbozi_items_to_remove = []
    google_fixed_count = 0
    zbozi_fixed_count = 0

    # Kontrola a oprava formátu Google klíčových slov (5 hodnot) s progress barem
    for i, item in enumerate(tqdm(google_keywords, desc="Kontrola Google klíčových slov")):
        if 'KEY' not in item or 'VALUE' not in item:
            continue

        product_key = item['KEY']
        keywords_value = item['VALUE'].strip()

        if not keywords_value:
            continue

        # Rozdělit klíčová slova podle čárky
        keywords = [kw.strip() for kw in keywords_value.split(',')]
        num_keywords = len(keywords)

        if num_keywords != 5:
            logging.info(f"Google klíčová slova produktu '{product_key}' mají {num_keywords} hodnot místo 5: '{keywords_value}'")

            if fix_mode:
                # Jasný případ - klíčových slov je více než 5, automaticky zkrátíme
                if num_keywords > 5:
                    new_keywords = keywords[:5]
                    new_value = ', '.join(new_keywords)

                    logging.info(f"Automaticky zkracuji Google klíčová slova produktu '{product_key}' na '{new_value}'")
                    item['VALUE'] = new_value
                    google_changes = True
                    google_fixed_count += 1

                # Nejasný případ - klíčových slov je méně než 5, nabídneme doplnění
                elif num_keywords < 5:
                    tqdm.write("\n\n")  # Přidáme prázdné řádky pro oddělení od progress baru
                    tqdm.write("=" * 80)  # Výraznější oddělovač
                    tqdm.write("PROBLÉM S FORMÁTEM KLÍČOVÝCH SLOV GOOGLE")
                    tqdm.write("-" * 80)
                    tqdm.write(f"Produkt: '{product_key}'")
                    tqdm.write(f"Současná klíčová slova ({num_keywords}/5): '{keywords_value}'")
                    tqdm.write(f"Google klíčová slova musí obsahovat přesně 5 hodnot oddělených čárkou.")
                    tqdm.write("-" * 80)
                    tqdm.write("Zadejte všech 5 klíčových slov oddělených čárkou (nebo Enter pro ponechání):")
                    new_value = input("> ")
                    tqdm.write("=" * 80)
                    tqdm.write("\n")  # Přidáme prázdný řádek pro oddělení od dalšího progress baru
                    if new_value:
                        item['VALUE'] = new_value
                        google_changes = True
                        google_fixed_count += 1
                        logging.info(f"Ručně opravena Google klíčová slova produktu '{product_key}' na '{new_value}'")
            else:
                # Režim mazání - označíme položku k odstranění
                google_items_to_remove.append(i)
                logging.info(f"Označuji k odstranění záznam Google klíčových slov pro produkt '{product_key}' s nesprávným počtem hodnot")
                google_changes = True

    # Kontrola a oprava formátu Zbozi klíčových slov (2 hodnoty) s progress barem
    for i, item in enumerate(tqdm(zbozi_keywords, desc="Kontrola Zboží klíčových slov")):
        if 'KEY' not in item or 'VALUE' not in item:
            continue

        product_key = item['KEY']
        keywords_value = item['VALUE'].strip()

        if not keywords_value:
            continue

        # Rozdělit klíčová slova podle čárky
        keywords = [kw.strip() for kw in keywords_value.split(',')]
        num_keywords = len(keywords)

        if num_keywords != 2:
            logging.info(f"Zbozi klíčová slova produktu '{product_key}' mají {num_keywords} hodnot místo 2: '{keywords_value}'")

            if fix_mode:
                # Jasný případ - klíčových slov je více než 2, automaticky zkrátíme
                if num_keywords > 2:
                    new_keywords = keywords[:2]
                    new_value = ', '.join(new_keywords)

                    logging.info(f"Automaticky zkracuji Zbozi klíčová slova produktu '{product_key}' na '{new_value}'")
                    item['VALUE'] = new_value
                    zbozi_changes = True
                    zbozi_fixed_count += 1

                # Nejasný případ - klíčových slov je méně než 2, nabídneme doplnění
                elif num_keywords < 2:
                    tqdm.write("\n\n")  # Přidáme prázdné řádky pro oddělení od progress baru
                    tqdm.write("=" * 80)  # Výraznější oddělovač
                    tqdm.write("PROBLÉM S FORMÁTEM KLÍČOVÝCH SLOV ZBOŽÍ")
                    tqdm.write("-" * 80)
                    tqdm.write(f"Produkt: '{product_key}'")
                    tqdm.write(f"Současná klíčová slova ({num_keywords}/2): '{keywords_value}'")
                    tqdm.write(f"Zboží klíčová slova musí obsahovat přesně 2 hodnoty oddělené čárkou.")
                    tqdm.write("-" * 80)
                    tqdm.write("Zadejte 2 klíčová slova oddělená čárkou (nebo Enter pro ponechání):")
                    new_value = input("> ")
                    tqdm.write("=" * 80)
                    tqdm.write("\n")  # Přidáme prázdný řádek pro oddělení od dalšího progress baru
                    if new_value:
                        item['VALUE'] = new_value
                        zbozi_changes = True
                        zbozi_fixed_count += 1
                        logging.info(f"Ručně opravena Zbozi klíčová slova produktu '{product_key}' na '{new_value}'")
            else:
                # Režim mazání - označíme položku k odstranění
                zbozi_items_to_remove.append(i)
                logging.info(f"Označuji k odstranění záznam Zbozi klíčových slov pro produkt '{product_key}' s nesprávným počtem hodnot")
                zbozi_changes = True

    # Odstranění položek v režimu mazání
    if not fix_mode:
        if google_items_to_remove:
            for index in sorted(google_items_to_remove, reverse=True):
                removed_item = google_keywords.pop(index)
                logging.info(f"Odstraněn vadný záznam Google klíčových slov pro produkt '{removed_item.get('KEY', '')}'")
            logging.info(f"Celkem odstraněno {len(google_items_to_remove)} vadných záznamů z KeywordsGoogle_{language}")

        if zbozi_items_to_remove:
            for index in sorted(zbozi_items_to_remove, reverse=True):
                removed_item = zbozi_keywords.pop(index)
                logging.info(f"Odstraněn vadný záznam Zbozi klíčových slov pro produkt '{removed_item.get('KEY', '')}'")
            logging.info(f"Celkem odstraněno {len(zbozi_items_to_remove)} vadných záznamů z KeywordsZbozi_{language}")

    # Uložíme změny
    if google_changes:
        if fix_mode:
            logging.info(f"Bylo provedeno celkem {google_fixed_count} oprav formátu Google klíčových slov v KeywordsGoogle_{language}")
        else:
            logging.info(f"Bylo odstraněno celkem {len(google_items_to_remove)} vadných záznamů Google klíčových slov z KeywordsGoogle_{language}")
        save_memory_file(google_keywords, memory_dir, google_keywords_filename, no_save)
    else:
        logging.info(f"Všechna Google klíčová slova v KeywordsGoogle_{language} mají správný formát")

    if zbozi_changes:
        if fix_mode:
            logging.info(f"Bylo provedeno celkem {zbozi_fixed_count} oprav formátu Zbozi klíčových slov v KeywordsZbozi_{language}")
        else:
            logging.info(f"Bylo odstraněno celkem {len(zbozi_items_to_remove)} vadných záznamů Zbozi klíčových slov z KeywordsZbozi_{language}")
        save_memory_file(zbozi_keywords, memory_dir, zbozi_keywords_filename, no_save)
    else:
        logging.info(f"Všechna Zbozi klíčová slova v KeywordsZbozi_{language} mají správný formát")

    return google_changes or zbozi_changes


def check_variant_in_type_model(memory_dir: str, language: str, no_save: bool = False, fix_mode: bool = False) -> bool:
    """
    Kontroluje hodnoty v ProductTypeMemory a ProductModelMemory, aby neobsahovaly varianty.

    Pokud fix_mode=True, provádí opravy (odstraňuje variantní hodnoty z typů a modelů),
    jinak maže záznamy, které obsahují variantní hodnoty.

    Args:
        memory_dir: Adresář s paměťovými soubory
        language: Kód jazyka
        no_save: True pokud se nemají ukládat změny, False jinak
        fix_mode: True pro režim oprav, False pro režim mazání vadných záznamů

    Returns:
        True pokud byly provedeny změny, False jinak
    """
    if fix_mode:
        logging.info("Kontroluji a opravuji hodnoty v Type a Model, které obsahují varianty...")
    else:
        logging.info("Kontroluji hodnoty v Type a Model a odstraňuji záznamy obsahující variantní hodnoty...")

    # Načtení potřebných souborů
    type_filename = f"ProductTypeMemory_{language}.csv"
    model_filename = f"ProductModelMemory_{language}.csv"
    variant_name_filename = f"VariantNameMemory_{language}.csv"
    variant_value_filename = f"VariantValueMemory_{language}.csv"

    type_memory = load_memory_file(memory_dir, type_filename)
    model_memory = load_memory_file(memory_dir, model_filename)
    variant_name_memory = load_memory_file(memory_dir, variant_name_filename)
    variant_value_memory = load_memory_file(memory_dir, variant_value_filename)

    # Vytvoříme množiny všech variantních názvů a hodnot pro rychlé vyhledávání
    variant_names = set()
    for item in variant_name_memory:
        if 'VALUE' in item and item['VALUE']:
            variant_names.add(item['VALUE'].lower())

    variant_values = set()
    for item in variant_value_memory:
        if 'VALUE' in item and item['VALUE']:
            variant_values.add(item['VALUE'].lower())

    # Pokud nemáme žádné varianty k kontrole, vrátíme False
    if not variant_names and not variant_values:
        logging.info("Žádné variantní hodnoty nebyly nalezeny k porovnání")
        return False

    type_changes = False
    model_changes = False
    type_items_to_remove = []
    model_items_to_remove = []
    type_fixed_count = 0
    model_fixed_count = 0

    # Kontrola TYPE hodnot s progress barem
    for i, item in enumerate(tqdm(type_memory, desc="Kontrola typů - kontrola variant")):
        if 'KEY' not in item or 'VALUE' not in item or not item['VALUE']:
            continue

        product_key = item['KEY']
        type_value = item['VALUE']
        original_value = type_value
        modified_value = type_value
        contains_variant = False

        # Kontrola, zda typ obsahuje nějaký variantní název
        for variant_name in variant_names:
            if len(variant_name) > 1 and re.search(r'\b' + re.escape(variant_name) + r'\b', type_value, flags=re.IGNORECASE):
                contains_variant = True
                # Pokud jsme v režimu mazání, nemusíme dále kontrolovat
                if not fix_mode:
                    break
                # V režimu oprav odstraníme variantní název
                modified_value = re.sub(r'\b' + re.escape(variant_name) + r'\b', '', modified_value, flags=re.IGNORECASE)

        # Kontrola, zda typ obsahuje nějakou variantní hodnotu
        if not contains_variant or fix_mode:  # Pokračujeme jen pokud jsme nedetekovali varianty nebo jsme v režimu oprav
            for variant_value in variant_values:
                if len(variant_value) > 1 and re.search(r'\b' + re.escape(variant_value) + r'\b', type_value, flags=re.IGNORECASE):
                    contains_variant = True
                    # Pokud jsme v režimu mazání, nemusíme dále kontrolovat
                    if not fix_mode:
                        break
                    # V režimu oprav odstraníme variantní hodnotu
                    modified_value = re.sub(r'\b' + re.escape(variant_value) + r'\b', '', modified_value, flags=re.IGNORECASE)

        # Pokud hodnota obsahuje variantu
        if contains_variant:
            if fix_mode:
                # Režim oprav - vyčistíme a upravíme hodnotu
                modified_value = ' '.join(modified_value.split()).strip()  # Odstranění vícenásobných mezer a trimování

                # Pokud je výsledný řetězec prázdný nebo příliš krátký, zeptáme se uživatele
                if not modified_value or len(modified_value) <= 2:
                    tqdm.write("\n\n")  # Přidáme prázdné řádky pro oddělení od progress baru
                    tqdm.write("=" * 80)  # Výraznější oddělovač
                    tqdm.write("PROBLÉM S TYPEM PRODUKTU - OBSAHUJE VARIANTU")
                    tqdm.write("-" * 80)
                    tqdm.write(f"Produkt: '{product_key}'")
                    tqdm.write(f"Původní typ: '{original_value}'")
                    tqdm.write(f"Po odstranění variant: '{modified_value}' (příliš krátký nebo prázdný)")
                    tqdm.write("-" * 80)
                    new_value = input(f"Zadejte novou hodnotu typu (prázdný řádek = ponechat '{original_value}'): ")
                    tqdm.write("=" * 80)
                    tqdm.write("\n")  # Přidáme prázdný řádek pro oddělení od dalšího progress baru
                    if new_value:
                        item['VALUE'] = new_value
                        logging.info(f"Ručně opraven typ produktu '{product_key}' z '{original_value}' na '{new_value}'")
                        type_changes = True
                        type_fixed_count += 1
                else:
                    item['VALUE'] = modified_value
                    logging.info(f"Automaticky odstraněny varianty z typu produktu '{product_key}' z '{original_value}' na '{modified_value}'")
                    type_changes = True
                    type_fixed_count += 1
            else:
                # Režim mazání - zaznamenáme položku k odstranění
                type_items_to_remove.append(i)
                logging.info(f"Označuji k odstranění vadný záznam typu pro produkt '{product_key}' s hodnotou '{original_value}' (obsahuje variantu)")
                type_changes = True

    # Kontrola MODEL hodnot s progress barem
    for i, item in enumerate(tqdm(model_memory, desc="Kontrola modelů - kontrola variant")):
        if 'KEY' not in item or 'VALUE' not in item or not item['VALUE']:
            continue

        product_key = item['KEY']
        model_value = item['VALUE']

        original_value = model_value
        modified_value = model_value
        contains_variant = False

        # Kontrola, zda model obsahuje nějaký variantní název
        for variant_name in variant_names:
            if len(variant_name) > 1 and re.search(r'\b' + re.escape(variant_name) + r'\b', model_value, flags=re.IGNORECASE):
                contains_variant = True
                # Pokud jsme v režimu mazání, nemusíme dále kontrolovat
                if not fix_mode:
                    break
                # V režimu oprav odstraníme variantní název
                modified_value = re.sub(r'\b' + re.escape(variant_name) + r'\b', '', modified_value, flags=re.IGNORECASE)

        # Kontrola, zda model obsahuje nějakou variantní hodnotu
        if not contains_variant or fix_mode:  # Pokračujeme jen pokud jsme nedetekovali varianty nebo jsme v režimu oprav
            for variant_value in variant_values:
                if len(variant_value) > 1 and re.search(r'\b' + re.escape(variant_value) + r'\b', model_value, flags=re.IGNORECASE):
                    contains_variant = True
                    # Pokud jsme v režimu mazání, nemusíme dále kontrolovat
                    if not fix_mode:
                        break
                    # V režimu oprav odstraníme variantní hodnotu
                    modified_value = re.sub(r'\b' + re.escape(variant_value) + r'\b', '', modified_value, flags=re.IGNORECASE)

        # Pokud hodnota obsahuje variantu
        if contains_variant:
            if fix_mode:
                # Režim oprav - vyčistíme a upravíme hodnotu
                modified_value = ' '.join(modified_value.split()).strip()  # Odstranění vícenásobných mezer a trimování

                # Pokud je výsledný řetězec prázdný nebo příliš krátký, zeptáme se uživatele
                if not modified_value or len(modified_value) <= 2:
                    tqdm.write("\n\n")  # Přidáme prázdné řádky pro oddělení od progress baru
                    tqdm.write("=" * 80)  # Výraznější oddělovač
                    tqdm.write("PROBLÉM S MODELEM PRODUKTU - OBSAHUJE VARIANTU")
                    tqdm.write("-" * 80)
                    tqdm.write(f"Produkt: '{product_key}'")
                    tqdm.write(f"Původní model: '{original_value}'")
                    tqdm.write(f"Po odstranění variant: '{modified_value}' (příliš krátký nebo prázdný)")
                    tqdm.write("-" * 80)
                    new_value = input(f"Zadejte novou hodnotu modelu (prázdný řádek = ponechat '{original_value}'): ")
                    tqdm.write("=" * 80)
                    tqdm.write("\n")  # Přidáme prázdný řádek pro oddělení od dalšího progress baru
                    if new_value:
                        item['VALUE'] = new_value
                        logging.info(f"Ručně opraven model produktu '{product_key}' z '{original_value}' na '{new_value}'")
                        model_changes = True
                        model_fixed_count += 1
                else:
                    item['VALUE'] = modified_value
                    logging.info(f"Automaticky odstraněny varianty z modelu produktu '{product_key}' z '{original_value}' na '{modified_value}'")
                    model_changes = True
                    model_fixed_count += 1
            else:
                # Režim mazání - zaznamenáme položku k odstranění
                model_items_to_remove.append(i)
                logging.info(f"Označuji k odstranění vadný záznam modelu pro produkt '{product_key}' s hodnotou '{original_value}' (obsahuje variantu)")
                model_changes = True

    # Odstraníme označené položky (od konce, aby se zachovaly indexy)
    if not fix_mode:
        if type_items_to_remove:
            for index in sorted(type_items_to_remove, reverse=True):
                removed_item = type_memory.pop(index)
                logging.info(f"Odstraněn vadný záznam typu pro produkt '{removed_item.get('KEY', '')}'")
            logging.info(f"Celkem odstraněno {len(type_items_to_remove)} vadných záznamů z ProductTypeMemory_{language} obsahujících varianty")

        if model_items_to_remove:
            for index in sorted(model_items_to_remove, reverse=True):
                removed_item = model_memory.pop(index)
                logging.info(f"Odstraněn vadný záznam modelu pro produkt '{removed_item.get('KEY', '')}'")
            logging.info(f"Celkem odstraněno {len(model_items_to_remove)} vadných záznamů z ProductModelMemory_{language} obsahujících varianty")

    # Uložíme změny pro TYPE soubor
    if type_changes:
        if fix_mode:
            logging.info(f"Bylo provedeno celkem {type_fixed_count} oprav variant v ProductTypeMemory_{language}")
        else:
            logging.info(f"Bylo odstraněno celkem {len(type_items_to_remove)} vadných záznamů z ProductTypeMemory_{language} obsahujících varianty")
        save_memory_file(type_memory, memory_dir, type_filename, no_save)
    else:
        logging.info(f"Žádné změny v ProductTypeMemory_{language} nebyly potřeba")

    # Uložíme změny pro MODEL soubor
    if model_changes:
        if fix_mode:
            logging.info(f"Bylo provedeno celkem {model_fixed_count} oprav variant v ProductModelMemory_{language}")
        else:
            logging.info(f"Bylo odstraněno celkem {len(model_items_to_remove)} vadných záznamů z ProductModelMemory_{language} obsahujících varianty")
        save_memory_file(model_memory, memory_dir, model_filename, no_save)
    else:
        logging.info(f"Žádné změny v ProductModelMemory_{language} nebyly potřeba")

    return type_changes or model_changes


def update_name_memory(memory_dir: str, language: str, no_save: bool = False) -> bool:
    """
    Aktualizuje hodnoty v NameMemory na základě hodnot z ProductTypeMemory, ProductBrandMemory a ProductModelMemory.
    Také odstraňuje záznamy v NameMemory, pokud odpovídající klíč byl odstraněn z některého z paměťových souborů.

    Args:
        memory_dir: Adresář s paměťovými soubory
        language: Kód jazyka
        no_save: True pokud se nemají ukládat změny, False jinak

    Returns:
        True pokud byly provedeny změny, False jinak
    """
    logging.info(f"Aktualizuji NameMemory_{language} na základě typů, značek a modelů...")

    # Načtení potřebných souborů
    name_filename = f"NameMemory_{language}.csv"
    type_filename = f"ProductTypeMemory_{language}.csv"
    brand_filename = f"ProductBrandMemory_{language}.csv"
    model_filename = f"ProductModelMemory_{language}.csv"

    name_memory = load_memory_file(memory_dir, name_filename)
    type_memory = load_memory_file(memory_dir, type_filename)
    brand_memory = load_memory_file(memory_dir, brand_filename)
    model_memory = load_memory_file(memory_dir, model_filename)

    # Vytvoření slovníků pro rychlý přístup k datům
    type_values = {}
    for item in type_memory:
        if 'KEY' in item and 'VALUE' in item:
            type_values[item['KEY']] = item['VALUE']

    brand_values = {}
    for item in brand_memory:
        if 'KEY' in item and 'VALUE' in item:
            brand_values[item['KEY']] = item['VALUE']

    model_values = {}
    for item in model_memory:
        if 'KEY' in item and 'VALUE' in item:
            model_values[item['KEY']] = item['VALUE']

    # Převedení NameMemory na slovník pro rychlejší aktualizace
    name_memory_dict = {}
    for item in name_memory:
        if 'KEY' in item and 'VALUE' in item:
            name_memory_dict[item['KEY']] = item['VALUE']

    # Získání všech unikátních klíčů z paměťových souborů
    all_memory_keys = set(type_values.keys()) | set(brand_values.keys()) | set(model_values.keys())

    # Získání všech unikátních klíčů z NameMemory
    name_memory_keys = set(name_memory_dict.keys())

    # Klíče, které jsou v NameMemory, ale nejsou v žádném z paměťových souborů
    keys_to_remove = name_memory_keys - all_memory_keys

    changes_made = False
    removed_count = 0
    updated_count = 0
    added_count = 0

    # Odstraníme záznamy, které už neexistují v ostatních paměťových souborech
    if keys_to_remove:
        for key in keys_to_remove:
            logging.info(f"Odstraňuji z NameMemory záznam pro produkt '{key}', který byl odstraněn z některého z paměťových souborů")
            name_memory_dict.pop(key)
            changes_made = True
            removed_count += 1
        logging.info(f"Celkem odstraněno {removed_count} záznamů z NameMemory_{language}, které byly odstraněny z jiných paměťových souborů")

    # Pro každý produkt sestavíme novou hodnotu v NameMemory s progress barem
    for product_key in tqdm(all_memory_keys, desc="Aktualizace názvů produktů"):
        product_type = type_values.get(product_key, "")
        product_brand = brand_values.get(product_key, "")
        product_model = model_values.get(product_key, "")

        # Sestavíme nový název jako spojení typu, značky a modelu
        parts = []
        if product_type:
            parts.append(product_type)
        if product_brand:
            parts.append(product_brand)
        if product_model:
            parts.append(product_model)

        new_name = " ".join(parts).strip()

        # Pokud je nový název prázdný, pokračujeme dalším produktem
        if not new_name:
            continue

        # Aktualizujeme nebo přidáme hodnotu v NameMemory
        old_name = name_memory_dict.get(product_key, "")

        if new_name != old_name:
            if old_name:
                # Aktualizujeme existující záznam
                updated_count += 1
            else:
                # Přidáváme nový záznam
                added_count += 1

            name_memory_dict[product_key] = new_name
            changes_made = True
            logging.debug(f"Aktualizován název produktu '{product_key}' z '{old_name}' na '{new_name}'")

    # Pokud byly provedeny změny, aktualizujeme NameMemory
    if changes_made:
        # Vytvoříme nový seznam položek pro NameMemory
        new_name_memory = []
        for product_key, name_value in name_memory_dict.items():
            new_name_memory.append({'KEY': product_key, 'VALUE': name_value})

        # Nahradíme původní NameMemory novým a uložíme
        logging.info(f"Odstraněno {removed_count} záznamů, aktualizováno {updated_count} záznamů a přidáno {added_count} nových záznamů v NameMemory_{language}")
        save_memory_file(new_name_memory, memory_dir, name_filename, no_save)
    else:
        logging.info(f"Žádné změny v NameMemory_{language} nebyly potřeba")

    return changes_made


def check_unique_values(memory_dir: str, language: str, no_save: bool = False, fix_mode: bool = False) -> bool:
    """
    Kontroluje a opravuje unikátní hodnoty ve všech paměťových souborech.
    Pro každou unikátní hodnotu v souborech se ptá uživatele, zda je platná.

    Hodnoty lišící se pouze velikostí písmen jsou považovány za totožné,
    přičemž se preferuje hodnota začínající velkým písmenem.

    Soubory jsou zpracovávány vzestupně podle počtu unikátních hodnot.

    Pokud fix_mode=True, umožňuje nahradit neplatné hodnoty novými,
    jinak neplatné hodnoty odstraňuje.

    Args:
        memory_dir: Adresář s paměťovými soubory
        language: Kód jazyka
        no_save: True pokud se nemají ukládat změny, False jinak
        fix_mode: True pro režim oprav, False pro režim mazání neplatných hodnot

    Returns:
        True pokud byly provedeny změny, False jinak
    """
    logging.info("Spouštím kontrolu unikátních hodnot ve všech paměťových souborech...")

    # Základní seznam paměťových souborů k kontrole (vždy kontrolované)
    memory_file_keys = [
        MEMORY_KEY_PRODUCT_TYPE_MEMORY,
        MEMORY_KEY_PRODUCT_MODEL_MEMORY,
        MEMORY_KEY_PRODUCT_BRAND_MEMORY,
        MEMORY_KEY_VARIANT_NAME_MEMORY,
        MEMORY_KEY_VARIANT_VALUE_MEMORY,
        MEMORY_KEY_CATEGORY_MEMORY
    ]

    # Soubory kontrolované pouze v režimu oprav (fix_mode=True)
    if fix_mode:
        memory_file_keys.extend([
            MEMORY_KEY_NAME_MEMORY,       # NameMemory kontrolujeme pouze v režimu oprav
            MEMORY_KEY_KEYWORDS_GOOGLE,   # KeywordsGoogle kontrolujeme pouze v režimu oprav
            MEMORY_KEY_KEYWORDS_ZBOZI     # KeywordsZbozi kontrolujeme pouze v režimu oprav
        ])

    # Formátujeme názvy souborů s příslušným jazykem
    memory_files = [key_template.format(language=language) + ".csv" for key_template in memory_file_keys]

    # Struktura pro uchování informací o souborech a jejich unikátních hodnotách
    file_info = []

    # Pro každý soubor spočítáme počet unikátních hodnot
    for filename in memory_files:
        memory_data = load_memory_file(memory_dir, filename)
        if not memory_data:
            logging.info(f"Soubor {filename} je prázdný nebo neexistuje, přeskakuji.")
            continue

        # Vytvoříme slovník pro case-insensitive hodnoty
        unique_values_dict = {}

        # Projdeme všechny hodnoty a vytvoříme slovník case-insensitive hodnot
        for item in memory_data:
            if 'VALUE' in item and item['VALUE']:
                value = item['VALUE']
                lower_value = value.lower()

                # Pokud hodnota se stejným lowercase již existuje, rozhodneme, kterou z nich zachovat
                if lower_value in unique_values_dict:
                    # Preferujeme hodnotu začínající velkým písmenem
                    if value[0].isupper() and not unique_values_dict[lower_value][0].isupper():
                        unique_values_dict[lower_value] = value
                else:
                    # Pokud je to první výskyt, uložíme hodnotu
                    unique_values_dict[lower_value] = value

        # Přidáme informace o souboru do seznamu
        file_info.append({
            'filename': filename,
            'unique_values_count': len(unique_values_dict),
            'unique_values_dict': unique_values_dict,
            'memory_data': memory_data
        })

    # Seřadíme soubory podle počtu unikátních hodnot vzestupně
    sorted_file_info = sorted(file_info, key=lambda x: x['unique_values_count'])

    changes_made = False

    # Nyní procházíme soubory v seřazeném pořadí (od nejmenšího počtu unikátních hodnot)
    for file_data in sorted_file_info:
        filename = file_data['filename']
        unique_values_dict = file_data['unique_values_dict']
        memory_data = file_data['memory_data']
        unique_values_count = file_data['unique_values_count']

        # Získáme seznam unikátních hodnot
        unique_values = list(unique_values_dict.values())

        # Seřadíme hodnoty abecedně (case-insensitive)
        sorted_values = sorted(unique_values, key=lambda x: x.lower())

        logging.info(f"Kontroluji {unique_values_count} unikátních hodnot v souboru {filename}")
        print(f"\n{'=' * 80}")
        print(f"KONTROLA UNIKÁTNÍCH HODNOT V SOUBORU {filename}")
        print(f"{'=' * 80}")
        print(f"Soubor obsahuje {unique_values_count} unikátních hodnot")
        print("Pro každou hodnotu zadejte A (platná) nebo N (neplatná)")
        print("Stiskněte Enter pro potvrzení platné hodnoty (výchozí: A)")
        print("-" * 80)

        file_changes = False
        invalid_values = []

        # Ptáme se na každou unikátní hodnotu - místo progressbaru vypisujeme čísla položek
        total_values = len(sorted_values)
        for i, value in enumerate(sorted_values):
            # Vypočítáme procentuální postup (zaokrouhlený na 2 desetinná místa)
            progress_percent = round((i + 1) / total_values * 100, 2)

            # Vypíšeme informace o postupu
            print(f"Hodnota {i+1}/{total_values} ({progress_percent}%): '{value}'")
            response = input(f"Je '{value}' platná hodnota? [A/N]: ").strip().upper()

            # Pokud je odpověď prázdná nebo A, hodnota je platná
            if response != "N":
                continue

            # Hodnota není platná
            invalid_values.append(value)
            file_changes = True

        # Zpracování neplatných hodnot
        if invalid_values:
            items_to_remove = []
            items_to_fix = {}

            # Vytvoříme množinu neplatných hodnot v lowercase pro case-insensitive porovnávání
            lower_invalid_values = {val.lower() for val in invalid_values}

            # Procházíme všechny položky a hledáme ty s neplatnými hodnotami (case-insensitive)
            for i, item in enumerate(memory_data):
                if 'VALUE' in item and item['VALUE'] and item['VALUE'].lower() in lower_invalid_values:
                    product_key = item.get('KEY', '')

                    if fix_mode:
                        # V režimu oprav se ptáme na novou hodnotu pro každý klíč
                        print(f"\n{'=' * 80}")
                        print(f"OPRAVA NEPLATNÉ HODNOTY")
                        print(f"{'=' * 80}")
                        print(f"Klíč: {product_key}")
                        print(f"Neplatná hodnota: {item['VALUE']}")
                        new_value = input("Zadejte novou hodnotu (prázdný řádek = odstranit záznam): ")

                        if new_value:
                            # Uložíme novou hodnotu
                            items_to_fix[i] = new_value
                            logging.info(f"Nahrazuji neplatnou hodnotu '{item['VALUE']}' na '{new_value}' pro klíč '{product_key}' v souboru {filename}")
                        else:
                            # Pokud je nová hodnota prázdná, odstraníme záznam
                            items_to_remove.append(i)
                            logging.info(f"Označuji k odstranění záznam pro klíč '{product_key}' s neplatnou hodnotou '{item['VALUE']}' v souboru {filename}")
                    else:
                        # V režimu mazání jednoduše označíme záznam k odstranění
                        items_to_remove.append(i)
                        logging.info(f"Označuji k odstranění záznam pro klíč '{product_key}' s neplatnou hodnotou '{item['VALUE']}' v souboru {filename}")

            # Provedeme opravy hodnot
            for idx, new_value in sorted(items_to_fix.items(), reverse=True):
                memory_data[idx]['VALUE'] = new_value

            # Odstraníme označené záznamy
            for idx in sorted(items_to_remove, reverse=True):
                removed_item = memory_data.pop(idx)
                logging.info(f"Odstraněn záznam pro klíč '{removed_item.get('KEY', '')}' s neplatnou hodnotou '{removed_item.get('VALUE', '')}' v souboru {filename}")

            # Vypíšeme shrnutí změn
            removed_count = len(items_to_remove)
            fixed_count = len(items_to_fix)

            if fix_mode:
                logging.info(f"V souboru {filename} bylo opraveno {fixed_count} záznamů a odstraněno {removed_count} záznamů s neplatnými hodnotami")
            else:
                logging.info(f"V souboru {filename} bylo odstraněno {removed_count} záznamů s neplatnými hodnotami")

            # Uložíme změny do souboru
            if file_changes:
                save_memory_file(memory_data, memory_dir, filename, no_save)
                changes_made = True
        else:
            logging.info(f"Všechny hodnoty v souboru {filename} jsou platné")

    if changes_made:
        logging.info("Kontrola unikátních hodnot je dokončena, byly provedeny změny")
    else:
        logging.info("Kontrola unikátních hodnot je dokončena, nebyly provedeny žádné změny")

    return changes_made


def check_product_model_memory_against_pincesobchod(memory_dir: str, language: str, no_save: bool = False, fix_mode: bool = False) -> bool:
    """
    Kontroluje hodnoty v ProductModelMemory a odstraňuje ty, které nejsou obsaženy
    v žádném názvu produktu z Pincesobchod pro daný jazyk.

    Args:
        memory_dir: Adresář s paměťovými soubory
        language: Kód jazyka
        no_save: True pokud se nemají ukládat změny, False jinak
        fix_mode: True pro režim oprav, False pro režim mazání nevalidních hodnot

    Returns:
        True pokud byly provedeny změny, False jinak
    """
    import json
    from shared.file_ops import load_json_file
    from unifierlib.constants import SCRIPT_DIR, MEMORY_KEY_PRODUCT_MODEL_MEMORY

    if fix_mode:
        logging.info(f"Kontroluji ProductModelMemory_{language} proti názvům produktů z Pincesobchod_{language} - režim oprav...")
    else:
        logging.info(f"Kontroluji ProductModelMemory_{language} proti názvům produktů z Pincesobchod_{language} - režim mazání...")

    # Načtení ProductModelMemory
    model_memory_filename = f"{MEMORY_KEY_PRODUCT_MODEL_MEMORY.format(language=language)}.csv"
    model_memory = load_memory_file(memory_dir, model_memory_filename)

    if not model_memory:
        logging.warning(f"Soubor {model_memory_filename} je prázdný nebo neexistuje")
        return False

    # Cesta k souboru Pincesobchod - konzistentně s přístupem v unifier.py
    examples_dir = os.path.join(SCRIPT_DIR, "Examples")
    pincesobchod_file_path = os.path.join(examples_dir, f"pincesobchod_{language}.json")

    if not os.path.exists(pincesobchod_file_path):
        logging.error(f"Soubor pincesobchod_{language}.json nebyl nalezen na cestě: {pincesobchod_file_path}")
        return False

    # Načtení dat z Pincesobchod JSON souboru
    try:
        logging.debug(f"Načítám JSON soubor: {pincesobchod_file_path}")

        with open(pincesobchod_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        # Extrakce názvů produktů z Pincesobchod - použijeme přesně stejnou cestu jako v parseru.py
        product_names = []

        # Zpracování různých struktur JSON
        if isinstance(json_data, list):
            # Přímý seznam produktů
            product_list = json_data
        elif isinstance(json_data, dict):
            # Kontrola běžných klíčů obsahujících produkty
            if 'products' in json_data:
                product_list = json_data['products']
            elif 'items' in json_data:
                product_list = json_data['items']
            elif 'data' in json_data:
                product_list = json_data['data']
            else:
                # Předpokládáme, že slovník je sám o sobě produktem
                product_list = [json_data]
        else:
            logging.error(f"Neočekávaná struktura JSON souboru {pincesobchod_file_path}")
            return False

        # Extrakce názvů produktů pomocí přesné cesty z parseru.py: data['translations']['cs']['name']
        for product in product_list:
            if isinstance(product, dict):
                try:
                    # Použití přesné cesty pro extrakci názvu podle parser.py
                    if 'translations' in product and language.lower() in product['translations']:
                        product_name = product['translations'][language.lower()].get('name', '')
                        if product_name:
                            product_names.append(product_name)
                except (KeyError, TypeError) as e:
                    # Pokud přesná cesta selže, pokusíme se najít název v běžných polích
                    fallback_name = None
                    for field in ['name', 'title', 'productName']:
                        if field in product:
                            fallback_name = product[field]
                            break

                    if fallback_name:
                        product_names.append(fallback_name)
                        logging.debug(f"Použit fallback název produktu: '{fallback_name}', přesná cesta selhala: {str(e)}")

        # Pro jistotu odstraníme prázdné řetězce a None hodnoty
        product_names = [name for name in product_names if name]

    except Exception as e:
        logging.error(f"Chyba při načítání nebo zpracování souboru {pincesobchod_file_path}: {str(e)}")
        return False


    if not product_names:
        logging.error(f"Nepodařilo se extrahovat názvy produktů z Pincesobchod_{language}.json")
        return False

    logging.info(f"Načteno {len(product_names)} názvů produktů z Pincesobchod_{language}.json")

    # Sloučení všech názvů produktů do jednoho textu pro rychlejší vyhledávání
    all_product_names_text = ' '.join(product_names).lower()

    # Kontrola hodnot v ProductModelMemory
    models_to_remove = []
    models_to_fix = {}

    for i, item in enumerate(tqdm(model_memory, desc=f"Kontrola modelů proti Pincesobchod_{language}")):
        if 'VALUE' not in item or not item['VALUE']:
            continue

        model_value = item['VALUE']
        product_key = item.get('KEY', '')

        # Kontrola, zda se model vyskytuje v názvech produktů (case insensitive)
        if model_value.lower() not in all_product_names_text:
            if fix_mode:
                # Režim oprav - nabídneme možnost ruční opravy
                tqdm.write("\n\n")  # Přidáme prázdné řádky pro oddělení od progress baru
                tqdm.write("=" * 80)  # Výraznější oddělovač
                tqdm.write("MODEL NENÍ OBSAZEN V NÁZVECH PRODUKTŮ")
                tqdm.write("-" * 80)
                tqdm.write(f"Produkt: '{product_key}'")
                tqdm.write(f"Model: '{model_value}'")
                tqdm.write(f"Tento model se nevyskytuje v žádném názvu produktu z Pincesobchod_{language}.")
                tqdm.write("-" * 80)
                tqdm.write("Zadejte novou hodnotu modelu nebo stiskněte Enter pro odstranění záznamu:")
                new_value = input("> ")
                tqdm.write("=" * 80)
                tqdm.write("\n")  # Přidáme prázdný řádek pro oddělení od dalšího progress baru

                if new_value:
                    models_to_fix[i] = new_value
                    logging.info(f"Ručně opraven model '{model_value}' na '{new_value}' pro produkt '{product_key}'")
                else:
                    models_to_remove.append((i, product_key, model_value))
                    logging.info(f"Označen k odstranění model '{model_value}' pro produkt '{product_key}', který není obsažen v žádném názvu produktu")
            else:
                # Režim mazání - označíme k odstranění
                models_to_remove.append((i, product_key, model_value))
                logging.info(f"Označen k odstranění model '{model_value}' pro produkt '{product_key}', který není obsažen v žádném názvu produktu")

    changes_made = False

    # Aplikujeme opravy v režimu oprav
    if fix_mode and models_to_fix:
        for idx, new_value in sorted(models_to_fix.items(), key=lambda x: x[0]):
            model_memory[idx]['VALUE'] = new_value

        changes_made = True
        logging.info(f"Opraveno {len(models_to_fix)} modelů, které nebyly obsaženy v názvech produktů")

    # Odstranění hodnot, které nejsou v názvech produktů
    if models_to_remove:
        # Seřadíme indexy sestupně, abychom mohli bezpečně odstraňovat položky
        for index, product_key, model_value in sorted(models_to_remove, key=lambda x: x[0], reverse=True):
            model_memory.pop(index)
            logging.info(f"Odstraněn model '{model_value}' pro produkt '{product_key}', který není obsažen v žádném názvu produktu z Pincesobchod_{language}")

        changes_made = True
        logging.info(f"Celkem odstraněno {len(models_to_remove)} modelů, které nejsou obsaženy v názvech produktů z Pincesobchod_{language}")

    # Uložení upraveného souboru
    if changes_made:
        save_memory_file(model_memory, memory_dir, model_memory_filename, no_save)
        return True
    else:
        logging.info(f"Všechny modely v ProductModelMemory_{language} jsou obsaženy v názvech produktů z Pincesobchod_{language}")
        return False


def check_invalid_value_format(memory_dir: str, language: str, no_save: bool = False, fix_mode: bool = False) -> bool:
    """
    Kontroluje a opravuje nevhodné formátování hodnot ve všech paměťových souborech:
    - Hodnoty obsahující více než 3 velká písmena po sobě
    - Hodnoty začínající malým písmenem po odstranění bílých znaků

    Pokud fix_mode=True, provádí opravy (konverze na správný formát),
    jinak maže záznamy s nesprávným formátem.

    Args:
        memory_dir: Adresář s paměťovými soubory
        language: Kód jazyka
        no_save: True pokud se nemají ukládat změny, False jinak
        fix_mode: True pro režim oprav, False pro režim mazání vadných záznamů

    Returns:
        True pokud byly provedeny změny, False jinak
    """
    if fix_mode:
        logging.info("Kontroluji a opravuji nevhodné formátování hodnot ve vybraných paměťových souborech...")
    else:
        logging.info("Kontroluji a odstraňuji záznamy s nevhodným formátováním hodnot...")

    # Seznam paměťových souborů k kontrole - pouze ty, které procházejí i jinou kontrolou
    memory_file_keys = [
        MEMORY_KEY_PRODUCT_TYPE_MEMORY,
        MEMORY_KEY_PRODUCT_MODEL_MEMORY,
        MEMORY_KEY_PRODUCT_BRAND_MEMORY,
        MEMORY_KEY_VARIANT_NAME_MEMORY,
        MEMORY_KEY_VARIANT_VALUE_MEMORY,
        MEMORY_KEY_CATEGORY_MEMORY
    ]

    # Formátujeme názvy souborů s příslušným jazykem
    memory_files = [key_template.format(language=language) + ".csv" for key_template in memory_file_keys]

    changes_made = False
    total_fixed = 0
    total_removed = 0

    # Pro každý paměťový soubor provedeme kontrolu a opravy
    for filename in tqdm(memory_files, desc="Kontrola formátu hodnot v souborech"):
        memory_data = load_memory_file(memory_dir, filename)

        if not memory_data:
            logging.debug(f"Soubor {filename} je prázdný nebo neexistuje, přeskakuji.")
            continue

        file_changes = False
        items_to_remove = []
        items_to_fix = {}
        file_fixed = 0
        file_removed = 0

        # Kontrola všech hodnot v souboru
        for i, item in enumerate(memory_data):
            if 'VALUE' not in item or not item['VALUE']:
                continue

            # Odstranění bílých znaků z obou konců
            original_value = item['VALUE']
            stripped_value = original_value.strip()

            if not stripped_value:
                continue

            # Detekce problému 1: Hodnota obsahuje více než 3 velká písmena po sobě
            has_uppercase_sequence = bool(re.search(r'[A-Z]{4,}', stripped_value))

            # Detekce problému 2: Hodnota začíná malým písmenem
            starts_with_lowercase = stripped_value[0].islower()

            # Pokud existuje alespoň jeden problém
            if has_uppercase_sequence or starts_with_lowercase:
                product_key = item.get('KEY', '')

                # Informativní výpisy pro diagnostiku
                if has_uppercase_sequence:
                    uppercase_sequences = re.findall(r'[A-Z]{4,}', stripped_value)
                    logging.info(f"V souboru {filename}: Hodnota '{stripped_value}' pro klíč '{product_key}' obsahuje sekvenci více než 3 velkých písmen: {uppercase_sequences}")

                if starts_with_lowercase:
                    logging.info(f"V souboru {filename}: Hodnota '{stripped_value}' pro klíč '{product_key}' začíná malým písmenem.")

                # Rozhodnutí o akci na základě režimu
                if fix_mode:
                    # Režim oprav - upravíme hodnotu
                    modified_value = stripped_value

                    # Oprava problému 1: Konvertujeme dlouhé sekvence velkých písmen
                    if has_uppercase_sequence:
                        # Najdeme všechny sekvence 4+ velkých písmen a převedeme je na první velké, zbytek malé
                        def capitalize_match(match):
                            s = match.group(0)
                            return s[0].upper() + s[1:].lower()

                        modified_value = re.sub(r'[A-Z]{4,}', capitalize_match, modified_value)

                    # Oprava problému 2: První písmeno na velké
                    if starts_with_lowercase and modified_value:
                        modified_value = modified_value[0].upper() + modified_value[1:]

                    # Pokud se hodnota změnila, zaznamenáme opravu
                    if modified_value != original_value:
                        items_to_fix[i] = modified_value
                        logging.info(f"V souboru {filename}: Opravuji formát hodnoty z '{original_value}' na '{modified_value}' pro klíč '{product_key}'")
                        file_changes = True
                        file_fixed += 1
                else:
                    # Režim mazání - označíme položku k odstranění
                    items_to_remove.append(i)
                    logging.info(f"V souboru {filename}: Označuji k odstranění záznam pro klíč '{product_key}' s nevhodnou hodnotou '{original_value}'")
                    file_changes = True
                    file_removed += 1

        # Aplikujeme změny na soubor
        if fix_mode and items_to_fix:
            for idx, new_value in sorted(items_to_fix.items(), reverse=True):
                memory_data[idx]['VALUE'] = new_value

            logging.info(f"V souboru {filename} bylo opraveno {len(items_to_fix)} záznamů s nevhodným formátem")
            total_fixed += len(items_to_fix)

        if items_to_remove:
            # Odstraníme záznamy od konce, aby indexy zůstaly platné
            for idx in sorted(items_to_remove, reverse=True):
                removed_item = memory_data.pop(idx)
                logging.debug(f"V souboru {filename}: Odstraněn záznam s nevhodnou hodnotou '{removed_item.get('VALUE', '')}' pro klíč '{removed_item.get('KEY', '')}'")

            logging.info(f"V souboru {filename} bylo odstraněno {len(items_to_remove)} záznamů s nevhodným formátem")
            total_removed += len(items_to_remove)

        # Pokud byly provedeny změny, uložíme soubor
        if file_changes:
            save_memory_file(memory_data, memory_dir, filename, no_save)
            changes_made = True
            if fix_mode:
                logging.info(f"Soubor {filename}: opraveno {file_fixed} záznamů")
            else:
                logging.info(f"Soubor {filename}: odstraněno {file_removed} záznamů")
        else:
            logging.debug(f"V souboru {filename} nebyly nalezeny žádné hodnoty s nevhodným formátem")

    if changes_made:
        if fix_mode:
            logging.info(f"Celkově opraveno {total_fixed} záznamů s nevhodným formátem ve vybraných souborech")
        else:
            logging.info(f"Celkově odstraněno {total_removed} záznamů s nevhodným formátem ve vybraných souborech")
    else:
        logging.info("Kontrola formátu hodnot dokončena, nebyly nalezeny žádné hodnoty s nevhodným formátem")

    return changes_made


def main():
    """Hlavní funkce skriptu pro kontrolu paměťových souborů."""
    args = parse_arguments()

    # Nastavení logování
    setup_logging(debug=args.debug)

    logging.info(f"Spouštím kontrolu paměťových souborů pro jazyk: {args.language}")
    logging.info(f"Adresář s paměťovými soubory: {args.memory_dir}")
    logging.info(f"Ukládání změn: {'vypnuto' if args.no_save else 'zapnuto'}")
    logging.info(f"Režim: {'opravy' if args.fix else 'mazání vadných záznamů'}")

    # Seznam pro sledování, zda byly provedeny nějaké změny
    changes = []

    # Kontrola a oprava nevhodného formátování hodnot - přesunuto na první místo, aby ostatní funkce
    # pracovaly již s opravenými daty
    changes.append(check_invalid_value_format(args.memory_dir, args.language, args.no_save, args.fix))

    # 1. Kontrola a oprava ProductBrandMemory
    changes.append(check_and_fix_product_brand_memory(args.memory_dir, args.language, args.no_save, args.fix))

    # 2. Kontroluje, zda typy a modely neobsahují značky
    changes.append(check_type_model_contains_brand(args.memory_dir, args.language, args.no_save, args.fix))

    # 3. Kontroluje, zda typy a modely neobsahují variantní hodnoty
    changes.append(check_variant_in_type_model(args.memory_dir, args.language, args.no_save, args.fix))

    # 4. Kontrola překrývajících se hodnot mezi typy a modely
    # (až po odstranění značek a variant, abychom pracovali s očištěnými daty)
    changes.append(check_type_model_overlap(args.memory_dir, args.language, args.no_save, args.fix))

    # 5. Kontrola formátu klíčových slov
    changes.append(check_keywords_format(args.memory_dir, args.language, args.no_save, args.fix))

    # 6. Kontrola ProductModelMemory proti názvům produktů z Pincesobchod
    changes.append(check_product_model_memory_against_pincesobchod(args.memory_dir, args.language, args.no_save, args.fix))

    # 7. Aktualizace NameMemory na základě opravených hodnot
    changes.append(update_name_memory(args.memory_dir, args.language, args.no_save))

    # 8. Kontrola unikátních hodnot ve všech paměťových souborech
    changes.append(check_unique_values(args.memory_dir, args.language, args.no_save, args.fix))

    # 9. Znovu kontrola formátování - pro jistotu zkontrolujeme po všech ostatních úpravách
    changes.append(check_invalid_value_format(args.memory_dir, args.language, args.no_save, args.fix))


    # Zjistíme, zda byly provedeny nějaké změny celkově
    any_changes = any(changes)

    if any_changes and not args.no_save:
        logging.info("Všechny změny byly uloženy")
    elif any_changes and args.no_save:
        logging.info("Byly nalezeny potřebné změny, ale nebyly uloženy (--no-save)")
    else:
        logging.info("Žádné změny nebyly potřeba, všechny soubory jsou v pořádku")

    return 0 if not any_changes else 1


if __name__ == "__main__":
    sys.exit(main())
