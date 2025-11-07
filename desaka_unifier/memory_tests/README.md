# Memory Tests - Heuristic Extraction Methods

Tato složka obsahuje heuristické extraction metody a unit testy pro memory CSV soubory.

## Přehled

Každý memory soubor má:
1. **Extraction metodu** (`extract_*.py`) - heuristická metoda pro extrakci VALUE z KEY
2. **Unit test** (`test_*.py`) - test, který ověřuje přesnost extraction metody proti skutečnému memory souboru

## Implementované extraction metody

### Hlavní tři (Product data)

| Memory soubor | Extraction metoda | Test | Přesnost |
|---------------|-------------------|------|----------|
| ProductBrandMemory_CS.csv | extract_product_brand.py | test_product_brand.py | **99.40%** ✓ |
| ProductModelMemory_CS.csv | extract_product_model.py | test_product_model.py | **58.41%** |
| ProductTypeMemory_CS.csv | extract_product_type.py | test_product_type.py | **66.52%** |

### Doplňkové extraction metody

| Memory soubor | Extraction metoda | Test | Přesnost |
|---------------|-------------------|------|----------|
| CategoryMemory_CS.csv | extract_category.py | test_category.py | N/A |
| VariantNameMemory_CS.csv | extract_variant_name.py | test_variant_name.py | **27.78%** |
| StockStatusMemory_CS.csv | extract_stock_status.py | test_stock_status.py | **9.38%** |

## Spuštění testů

```bash
cd desaka_unifier/memory_tests

# Spustit jeden test
python3 test_product_brand.py

# Spustit všechny testy
python3 -m unittest discover -p "test_*.py" -v
```

## Interpretace výsledků

### Vysoká přesnost (>95%)
- **ProductBrand (99.40%)**: Brand detection je úspěšný díky načtení všech unikátních brandů z memory souboru

### Střední přesnost (50-70%)
- **ProductModel (58.41%)**: Čištění modelových názvů je složité kvůli:
  - Číslům v názvech modelů (např. "Europa 25")
  - Různým konvencím odstraňování variant
  - Nejednoznačným hranicím mezi model/variant

- **ProductType (66.52%)**: Klasifikace typů vyžaduje:
  - Znalost produktových řad (např. "Rasanter" = rubber, "Viscaria" = blade)
  - Kontext (např. "Tisch" může být stůl nebo součást sady)
  - Prioritu detekce (set vs. jednotlivý produkt)

### Nízká přesnost (<30%)
- **VariantName (27.78%)**: Limitované translation pravidla
- **StockStatus (9.38%)**: Velmi specifické formatted messages vyžadující AI/templates

## Závěry

1. **Brand extraction** je velmi úspěšný s heuristickou metodou
2. **Model a Type extraction** ukazují limity čisté heuristiky - vyžadují:
   - Rozsáhlé slovníky produktových řad
   - Kontext a pravidla priorit
   - Nebo AI pro komplexní případy

3. **Descriptive fields** (DescMemory, ShortDescMemory, StockStatusMemory) vyžadují:
   - AI generování
   - Templates
   - Nebo přesné slovníkové matching

## Zbývající implementace

Následující memory soubory zatím nemají extraction metody (vyžadují AI nebo complex templates):

- NameMemory_CS/SK.csv - transformace complex names
- DescMemory_CS/SK.csv - generování HTML popisů
- ShortDescMemory_CS/SK.csv - generování krátkých popisů
- CategoryNameMemory_CS.csv - kategorie names
- VariantValueMemory_CS/SK.csv - variant value translations
- ProductBrand/Model/Type_SK.csv - Slovak versions (similar logic as CS)
- productBrandMemoryValidated.csv - validated brand data
- productTypeMemoryValidated.csv - validated type data

## Poznámky k implementaci

- Extraction metody jsou **čistě heuristické** - nepoužívají AI
- Unit testy **netestují 100% shodu** - měří úspěšnost heuristické predikce
- Vysoká přesnost (>95%) je výborná, střední přesnost (50-70%) je očekávaná
- Nízká přesnost (<30%) ukazuje, že field vyžaduje AI nebo templates
