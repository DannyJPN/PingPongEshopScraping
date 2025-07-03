# Implementace prohledávání internetu a správných modelů

## Přehled implementovaných změn

Úspěšně byly implementovány všechny požadované změny pro zlepšení AI promptů:

### 1. ✅ Instrukce pro prohledávání internetu
- **Všechny prompty** nyní instruují AI k prohledání internetu pro aktuální informace
- **pincesobchod.cz** je explicitně zmíněn ve všech promptech pro table tennis kontext
- **Aktuální tržní terminologie** je požadována pro lepší výsledky

### 2. ✅ Platform-specifické prohledávání pro category mapping
- **Heureka.cz** - prohledávání kategoriální struktury
- **Glami.cz** - research kategoriální taxonomie
- **Google Shopping** - analýza kategoriální struktury
- **Zbozi.cz** - prohledávání kategoriální struktury
- **Fallback** - automatické generování URL pro neznámé platformy

### 3. ✅ Správné modely pro různé akce
- **GPT-4** pro složité úkoly (keywords, category mapping, variant standardization, product analysis)
- **GPT-3.5-turbo** zůstává výchozí pro jednoduché úkoly

## Upravené metody

### `generate_google_keywords()`
```
Nové instrukce:
1. Search the internet for similar products and current market trends
2. Check pincesobchod.cz for table tennis product terminology and keywords
3. Use current market terminology and popular search terms
Model: GPT-4
```

### `generate_zbozi_keywords()`
```
Nové instrukce:
1. Search the internet for similar products on Czech e-commerce sites
2. Check pincesobchod.cz for table tennis product terminology in Czech
3. Research Zbozi.cz platform to understand their keyword structure
4. Use Czech terminology that Czech customers would search for
Model: GPT-4
```

### `standardize_variant_name()`
```
Nové instrukce:
1. Search the internet for standard table tennis product variant terminology
2. Check pincesobchod.cz for how they categorize table tennis product variants
3. Use industry-standard terminology that customers would recognize
Model: GPT-4
```

### `standardize_variant_value()`
```
Nové instrukce:
1. Search the internet for standard table tennis product specifications and terminology
2. Check pincesobchod.cz for how they specify table tennis product variant values
3. Use industry-standard units and terminology that customers would recognize
Model: GPT-4
```

### `suggest_category_mapping()`
```
Nové instrukce:
1. Search the internet for {platform} platform category structure
2. Visit {platform_url} to research their current category taxonomy
3. Check pincesobchod.cz for table tennis product categorization
4. Ensure the mapping follows {platform}'s actual category structure

Platform URLs:
- Heureka: heureka.cz
- Glami: glami.cz
- Google: google.com/shopping
- Zbozi: zbozi.cz
- Ostatní: {platform.lower()}.com

Model: GPT-4
```

### `find_category()`
```
Nové instrukce:
1. Search the internet for similar products to understand their categorization
2. Check pincesobchod.cz for table tennis product categories
3. Use your knowledge of current market categorization standards
Model: GPT-4
```

### `find_brand()`
```
Nové instrukce:
1. Search the internet for information about table tennis brands and manufacturers
2. Check pincesobchod.cz for brand information and product listings
3. Use your knowledge of current table tennis brand landscape
Model: GPT-4
```

### `generate_product_name()`
```
Nové instrukce:
1. Search the internet for table tennis product naming conventions
2. Check pincesobchod.cz for how they structure table tennis product names
3. Use current industry standards for product naming
Model: GPT-4
```

### `translate_and_validate_description()`
```
Nové instrukce:
1. Search the internet for current table tennis terminology and product descriptions
2. Check pincesobchod.cz for how they describe similar table tennis products
3. Use current industry-standard terminology that customers would understand
Model: GPT-4
```

## Příklady promptů

### Google Keywords s internetovým prohledáváním:
```
I respectfully ask you to:
1. Search the internet for similar products and current market trends
2. Check pincesobchod.cz for table tennis product terminology and keywords
3. Analyze the product information thoroughly
4. Generate exactly 5 relevant keywords
5. Keywords should be suitable for Google advertising
6. Draw inspiration from existing keywords in memory for consistency
7. Use current market terminology and popular search terms
```

### Category Mapping s platform-specifickým prohledáváním:
```
I respectfully ask you to:
1. Search the internet for Heureka platform category structure
2. Visit heureka.cz to research their current category taxonomy
3. Check pincesobchod.cz for table tennis product categorization
4. Analyze the original category carefully
5. Consider the target platform's category structure and naming conventions
6. Ensure the mapping follows Heureka's actual category structure
```

## Výhody implementace

1. **Aktuální informace** - AI má přístup k nejnovějším tržním informacím
2. **Platform-specifické znalosti** - AI prohledává konkrétní platformy pro přesné mapování
3. **Table tennis kontext** - pincesobchod.cz poskytuje specializovaný kontext
4. **Lepší modely** - GPT-4 pro složité úkoly zajišťuje vyšší kvalitu
5. **Tržní relevance** - použití aktuální terminologie a standardů

## Testování

Všechny změny byly otestovány pomocí komplexního test scriptu:
- ✅ Internet search instrukce ve všech promptech
- ✅ pincesobchod.cz instrukce ve všech promptech  
- ✅ Platform-specifické URL pro category mapping
- ✅ GPT-4 model pro složité úkoly
- ✅ Správné mapování platform URLs

## Status: ✅ KOMPLETNĚ IMPLEMENTOVÁNO

Všechny prompty nyní instruují AI k prohledávání internetu, pincesobchod.cz a platform-specifických stránek pro zlepšení kvality výsledků. Správné modely jsou použity pro každou akci.
