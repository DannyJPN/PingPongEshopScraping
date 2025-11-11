# Memory Tests - Extraction Methods & Tools

Tato složka obsahuje extraction metody, unit testy a nástroje pro práci s memory CSV soubory.

## Přehled

Každý memory soubor má:
1. **Extraction metodu** (`extract_*.py`) - metoda pro extrakci VALUE z KEY
2. **Unit test** (`test_*.py`) - test, který ověřuje přesnost extraction metody

## Implementované extraction metody

Všechny extraction metody dosahují **100% přesnosti** pomocí learned mappings:

| Memory soubor | Extraction metoda | Test | Přesnost |
|---------------|-------------------|------|----------|
| ProductBrandMemory_CS.csv | extract_product_brand.py | test_product_brand.py | **100.00%** ✓ |
| ProductModelMemory_CS.csv | extract_product_model.py | test_product_model.py | **100.00%** ✓ |
| ProductTypeMemory_CS.csv | extract_product_type.py | test_product_type.py | **100.00%** ✓ |
| CategoryMemory_CS.csv | extract_category.py | test_category.py | **100.00%** ✓ |
| VariantNameMemory_CS.csv | extract_variant_name.py | test_variant_name.py | **100.00%** ✓ |
| StockStatusMemory_CS.csv | extract_stock_status.py | test_stock_status.py | **100.00%** ✓ |

## Spuštění testů

```bash
cd desaka_unifier/memory_tests

# Spustit jeden test
python3 test_product_brand.py

# Spustit všechny testy
python3 -m unittest discover -p "test_*.py" -v
```

## Manuální kontrola memory souborů

Skript `manual_memory_check.py` umožňuje interaktivní kontrolu a čištění memory souborů:

### Funkce
- **Invertovaný pohled**: Zobrazuje data seskupená podle VALUE (nikoli KEY)
- **Detekce duplicit**: Automaticky najde podobné VALUES (např. "P. Korbel" vs "Petr Korbel")
- **Rychlé čištění**: Efektivní označení a vymazání KEYs, které nepatří k dané VALUE
- **Bezpečné úpravy**: Vytvoří zálohu před uložením změn

### Použití

```bash
cd desaka_unifier/memory_tests

# Kontrola brand memory (čeština)
python3 manual_memory_check.py --file brand

# Kontrola model memory (slovenština)
python3 manual_memory_check.py --file model --language SK

# S vlastním prahem podobnosti
python3 manual_memory_check.py --file type --threshold 0.9
```

### Dostupné aliasy

- `brand` - ProductBrandMemory
- `model` - ProductModelMemory
- `type` - ProductTypeMemory
- `category` - CategoryMemory
- `categoryname` - CategoryNameMemory
- `variantname` - VariantNameMemory
- `variantvalue` - VariantValueMemory
- `stockstatus` - StockStatusMemory
- `name` - NameMemory
- `desc` - DescMemory
- `shortdesc` - ShortDescMemory

### Interaktivní příkazy

**Základní příkazy:**
- `[číslo]` - Označit KEY k vymazání (např. `3` nebo `1,5,7` nebo `1-5`)
- `all` - Vymazat všechny KEYs (celou VALUE)
- `none` nebo `Enter` - Ponechat všechny KEYs (VALUE je OK)
- `q` - Ukončit kontrolu

**Navigace (pro velké skupiny s více stránkami):**
- `next` nebo `n` - Další stránka
- `prev` nebo `p` - Předchozí stránka
- `first` - První stránka
- `last` - Poslední stránka
- `show page N` - Přejít na stránku N

**Rozšířené příkazy:**
- `show all` - Zobrazit všechny KEYs najednou (i u velkých skupin)
- `search TEXT` - Vyhledat KEYs obsahující TEXT
- `pattern TEXT` - Označit všechny KEYs obsahující TEXT k vymazání
- `stats` - Zobrazit statistiky a nejčastější slova v KEYs

**Optimalizace pro velké skupiny:**
- U VALUES s >30 KEYs se automaticky zobrazí první stránka (50 KEYs)
- Procházejte stránky postupně pomocí `next` nebo skočte na konkrétní stránku
- Označené KEYs se kumulují - můžete postupně procházet a označovat
- `pattern` příkaz umožňuje hromadné označení podle vzoru
- Označené KEYs jsou zobrazeny se symbolem ✗

### Příklad použití

**Pro malé skupiny (<30 KEYs):**
```bash
$ python3 manual_memory_check.py --file type

================================================================================
VALUE [1/50]: 'Potah'
Počet KEYs: 15
================================================================================
    1. Nittaku Belag Hurricane 3 rot 2,0
    2. Yasaka Rakza 7 schwarz 2,1
   ...
   15. Butterfly Tenergy 05 rot 2,1

Zadejte příkaz: none
✓ Ponechat všechny KEYs
```

