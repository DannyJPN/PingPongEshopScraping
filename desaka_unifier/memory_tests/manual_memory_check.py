#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manuální kontrola a čištění memory souborů

Načte memory soubor obráceně (seskupeno podle VALUE) a umožní:
- Kontrolu, že všechny KEYs patří k dané VALUE
- Detekci podobných/duplicitních VALUES
- Vyřazení nesprávných KEYs z memory souboru
"""

import argparse
import os
import sys
from pathlib import Path
from collections import defaultdict
from difflib import SequenceMatcher
from tqdm import tqdm

# Import existing file operations
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.file_ops import load_csv_file, save_csv_file

# Mapování aliasů na jména souborů
FILE_ALIASES = {
    'brand': 'ProductBrandMemory',
    'model': 'ProductModelMemory',
    'type': 'ProductTypeMemory',
    'category': 'CategoryMemory',
    'categoryname': 'CategoryNameMemory',
    'variantname': 'VariantNameMemory',
    'variantvalue': 'VariantValueMemory',
    'stockstatus': 'StockStatusMemory',
    'name': 'NameMemory',
    'desc': 'DescMemory',
    'shortdesc': 'ShortDescMemory',
}

# Velikost stránky pro zobrazení KEYs
PAGE_SIZE = 40


def get_memory_filepath(alias: str, language: str) -> Path:
    """
    Převede alias na plnou cestu k memory souboru.

    Args:
        alias: Alias souboru (např. 'brand', 'model')
        language: Jazykový kód (CS, SK)

    Returns:
        Path k memory souboru
    """
    if alias.lower() not in FILE_ALIASES:
        raise ValueError(f"Neznámý alias '{alias}'. Dostupné aliasy: {', '.join(FILE_ALIASES.keys())}")

    filename = f"{FILE_ALIASES[alias.lower()]}_{language.upper()}.csv"
    filepath = Path(__file__).parent.parent / 'Memory' / filename

    if not filepath.exists():
        raise FileNotFoundError(f"Soubor nenalezen: {filepath}")

    return filepath


def load_memory_file(filepath: Path) -> dict:
    """
    Načte memory soubor a vrátí slovník KEY→VALUE.

    Uses existing load_csv_file from shared.file_ops.

    Args:
        filepath: Cesta k memory souboru

    Returns:
        Slovník {KEY: VALUE}
    """
    # Use shared file operations
    csv_data = load_csv_file(str(filepath))

    # Convert list of dicts to KEY→VALUE dict
    data = {}
    for row in csv_data:
        data[row['KEY']] = row['VALUE']

    return data


def invert_memory_data(data: dict) -> dict:
    """
    Invertuje memory data: VALUE → list of KEYs.

    Args:
        data: Slovník {KEY: VALUE}

    Returns:
        Slovník {VALUE: [KEY1, KEY2, ...]} - KEYs jsou seřazeny abecedně
    """
    inverted = defaultdict(list)
    for key, value in data.items():
        inverted[value].append(key)

    # Seřadit KEYs pro každou VALUE abecedně (case-insensitive)
    for value in inverted:
        inverted[value].sort(key=lambda x: x.lower())

    return dict(inverted)


def normalize_value(value: str) -> str:
    """
    Normalizuje VALUE pro detekci podobností.

    Args:
        value: Původní VALUE

    Returns:
        Normalizovaný VALUE (lowercase, bez extra mezer)
    """
    return ' '.join(value.lower().split())


def find_similar_values(values: list, threshold: float = 0.85) -> list:
    """
    Najde podobné VALUES pomocí fuzzy matchingu.

    Args:
        values: Seznam VALUES
        threshold: Práh podobnosti (0.0-1.0)

    Returns:
        Seznam skupin podobných VALUES
    """
    similar_groups = []
    processed = set()

    # Progress bar pro vnější smyčku
    with tqdm(total=len(values), desc="Hledání podobných VALUES", unit="value") as pbar:
        for i, val1 in enumerate(values):
            if val1 in processed:
                pbar.update(1)
                continue

            group = [val1]
            norm1 = normalize_value(val1)

            # Vnitřní smyčka bez progress baru (byla by příliš mnoho aktualizací)
            for val2 in values[i+1:]:
                if val2 in processed:
                    continue

                norm2 = normalize_value(val2)
                similarity = SequenceMatcher(None, norm1, norm2).ratio()

                if similarity >= threshold:
                    group.append(val2)
                    processed.add(val2)

            if len(group) > 1:
                similar_groups.append(group)

            processed.add(val1)
            pbar.update(1)

    return similar_groups


def find_similar_keys(deleted_keys: list, all_keys: list, threshold: float = 0.85) -> dict:
    """
    Najde podobné KEYs k mazaným KEYs pomocí fuzzy matchingu.

    Args:
        deleted_keys: Seznam mazaných KEYs
        all_keys: Seznam všech zbývajících KEYs v memory
        threshold: Práh podobnosti (0.0-1.0)

    Returns:
        Slovník {deleted_key: [similar_keys]}
    """
    similar_map = {}

    # Progress bar pro mazané klíče
    with tqdm(total=len(deleted_keys), desc="Hledání podobných KEYs", unit="key") as pbar:
        for deleted_key in deleted_keys:
            norm_deleted = normalize_value(deleted_key)
            similar_keys = []

            # Hledat podobné klíče mezi všemi zbývajícími
            for key in all_keys:
                norm_key = normalize_value(key)
                similarity = SequenceMatcher(None, norm_deleted, norm_key).ratio()

                if similarity >= threshold:
                    similar_keys.append(key)

            if similar_keys:
                # Seřadit podobné klíče abecedně
                similar_keys.sort(key=lambda x: x.lower())
                similar_map[deleted_key] = similar_keys

            pbar.update(1)

    return similar_map


def display_value_group(value: str, keys: list, index: int, total: int) -> int:
    """
    Zobrazí skupinu KEYs pro danou VALUE s optimalizací pro velké skupiny.

    Args:
        value: VALUE
        keys: Seznam KEYs
        index: Index aktuální VALUE
        total: Celkový počet VALUES

    Returns:
        Počáteční číslo stránky (1 pro malé skupiny, 1 pro první stránku velkých skupin)
    """
    print("\n" + "=" * 80)
    print(f"VALUE [{index}/{total}]: '{value}'")
    print(f"Počet KEYs: {len(keys)}")
    print("=" * 80)

    # Pro velké skupiny zobrazit první stránku
    if len(keys) <= 30:
        # Malá skupina - zobrazit vše
        for i, key in enumerate(keys, 1):
            print(f"  {i:4d}. {key}")
        return 1  # Single page
    else:
        # Velká skupina - zobrazit první stránku
        total_pages = (len(keys) + PAGE_SIZE - 1) // PAGE_SIZE

        print(f"\n⚠️  Velká skupina ({len(keys)} KEYs, {total_pages} stránek)")
        print("\n--- Stránka 1/{} (KEYs 1-{} z {}) ---".format(
            total_pages, min(PAGE_SIZE, len(keys)), len(keys)
        ))

        for i in range(min(PAGE_SIZE, len(keys))):
            print(f"  {i+1:4d}. {keys[i]}")

        print("\n" + "-" * 80)
        print("💡 Navigace a příkazy:")
        print("   'next' / 'n'      - Další stránka")
        print("   'prev' / 'p'      - Předchozí stránka")
        print("   'show page N'     - Přejít na stránku N")
        print("   'first' / 'last'  - První/poslední stránka")
        print("   'show all'        - Zobrazit všechny KEYs")
        print("   'search TEXT'     - Vyhledat KEYs obsahující TEXT")
        print("   'pattern TEXT'    - Označit všechny KEYs obsahující TEXT k vymazání")
        print("   'stats'           - Zobrazit statistiky a podobnosti")
        print("-" * 80)

        return 1  # Start at page 1


def show_keys_page(keys: list, page: int, marked_for_removal: set = None, page_size: int = PAGE_SIZE):
    """
    Zobrazí stránku KEYs s označením vybraných k vymazání.

    Args:
        keys: Seznam všech KEYs
        page: Číslo stránky (1-based)
        marked_for_removal: Set indexů označených k vymazání
        page_size: Počet KEYs na stránku (default: PAGE_SIZE)
    """
    start = (page - 1) * page_size
    end = min(start + page_size, len(keys))
    total_pages = (len(keys) + page_size - 1) // page_size

    if page < 1 or page > total_pages:
        print(f"❌ Stránka {page} neexistuje (celkem {total_pages} stránek)")
        return False

    if marked_for_removal is None:
        marked_for_removal = set()

    print(f"\n--- Stránka {page}/{total_pages} (KEYs {start+1}-{end} z {len(keys)}) ---")
    for i in range(start, end):
        mark = "✗" if i in marked_for_removal else " "
        print(f" {mark} {i+1:4d}. {keys[i]}")

    return True


def search_keys(keys: list, search_text: str):
    """Vyhledá a zobrazí KEYs obsahující hledaný text."""
    search_lower = search_text.lower()
    matches = [(i, key) for i, key in enumerate(keys) if search_lower in key.lower()]

    if not matches:
        print(f"❌ Žádné KEYs neobsahují '{search_text}'")
        return

    print(f"\n✓ Nalezeno {len(matches)} KEYs obsahujících '{search_text}':")
    for i, (idx, key) in enumerate(matches[:PAGE_SIZE], 1):  # Show max PAGE_SIZE
        print(f"  {idx+1:4d}. {key}")

    if len(matches) > PAGE_SIZE:
        print(f"\n  ... a dalších {len(matches) - PAGE_SIZE} KEYs")


def show_stats(keys: list):
    """Zobrazí statistiky o KEYs."""
    print(f"\n📊 STATISTIKY")
    print(f"{'=' * 80}")
    print(f"Celkový počet KEYs: {len(keys)}")

    # Analyze common patterns
    words = []
    for key in keys:
        words.extend(key.split())

    from collections import Counter
    word_counts = Counter(words)

    print(f"\nNejčastější slova v KEYs:")
    for word, count in word_counts.most_common(10):
        if len(word) > 3:  # Skip short words
            pct = (count / len(keys)) * 100
            print(f"  '{word}': {count}x ({pct:.1f}%)")


def get_keys_to_remove(keys: list, initial_page: int = 1) -> list:
    """
    Interaktivně získá seznam KEYs k vymazání.

    Podporuje rozšířené příkazy pro velké skupiny a postupné procházení stránkami.

    Args:
        keys: Seznam všech KEYs
        initial_page: Počáteční stránka (1-based)

    Returns:
        Seznam indexů KEYs k vymazání nebo None (quit)
    """
    total_pages = (len(keys) + PAGE_SIZE - 1) // PAGE_SIZE
    current_page = initial_page
    marked_for_removal = set()

    print("\n" + "-" * 80)
    print("Příkazy:")
    print("  [číslo]         - Označit KEY k vymazání (např. '3' nebo '1,5,7' nebo '1-5')")
    print("  'all'           - Vymazat všechny KEYs (celou VALUE)")
    print("  'none' / Enter  - Ponechat všechny KEYs (VALUE je OK)")
    print("\nNavigace (pro velké skupiny):")
    print("  'next' / 'n'    - Další stránka")
    print("  'prev' / 'p'    - Předchozí stránka")
    print("  'show page N'   - Přejít na stránku N")
    print("  'first' / 'last' - První/poslední stránka")
    print("\nRozšířené příkazy:")
    print("  'show all'      - Zobrazit všechny KEYs")
    print("  'search TEXT'   - Vyhledat KEYs obsahující TEXT")
    print("  'pattern TEXT'  - Označit všechny KEYs obsahující TEXT k vymazání")
    print("  'stats'         - Zobrazit statistiky")
    print("  'q'             - Ukončit kontrolu")
    print("-" * 80)

    while True:
        if marked_for_removal:
            print(f"\n[Označeno {len(marked_for_removal)} KEYs k vymazání]")

        if len(keys) > 30 and total_pages > 1:
            print(f"[Aktuální stránka: {current_page}/{total_pages}]")

        response = input("\nZadejte příkaz: ").strip()

        if response.lower() == 'q':
            return None  # Signal to quit

        if response.lower() in ['none', '']:
            return list(marked_for_removal)

        if response.lower() == 'all':
            return list(range(len(keys)))

        # Navigation commands
        if response.lower() in ['next', 'n']:
            if current_page < total_pages:
                current_page += 1
                show_keys_page(keys, current_page, marked_for_removal)
            else:
                print(f"❌ Již jste na poslední stránce ({total_pages})")
            continue

        if response.lower() in ['prev', 'p']:
            if current_page > 1:
                current_page -= 1
                show_keys_page(keys, current_page, marked_for_removal)
            else:
                print("❌ Již jste na první stránce")
            continue

        if response.lower() == 'first':
            current_page = 1
            show_keys_page(keys, current_page, marked_for_removal)
            continue

        if response.lower() == 'last':
            current_page = total_pages
            show_keys_page(keys, current_page, marked_for_removal)
            continue

        # Show all
        if response.lower() == 'show all':
            print(f"\n--- Všechny KEYs ({len(keys)}) ---")
            for i, key in enumerate(keys, 1):
                mark = "✗" if (i-1) in marked_for_removal else " "
                print(f" {mark} {i:4d}. {key}")
            continue

        # Show page
        if response.lower().startswith('show page '):
            try:
                page = int(response.split()[-1])
                if show_keys_page(keys, page, marked_for_removal):
                    current_page = page
            except ValueError:
                print("❌ Chyba: Použijte 'show page N' kde N je číslo stránky")
            continue

        # Search
        if response.lower().startswith('search '):
            search_text = response[7:].strip()
            if search_text:
                search_keys(keys, search_text)
            else:
                print("❌ Chyba: Použijte 'search TEXT'")
            continue

        # Pattern removal
        if response.lower().startswith('pattern '):
            pattern_text = response[8:].strip()
            if pattern_text:
                pattern_lower = pattern_text.lower()
                matches = [i for i, key in enumerate(keys) if pattern_lower in key.lower()]
                if matches:
                    marked_for_removal.update(matches)
                    print(f"✓ Označeno {len(matches)} KEYs obsahujících '{pattern_text}'")
                else:
                    print(f"❌ Žádné KEYs neobsahují '{pattern_text}'")
            else:
                print("❌ Chyba: Použijte 'pattern TEXT'")
            continue

        # Stats
        if response.lower() == 'stats':
            show_stats(keys)
            continue

        # Parse numbers
        try:
            indices = []
            parts = response.split(',')
            for part in parts:
                part = part.strip()
                if '-' in part:
                    # Range: "1-5"
                    start, end = map(int, part.split('-'))
                    indices.extend(range(start - 1, end))
                else:
                    # Single number
                    indices.append(int(part) - 1)

            # Validate indices
            if all(0 <= i < len(keys) for i in indices):
                marked_for_removal.update(indices)
                print(f"✓ Přidáno {len(indices)} KEYs k označeným")
            else:
                print(f"❌ Chyba: Některé číslo je mimo rozsah 1-{len(keys)}")

        except ValueError:
            print("❌ Neplatný příkaz. Zadejte čísla KEYs nebo příkaz (např. 'next', 'search', 'none')")


def save_memory_file(filepath: Path, data: dict):
    """
    Uloží vyčištěný memory soubor.

    Uses existing save_csv_file from shared.file_ops (with automatic backup).

    Args:
        filepath: Cesta k memory souboru
        data: Slovník {KEY: VALUE}
    """
    # Convert dict to list of dicts for save_csv_file
    csv_data = [{'KEY': key, 'VALUE': value} for key, value in sorted(data.items())]

    # Use shared file operations (creates backup automatically)
    save_csv_file(csv_data, str(filepath))

    print(f"✓ Soubor uložen: {filepath.name}")
    print(f"✓ Záloha vytvořena automaticky")


def main():
    """Hlavní funkce."""
    parser = argparse.ArgumentParser(
        description='Manuální kontrola a čištění memory souborů',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Příklady použití:
  python manual_memory_check.py --file brand
  python manual_memory_check.py --file model --language SK
  python manual_memory_check.py -f type

Dostupné aliasy souborů:
  brand, model, type, category, categoryname, variantname, variantvalue,
  stockstatus, name, desc, shortdesc
        """
    )

    parser.add_argument('-f', '--file', required=True,
                       help='Alias memory souboru (např. brand, model, type)')
    parser.add_argument('-l', '--language', default='CS',
                       help='Jazyk (CS nebo SK, default: CS)')
    parser.add_argument('--threshold', type=float, default=0.85,
                       help='Práh podobnosti pro detekci duplicit (0.0-1.0, default: 0.85)')

    args = parser.parse_args()

    try:
        # Load memory file
        filepath = get_memory_filepath(args.file, args.language)
        print(f"\n📂 Načítám: {filepath.name}")

        original_data = load_memory_file(filepath)
        print(f"✓ Načteno {len(original_data)} záznamů")

        # Invert data
        inverted_data = invert_memory_data(original_data)
        print(f"✓ Seskupeno do {len(inverted_data)} jedinečných VALUES")

        # Find similar values
        print(f"\n🔍 Hledání podobných VALUES (práh podobnosti: {args.threshold})...")
        similar_groups = find_similar_values(list(inverted_data.keys()), args.threshold)
        print()  # Blank line after progress bar

        if similar_groups:
            print(f"\n⚠️  Nalezeno {len(similar_groups)} skupin podobných VALUES:")
            for i, group in enumerate(similar_groups, 1):
                print(f"\n  Skupina {i}:")
                for val in group:
                    print(f"    - '{val}' ({len(inverted_data[val])} KEYs)")
        else:
            print("✓ Žádné podobné VALUES nenalezeny")

        # Interactive review
        print("\n" + "=" * 80)
        print("INTERAKTIVNÍ KONTROLA")
        print("=" * 80)
        print("\nProcházejte VALUES a označte KEYs, které nepatří k dané VALUE.")

        total_deleted = 0
        # Seřadit VALUES abecedně (case-insensitive)
        values_list = sorted(inverted_data.items(), key=lambda x: x[0].lower())

        for index, (value, keys) in enumerate(values_list, 1):
            initial_page = display_value_group(value, keys, index, len(values_list))

            indices = get_keys_to_remove(keys, initial_page)

            if indices is None:
                # Quit requested
                print("\n⚠️  Kontrola ukončena uživatelem")
                print(f"Celkem smazáno: {total_deleted} KEYs")
                break

            if indices:
                # Show what will be deleted
                print(f"\n{'=' * 80}")
                print(f"Označeno {len(indices)} KEYs k vymazání pro VALUE: '{value}'")

                # Ask for confirmation
                confirm = input("💾 Potvrdit a smazat? (y/n, default: y): ").strip().lower()

                if confirm in ['y', '']:
                    # Delete marked keys immediately
                    keys_to_remove = [keys[i] for i in indices]
                    for key in keys_to_remove:
                        del original_data[key]

                    # Save file immediately
                    save_memory_file(filepath, original_data)
                    total_deleted += len(keys_to_remove)
                    print(f"✅ Smazáno {len(keys_to_remove)} KEYs (celkem: {total_deleted})")

                    # Heuristic check for similar keys within the same VALUE
                    print(f"\n🔍 Hledání podobných KEYs k mazaným klíčům v rámci VALUE '{value}' (práh: {args.threshold})...")
                    # Only search among remaining keys in the SAME VALUE
                    remaining_keys_in_value = [k for i, k in enumerate(keys) if i not in indices]
                    similar_map = find_similar_keys(keys_to_remove, remaining_keys_in_value, args.threshold)
                    print()  # Blank line after progress bar

                    if similar_map:
                        print(f"\n⚠️  Nalezeno {len(similar_map)} mazaných KEYs s podobnými klíči:")

                        # Pro každý mazaný klíč zobrazit podobné klíče
                        for deleted_key, similar_keys in similar_map.items():
                            print(f"\n{'=' * 80}")
                            print(f"Mazaný KEY: '{deleted_key}'")
                            print(f"Podobné KEYs z téže VALUE ({len(similar_keys)}):")
                            for i, sim_key in enumerate(similar_keys, 1):
                                print(f"  {i:4d}. {sim_key}")

                            # Zeptat se na smazání podobných klíčů
                            confirm_similar = input("\n💾 Smazat i tyto podobné KEYs? (y/n, default: y): ").strip().lower()

                            if confirm_similar in ['y', '']:
                                # Smazat podobné klíče
                                for sim_key in similar_keys:
                                    if sim_key in original_data:
                                        del original_data[sim_key]

                                # Uložit soubor
                                save_memory_file(filepath, original_data)
                                total_deleted += len(similar_keys)
                                print(f"✅ Smazáno {len(similar_keys)} podobných KEYs (celkem: {total_deleted})")

                                # Aktualizovat seznam zbývajících klíčů pro další mazané klíče
                                remaining_keys_in_value = [k for k in remaining_keys_in_value if k not in similar_keys]
                            else:
                                print("❌ Smazání podobných KEYs zrušeno")
                    else:
                        print("✓ Žádné podobné KEYs nenalezeny v rámci této VALUE")
                else:
                    print("❌ Smazání zrušeno pro tuto VALUE")
            else:
                print("✓ Žádné KEYs ke smazání pro tuto VALUE")

        print(f"\n{'=' * 80}")
        print(f"KONTROLA DOKONČENA")
        print(f"{'=' * 80}")
        print(f"Celkem smazáno KEYs: {total_deleted}")
        print(f"Aktuální počet záznamů: {len(original_data)}")
        print(f"{'=' * 80}")

    except Exception as e:
        print(f"\n❌ Chyba: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
