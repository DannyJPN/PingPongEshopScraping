# Analýza parametrů RepairedProduct při převodu z DownloadedProduct

Tato analýza se zaměřuje na parametry, které **nejsou** jen přímou kopií z DownloadedProduct ani nejsou načítány přímo z jediného Memory souboru, ale mají komplexní odvozovací logiku.

## Přehled struktury tříd

### DownloadedProduct (vstup)
```python
- name: str
- short_description: str
- description: str
- main_photo_filepath: str
- gallery_filepaths: str
- variants: List[Variant]
- url: str
```

### RepairedProduct (výstup)
```python
- original_name: str
- category: str
- brand: str
- type: str
- model: str
- category_ids: str
- code: str
- desc: str
- glami_category: str
- google_category: str
- google_keywords: str
- heureka_category: str
- name: str
- price: str
- price_standard: str
- shortdesc: str
- url: str
- Variants: List[Variant]
- zbozi_category: str
- zbozi_keywords: str
```

---

## Parametry s komplexní logikou

### 1. **name** (parser.py:1671-1717)

**Zdroj dat**: Komponován z více parametrů + Memory

**Proces:**
1. Hledá v `NameMemory_{language}` s klíčem `downloaded.name`
2. Zkouší normalizovanou exact match
3. Zkouší fuzzy matching podobných klíčů (threshold 0.8)
4. Pokud nenajde v memory:
   - Získá `type` pomocí `_get_product_type()`
   - Získá `brand` pomocí `_get_brand(for_name_composition=True)`
   - Získá `model` pomocí `_get_product_model()`
   - **Formát**: `"{type} {brand} {model}"` nebo `"{type} {model}"` (pokud brand prázdný)
5. Uloží výsledek do `NameMemory_{language}`

**Závislosti**: ProductTypeMemory, ProductBrandMemory, ProductModelMemory, BrandCodeList

---

### 2. **type** (parser.py:971-1051)

**Zdroj dat**: ProductTypeMemory + heuristika + AI

**Proces:**
1. Hledá v `ProductTypeMemory_{language}[downloaded.name]`
2. Zkouší normalizovanou exact match
3. Zkouší fuzzy matching (threshold 0.8)
4. **Heuristická extrakce**:
   - Získá všechny existující typy z `ProductTypeMemory`
   - Hledá exact matches v textech produktu (name, url, description, short_description)
   - Pokud nenajde, zkouší **similarity search** (SequenceMatcher, threshold 0.8)
5. Pokud heuristika neuspěje → **OpenAI**:
   - Volá `openai.get_product_type()`
   - Předává heuristic_info (nalezené kandidáty)
   - Vyžaduje potvrzení uživatelem (pokud ne `--ConfirmAIResults`)
6. Fallback: Ptá se uživatele přímo
7. Default: `"Product"`

**Závislosti**: ProductTypeMemory, OpenAI GPT-4o-mini

---

### 3. **model** (parser.py:1053-1133)

**Zdroj dat**: ProductModelMemory + heuristika + AI + formátování

**Proces:**
1. Hledá v `ProductModelMemory_{language}[downloaded.name]`
2. Zkouší normalizovanou exact match → aplikuje `_format_model_name()`
3. Zkouší fuzzy matching (threshold 0.8)
4. Heuristická extrakce (stejně jako u type)
5. OpenAI: `openai.get_product_model()`
6. **Formátování** pomocí `_format_model_name()`:
   - Rozdělí na slova
   - Akronymy (≤4 znaky, velká písmena) zůstávají uppercase
   - Ostatní slova → capitalize
7. Default: `"Standard"`

**Závislosti**: ProductModelMemory, OpenAI GPT-4o-mini

---

### 4. **brand** (parser.py:866-964)

**Zdroj dat**: ProductBrandMemory + heuristika + AI + speciální zpracování

**Proces:**
1. Hledá v `ProductBrandMemory_{language}[downloaded.name]`
2. Zkouší normalizovanou exact match
3. Zkouší fuzzy matching (threshold 0.8)
4. **Heuristická extrakce**:
   - Získá seznam značek z `BrandCodeList`
   - Hledá exact matches v product textech
   - Pokud nenajde → similarity search