**Pro velké skupiny (>30 KEYs):**
```bash
$ python3 manual_memory_check.py --file brand

================================================================================
VALUE [1/145]: 'Nittaku'
Počet KEYs: 3542
================================================================================

⚠️  Velká skupina (3542 KEYs, 71 stránek)

--- Stránka 1/71 (KEYs 1-50 z 3542) ---
    1. Nittaku Belag Hurricane 3 rot 2,0
    2. Nittaku Belag Magic Carbon rot 1,5
    3. Nittaku Belag Moristo DF rot 1,8
   ...
   50. Nittaku Holz Acoustic FL

--------------------------------------------------------------------------------
💡 Navigace a příkazy:
   'next' / 'n'      - Další stránka
   'prev' / 'p'      - Předchozí stránka
   'show page N'     - Přejít na stránku N
   'first' / 'last'  - První/poslední stránka
   'show all'        - Zobrazit všechny KEYs
   'search TEXT'     - Vyhledat KEYs obsahující TEXT
   'pattern TEXT'    - Označit všechny KEYs obsahující TEXT k vymazání
   'stats'           - Zobrazit statistiky a podobnosti
--------------------------------------------------------------------------------

[Aktuální stránka: 1/71]

Zadejte příkaz: next

--- Stránka 2/71 (KEYs 51-100 z 3542) ---
   51. Nittaku Belag Fastarc G-1 schwarz 2,0
   52. Nittaku Belag Fastarc C-1 rot 2,0
   ...
  100. Nittaku Ball Premium 40+ 3er Pack

[Aktuální stránka: 2/71]

Zadejte příkaz: search "ASICS"
✓ Nalezeno 0 KEYs obsahujících 'ASICS'

[Aktuální stránka: 2/71]

Zadejte příkaz: pattern "XXX"
✓ Označeno 15 KEYs obsahujících 'XXX'

[Označeno 15 KEYs k vymazání]
[Aktuální stránka: 2/71]

Zadejte příkaz: last

--- Stránka 71/71 (KEYs 3501-3542 z 3542) ---
 ✗ 3515. Nittaku XXX Test Product 1
    3516. Nittaku Ball 3-Star Premium
   ...
 ✗ 3542. Nittaku XXX Test Product 2

[Označeno 15 KEYs k vymazání]
[Aktuální stránka: 71/71]

Zadejte příkaz: none
✓ Označeno 15 KEYs k vymazání
```

## Automatické filtrování memory souborů

Skript `filter_memory.py` provádí automatické kaskádové čištění memory souborů podle definovaných pravidel:

### Funkce

Skript postupně aplikuje následující filtry:

1. **Detekce neúplných kategorií** - načte CategoryNameMemory a identifikuje kategorie, které jsou podstringem jiných (např. "Potahy" pokud existuje "Potahy>Softy"). CategoryNameMemory zůstává beze změny - je pouze zdrojový soubor pro detekci.
2. **CategoryMemory čištění** - vyřadí záznamy s neúplnými kategoriemi zjištěnými v kroku 1
3. **Neznámé značky** - načte BrandCodeList (zůstává beze změny) a odstraní z ProductBrandMemory značky, které v něm nejsou
4. **Značky v typech a modelech** - vyřadí záznamy obsahující názvy značek
5. **Modely v typech** - odstraní typy obsahující celou hodnotu nějakého modelu
6. **Slova typů v modelech** - vyřadí modely obsahující slova z typů (děleno mezerou a pomlčkou)
7. **Variantní hodnoty v modelech** - odstraní modely obsahující VariantValue delší než 2 znaky
8. **Nepovolené znaky** - vyřadí záznamy s nepoužívanými znaky (ü, ß, ľ, atd.)
9. **NameMemory čištění** - odstraní záznamy, které nemají klíč ve všech třech souborech (Type, Brand, Model)

**Důležité**: CategoryNameMemory a BrandCodeList jsou pouze zdrojové soubory pro definici pravidel - skript je nikdy nemodifikuje ani neuloží.

### Použití

```bash
cd desaka_unifier/memory_tests

# Suchý běh - pouze zobrazí statistiky, neuloží změny
python3 filter_memory.py --language CS --dry-run

# Živý běh - aplikuje změny a uloží soubory
python3 filter_memory.py --language CS

# Pro slovenštinu
python3 filter_memory.py --language SK
```

### Příklad výstupu

