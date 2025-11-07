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

**Rozšířené příkazy (pro velké skupiny s tisíci KEYs):**
- `show all` - Zobrazit všechny KEYs (i u velkých skupin)
- `show page N` - Zobrazit stránku N (50 KEYs na stránku)
- `search TEXT` - Vyhledat KEYs obsahující TEXT
- `pattern TEXT` - Označit všechny KEYs obsahující TEXT k vymazání
- `stats` - Zobrazit statistiky a nejčastější slova v KEYs

**Optimalizace pro velké skupiny:**
- U VALUES s >30 KEYs se automaticky zobrazí pouze vzorky (prvních 15 + posledních 15)
- Označené KEYs se kumulují - můžete postupně přidávat více KEYs
- `pattern` příkaz umožňuje hromadné označení podle vzoru

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

⚠️  Velká skupina (3542 KEYs) - zobrazuji jen vzorky:

--- Prvních 15 KEYs ---
    1. Nittaku Belag Hurricane 3 rot 2,0
    2. Nittaku Belag Magic Carbon rot 1,5
   ...
   15. Nittaku Holz Acoustic FL

  ... 3512 KEYs vynecháno ...

--- Posledních 15 KEYs ---
 3528. Nittaku Ball Premium 40+ 3er Pack
   ...
 3542. Nittaku Tasche Crown Deluxe

--------------------------------------------------------------------------------
💡 Pro velké skupiny použijte rozšířené příkazy:
   'show all'        - Zobrazit všechny KEYs
   'show page N'     - Zobrazit stránku N (50 KEYs na stránku)
   'search TEXT'     - Vyhledat KEYs obsahující TEXT
   'pattern TEXT'    - Označit všechny KEYs obsahující TEXT k vymazání
   'stats'           - Zobrazit statistiky a podobnosti
--------------------------------------------------------------------------------

Zadejte příkaz: search "ASICS"
✓ Nalezeno 0 KEYs obsahujících 'ASICS'

Zadejte příkaz: stats

📊 STATISTIKY
================================================================================
Celkový počet KEYs: 3542

Nejčastější slova v KEYs:
  'Nittaku': 3542x (100.0%)
  'Belag': 2145x (60.5%)
  'Holz': 892x (25.2%)
  ...

Zadejte příkaz: pattern "XXX"
✓ Označeno 15 KEYs obsahujících 'XXX'

[Označeno 15 KEYs k vymazání]

Zadejte příkaz: none
✓ Vymazáno 15 KEYs
```

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
2. **Unit testy**: Spustit testy pro ověření 100% přesnosti
3. **Manuální kontrola**: Použít `manual_memory_check.py` pro kontrolu kvality
4. **Čištění**: Vyřadit nesprávné KEYs identifikované během kontroly
5. **Re-test**: Znovu spustit testy pro ověření
6. **Commit**: Commitnout vyčištěné memory soubory

## Zbývající implementace

Následující memory soubory zatím nemají extraction metody:

- NameMemory_CS/SK.csv - transformace složitých názvů produktů
- DescMemory_CS/SK.csv - generování HTML popisů (vyžaduje AI/templates)
- ShortDescMemory_CS/SK.csv - generování krátkých popisů (vyžaduje AI)
- CategoryNameMemory_CS.csv - názvy kategorií
- VariantValueMemory_CS/SK.csv - překlad hodnot variant
- ProductBrand/Model/Type_SK.csv - slovenské verze (podobná logika jako CS)