5. OpenAI: `openai.find_brand()`
6. **Speciální zpracování pro name composition** (`for_name_composition=True`):
   - Kontroluje `_is_desaka_brand()` - pokud ano, vrací `""`
   - Aplikuje `_format_brand_name()`:
     - Akronymy (≤4 znaky, uppercase) zůstávají
     - Ostatní → capitalize
7. Default: `"Unknown"` (nebo `""` pro name composition)

**Speciální detekce Desaka**:
```python
desaka_patterns = ['desaka', 'desaka s.r.o.', 'desaka s.r.o',
                   'desaka spol. s r.o.', 'desaka spol. s r.o']
```

**Závislosti**: ProductBrandMemory, BrandCodeList, OpenAI GPT-4o

---

### 5. **category** (parser.py:738-864)

**Zdroj dat**: CategoryMemory + CategoryList + CategoryNameMemory (key-based system) + AI

**Proces - Key-Based System:**
1. Hledá v `CategoryMemory_{language}[downloaded.name]` → vrací **category_key**
2. **Standardizace klíče**: `_standardize_category_by_key(category_key)`
   - Validuje proti `CategoryList` (list keys)
3. **Překlad**: `_get_translated_category_name(standardized_key)`
   - Hledá v `CategoryNameMemory_{language}[key]`
   - Vrací přeložený název pro daný jazyk
4. Zkouší normalizovanou exact match
5. Zkouší fuzzy matching (threshold 0.8) - zobrazuje přeložené názvy
6. **Heuristická extrakce**:
   - Získá všechny **translated values** z `CategoryNameMemory`
   - Hledá exact matches v product textech
   - Similarity search
7. OpenAI: `openai.find_category()` - pracuje s přeloženými názvy
8. **Ukládá se**: standardized key (ne translated value)
9. **Vrací se**: translated value (ne key)

**Architektura:**
```
CategoryList         → Master list keys (např. "Raketky>Běžecké")
CategoryMemory_CS    → downloaded.name → category_key
CategoryNameMemory_CS → category_key → "Pálky > Běžecké"
CategoryNameMemory_SK → category_key → "Pálky > Bežecké"
```

**Závislosti**: CategoryMemory, CategoryList, CategoryNameMemory, OpenAI GPT-4o

---

### 6. **Variants** (parser.py:1937-1989)

**Zdroj dat**: downloaded.variants + několik Memory souborů + generování kódů

**Proces:**
Každá downloaded variant → 1 RepairedProduct variant s:

#### a) **key_value_pairs** (max 3 páry)
- **Standardizace klíčů** pomocí `_standardize_variant_name()`:
  - `VariantNameMemory_{language}` (fuzzy match, AI, user input)
- **Standardizace hodnot** pomocí `_standardize_variant_value()`:
  - `VariantValueMemory_{language}` (fuzzy match, AI, user input)

#### b) **current_price** a **basic_price**
- Přímá kopie z downloaded variant
- Default: `0.0`

#### c) **stock_status**
- Standardizace pomocí `_standardize_stock_status()`:
  - `StockStatusMemory_{language}`
  - Fuzzy matching (threshold 0.8)
  - AI standardizace
  - User input fallback

#### d) **variantcode** (parser.py:1893-1935)
- **Generovaný**: `base_code + "-" + 2-digit index`
- Kontrola existujících variant v memory
- Hledá první volný index od 1
- Tracking pomocí `self.assigned_variant_codes`

**Závislosti**: VariantNameMemory, VariantValueMemory, StockStatusMemory, OpenAI GPT-4o-mini

---

### 7. **code** (parser.py:1241-1293)

**Zdroj dat**: Složený z více Memory souborů + generování

**Formát**: `[BrandCode:3][CategoryCode:2][SubCategoryCode:2][Index:4]`