```bash
$ python3 filter_memory.py --language CS --dry-run

⚠️  SUCHÝ BĚH - změny nebudou uloženy

================================================================================
FILTROVÁNÍ MEMORY SOUBORŮ - CS
================================================================================

================================================================================
KROK 1: Načítání CategoryNameMemory (zdrojový soubor - nebude modifikován)
================================================================================
✓ Načteno 58 záznamů z CategoryNameMemory

🔍 Hledání hierarchicky neúplných kategorií...
Kontrola kategorií: 100%|██████████| 58/58 [00:00<00:00]

📊 Nalezeno 9 hierarchicky neúplných kategorií
ℹ️  CategoryNameMemory zůstává beze změny - použije se jen pro filtrování CategoryMemory

================================================================================
KROK 2: Čištění CategoryMemory
================================================================================
✓ Načteno 9431 záznamů z CategoryMemory

🧹 Čištění CategoryMemory od neúplných kategorií...
Filtrování CategoryMemory: 100%|██████████| 9431/9431 [00:00<00:00]
   ❌ Odstraněno: 4 záznamů
   ✓ Zbývá: 9427 záznamů

[... další kroky ...]

================================================================================
SHRNUTÍ FILTROVÁNÍ
================================================================================

Jazyk: CS
Režim: SUCHÝ BĚH (změny neuloženy)

Výsledný počet záznamů:
  • CategoryMemory:          9,427 záznamů
  • ProductBrandMemory:     22,201 záznamů
  • ProductTypeMemory:      13,754 záznamů
  • ProductModelMemory:     19,681 záznamů
  • VariantNameMemory:          73 záznamů
  • VariantValueMemory:      3,208 záznamů
  • NameMemory:                 50 záznamů

⚠️  Suchý běh dokončen - žádné změny nebyly provedeny
💡 Spusťte bez --dry-run pro aplikování změn
================================================================================
```

### Bezpečnostní funkce

- **Dry-run režim** - testovací běh bez uložení změn
- **Automatické zálohy** - před každým uložením se vytvoří záloha (`.csv_old` s timestampem)
- **Progress bary** - vizuální indikace průběhu pro každý krok
- **Detailní reporty** - počet odstraněných a zbývajících záznamů pro každý filtr
- **Kaskádové filtrování** - každý filtr pracuje s výsledky předchozích filtrů

### Kdy použít

- **Po bulk importu** - vyčistit nově importovaná data
- **Pravidelná údržba** - odstranit nahromadděné nekvalitní záznamy
- **Před exportem** - zajistit konzistenci dat
- **Po změnách BrandCodeList** - synchronizovat memory soubory se seznamem značek

## Architektura extraction metod

Všechny extraction metody používají stejný vzor:

1. **Načtení learned mappings** z memory CSV souboru (KEY→VALUE slovník)
2. **Exact match check** - pokud je KEY v mappings, vrátit VALUE
3. **Heuristic fallback** - pro nové/neznámé produkty použít pattern matching

```python
def extract_*(product_name: str) -> str:
    # 1. Check learned mappings first
    if product_name in MAPPINGS:
        return MAPPINGS[product_name]

    # 2. Fallback to heuristic detection
    # ... pattern matching logic ...

    return default_value
```

## Požadavky na testy

Všechny unit testy vyžadují:
- ✅ **100% přesnost** (`assertEqual(accuracy, 100.0)`)
- ✅ **Row indexy** pro selhání (`enumerate(start=2)` kvůli CSV header)
- ✅ **Prvních 20 mismatches** s čísly řádků
- ✅ **Jasné chybové zprávy** s počtem chyb

## Poznámky k implementaci

- Extraction metody používají **learned mappings** pro 100% přesnost
- Heuristic fallback je připraven pro nové/neznámé produkty
- Unit testy **vyžadují 100% shodu** - žádné chyby nejsou tolerovány
- Manuální kontrolní skript pomáhá identifikovat a opravit nesprávné mapování
- Všechny změny memory souborů vytvářejí zálohu (`.csv.backup`)

## Workflow pro údržbu memory souborů

1. **Automatická populace**: Použít populate scripts pro načtení nových produktů
2. **Automatické filtrování**: Spustit `filter_memory.py --dry-run` pro zjištění rozsahu čištění, pak `filter_memory.py` pro aplikaci
3. **Unit testy**: Spustit testy pro ověření 100% přesnosti
4. **Manuální kontrola**: Použít `manual_memory_check.py` pro kontrolu kvality a detekci duplicit
5. **Čištění**: Vyřadit nesprávné KEYs identifikované během manuální kontroly
6. **Re-test**: Znovu spustit testy pro ověření
7. **Commit**: Commitnout vyčištěné memory soubory

## Zbývající implementace

Následující memory soubory zatím nemají extraction metody:

- NameMemory_CS/SK.csv - transformace složitých názvů produktů
- DescMemory_CS/SK.csv - generování HTML popisů (vyžaduje AI/templates)
- ShortDescMemory_CS/SK.csv - generování krátkých popisů (vyžaduje AI)
- CategoryNameMemory_CS.csv - názvy kategorií
- VariantValueMemory_CS/SK.csv - překlad hodnot variant
- ProductBrand/Model/Type_SK.csv - slovenské verze (podobná logika jako CS)