**Proces:**
1. **BrandCode** (3 znaky):
   - Kontrola `_is_desaka_brand()` → vždy `"DES"`
   - Jinak z `BrandCodeList[brand]`
   - Default: `"DES"`

2. **CategoryCode** (2 cifry):
   - Rozdělí category key pomocí `>` separator
   - První část (main category) → `CategoryCodeList[first_part]`
   - Formát: `{int:02d}`
   - Default: `"00"`

3. **SubCategoryCode** (2 cifry):
   - Druhá část category key → `CategorySubCodeList[second_part]`
   - Formát: `{int:02d}`
   - Default: `"00"`

4. **Index** (4 cifry) - `_get_next_product_index()`:
   - Kontroluje existující produkty se stejným `base_code` (prvních 7 znaků)
   - Pokud existuje produkt se stejným názvem → reuse index
   - Sbírá všechny použité indexy:
     - Z `self.assigned_codes`
     - Z `self.export_products`
   - Najde první volný index od 1
   - Formát: `{int:04d}`

5. Finální kód: `DES0202-0001`, `BUT0101-0023`, atd.
6. Tracking: Přidá do `self.assigned_codes`

**Závislosti**: BrandCodeList, CategoryCodeList, CategorySubCodeList, CategoryList, existing export_products

---

### 8. **category_ids** (parser.py:1204-1239)

**Zdroj dat**: Odvozeno z category + CategoryIDList

**Proces:**
1. Najde `category_key` z category value:
   - Pokud category je key v `CategoryList` → použij přímo
   - Jinak reverse lookup: `_find_category_key_by_value()` v `CategoryNameMemory`
2. Rozdělí key pomocí `>` → `["Raketky", "Běžecké"]`
3. **Reverse order**: `["Běžecké", "Raketky"]`
4. Mapování každé části pomocí `CategoryIDList[part]`
5. Pokud ID neexistuje → ptá se uživatele (`_ask_user_for_category_id()`)
6. Výsledek: `"456,123"` (comma-separated)

**Závislosti**: CategoryIDList, CategoryList, CategoryNameMemory

---

### 9. **price** a **price_standard** (parser.py:1760-1791)

**Zdroj dat**: Vypočítáno z variant cen + DPH

**Proces:**
1. Sbírá všechny `basic_price` z `downloaded.variants`
2. Najde **maximální cenu**: `max_price`
3. Získá **DPH sazbu**:
   - Z `memory['ExportProduct']['dph']`
   - Default: `21%` (0.21)
4. Výpočty:
   - **price** (bez DPH): `max_price / (1 + vat_rate)`
   - **price_standard** (s DPH): `max_price`
5. Formát: `"{value:.2f}"`
6. Default: `"0"`, `"0"`

**Závislosti**: downloaded.variants, ExportProduct default values (DPH)

---

### 10. **desc** (parser.py:1517-1573)

**Zdroj dat**: DescMemory + AI překlad/validace

**Proces:**
1. Hledá v `DescMemory_{language}[downloaded.name]`
2. Zkouší normalizovanou exact match
3. Zkouší fuzzy matching (threshold 0.8)
4. **OpenAI překlad/validace**:
   - `openai.translate_and_validate_description()`
   - **NE generování** z ničeho - pouze překlad existujícího
   - Vyžaduje potvrzení uživatelem
   - Zobrazuje HTML formatted preview
5. Pokud `downloaded.description` prázdný → ptá se uživatele
6. Fallback: `downloaded.description` (původní)

**Závislosti**: DescMemory, OpenAI GPT-4o

---

### 11. **shortdesc** (parser.py:1793-1852)

**Zdroj dat**: ShortDescMemory + AI překlad/generování

**Proces:**
1. Hledá v `ShortDescMemory_{language}[downloaded.name]`
2. Zkouší normalizovanou exact match
3. Zkouší fuzzy matching (threshold 0.8)
4. **OpenAI překlad nebo generování**:
   - `openai.translate_and_validate_short_description()`
   - **Může generovat z description**, pokud short_description prázdný
   - Vyžaduje potvrzení
5. Ptá se uživatele
6. Fallback: `downloaded.short_description[:150]` nebo `""`

**Závislosti**: ShortDescMemory, OpenAI GPT-4o

---

### 12. **google_keywords** (parser.py:1612-1669)

**Zdroj dat**: KeywordsGoogle Memory + AI generování

**Proces:**
1. Hledá v `KeywordsGoogle_{language}[downloaded.name]`
2. Zkouší normalizovanou exact match
3. Zkouší fuzzy matching (threshold 0.8)
4. **OpenAI generování**:
   - `openai.generate_google_keywords()`
   - Předává celý `memory_content` pro konzistenci
   - **Formát**: 5 keywordů oddělených čárkami
   - Vyžaduje potvrzení
5. Ptá se uživatele
6. Default: `""`

**Validace formátu** (memory_checker.py):
- Musí obsahovat přesně 5 keywordů
- Oddělené čárkami
- Validní formát: `"keyword1, keyword2, keyword3, keyword4, keyword5"`

**Závislosti**: KeywordsGoogle Memory, OpenAI GPT-4o-mini

---

### 13. **zbozi_keywords** (parser.py:2109-2166)

**Zdroj dat**: KeywordsZbozi Memory + AI generování

**Proces:**
1. Stejný jako google_keywords
2. **Formát**: 2 keywordy oddělené čárkami
3. `openai.generate_zbozi_keywords()`

**Validace formátu**:
- Musí obsahovat přesně 2 keywordy
- Oddělené čárkami
- Validní formát: `"keyword1, keyword2"`

**Závislosti**: KeywordsZbozi Memory, OpenAI GPT-4o-mini

---

### 14. **Platform-specific categories** (parser.py:1575-1610)

#### **glami_category, google_category, heureka_category, zbozi_category**

**Zdroj dat**: CategoryMapping{Platform} Memory + AI suggestions

**Proces:**
1. Hledá v `CategoryMapping{Platform}_{language}[category]`
   - Klíčem je **repaired.category** (přeložený název)
2. **OpenAI mapping suggestion**:
   - `openai.suggest_category_mapping(category, platform, language, memory_content)`
   - Předává celý existing memory pro konzistenci
   - Vyžaduje potvrzení
3. Ptá se uživatele s kontextem:
   - Zobrazuje product name, URL, current category
4. Default: `""`

**Platforms**: Glami, Google, Heureka, Zbozi

**Závislosti**: CategoryMappingGlami, CategoryMappingGoogle, CategoryMappingHeureka, CategoryMappingZbozi, OpenAI GPT-4o

---

## Společné vzory a techniky

### 1. **Fuzzy Matching** (threshold 0.8)
Používá `difflib.SequenceMatcher` pro:
- Similar memory keys matching
- Heuristic similarity search
- Normalizace: lowercase + whitespace normalization

### 2. **Heuristic Extraction**
Proces:
1. **Exact match** v textech (whole words, case-insensitive)
2. Pokud nenajde → **Similarity search** (threshold 0.8)
3. Substring matching s boosted similarity
4. Vrací: single match (pokud 1) nebo list všech

Texty prohledávány:
- `downloaded.name`
- `downloaded.url`
- `downloaded.description` / `downloaded.desc`
- `downloaded.short_description` / `downloaded.shortdesc`

### 3. **Memory Save Flow**
Každá metoda následuje pattern:
1. Check exact match → return
2. Check normalized exact match → save + return
3. Check fuzzy matches → ask user → save + return
4. Heuristic extraction → use if single match
5. AI call → confirm → save + return
6. Ask user → save + return
7. Fallback default

### 4. **User Confirmation Dialog**
Standardní formát:
```
================================
🤖 AI SUGGESTION FOR: {Property}
================================
📦 Product: {name}
🔗 URL: {url}
--------------------------------
🔍 HEURISTIC ANALYSIS RESULTS:
   Found: {matches} / No matches
--------------------------------
📄 Current Value: {current}
🎯 AI Suggests: {suggestion}
================================
✅ Press Enter to confirm or type new value:
```

### 5. **Memory File Naming Convention**
```
{PropertyName}Memory_{Language}.csv
```
Příklady:
- `ProductBrandMemory_CS.csv`
- `CategoryMemory_SK.csv`
- `VariantNameMemory_CS.csv`

---

## Parametry NEKOMPLIKOVANÉ (přímá kopie nebo single memory)

Pro úplnost, tyto parametry mají přímočarý mapping:

### Přímá kopie z DownloadedProduct:
- **original_name** ← `downloaded.name`
- **url** ← `downloaded.url`

### Memory-only parametry (nejsou předmětem této analýzy):
Existují memory soubory, které mapují celou hodnotu přímo:
- N/A v současné implementaci (všechny memory mají dodatečnou logiku)

---

## Souhrn závislostí na Memory souborech

| Parametr | Memory soubory | Další zdroje |
|----------|----------------|--------------|
| **name** | NameMemory, ProductTypeMemory, ProductBrandMemory, ProductModelMemory, BrandCodeList | AI, formátování |
| **type** | ProductTypeMemory | Heuristika, AI |
| **model** | ProductModelMemory | Heuristika, AI, formátování |
| **brand** | ProductBrandMemory, BrandCodeList | Heuristika, AI, Desaka check, formátování |
| **category** | CategoryMemory, CategoryList, CategoryNameMemory | Heuristika, AI |
| **Variants.key_value_pairs** | VariantNameMemory, VariantValueMemory | AI |
| **Variants.stock_status** | StockStatusMemory | AI |
| **Variants.variantcode** | — | Generováno z base_code + index |
| **code** | BrandCodeList, CategoryCodeList, CategorySubCodeList, CategoryList | Index generování |
| **category_ids** | CategoryIDList, CategoryList, CategoryNameMemory | Reverse category lookup |
| **price/price_standard** | ExportProduct defaults (DPH) | Výpočet z variant cen |
| **desc** | DescMemory | AI překlad/validace |
| **shortdesc** | ShortDescMemory | AI překlad/generování |
| **google_keywords** | KeywordsGoogle | AI generování |
| **zbozi_keywords** | KeywordsZbozi | AI generování |
| **{platform}_category** | CategoryMapping{Platform} | AI suggestions |

---

## AI Model Usage

| Úkol | Model | Metoda |
|------|-------|--------|
| Category classification | GPT-4o | `find_category()` |
| Brand detection | GPT-4o | `find_brand()` |
| Product type | GPT-4o-mini | `get_product_type()` |
| Product model | GPT-4o-mini | `get_product_model()` |
| Description translation | GPT-4o | `translate_and_validate_description()` |
| Short description | GPT-4o | `translate_and_validate_short_description()` |
| Keywords (Google) | GPT-4o-mini | `generate_google_keywords()` |
| Keywords (Zbozi) | GPT-4o-mini | `generate_zbozi_keywords()` |
| Category mapping | GPT-4o | `suggest_category_mapping()` |
| Variant name | GPT-4o-mini | `standardize_variant_name()` |
| Variant value | GPT-4o-mini | `standardize_variant_value()` |
| Stock status | GPT-4o-mini | (standardize_stock_status) |

---

## Command Line Flags Impact

| Flag | Vliv na parametry |
|------|-------------------|
| `--SkipAI` | Vypne všechny AI calls, používá pouze memory + heuristics + user input |
| `--ConfirmAIResults` | Auto-potvrzuje všechny AI suggestions bez user dialogu |
| `--UseFineTunedModels` | Používá custom fine-tuned modely místo standardních GPT |

---

## Conclusion

Většina parametrů RepairedProduct využívá **multi-source approach**:
1. **Memory lookup** (exact, normalized, fuzzy)
2. **Heuristic extraction** (exact match, similarity search)
3. **AI assistance** (GPT-4o / GPT-4o-mini)
4. **User confirmation/input**
5. **Additional processing** (formátování, generování kódů, výpočty)

Pouze 2 parametry jsou přímá kopie (`original_name`, `url`). Všechny ostatní procházejí komplexním workflow s multiple fallback strategies.
