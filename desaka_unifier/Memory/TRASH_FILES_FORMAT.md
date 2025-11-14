# Trash Files Format - Fine-tuning Negative Examples

## Účel

Trash soubory obsahují **negativní příklady** pro fine-tuning AI modelů. Zatímco Memory soubory obsahují správné odpovědi, Trash soubory obsahují špatné/zamítnuté odpovědi.

## Struktura souborů

Pro každý Memory soubor může existovat odpovídající Trash soubor:

| Memory soubor | Trash soubor | Popis |
|---------------|--------------|-------|
| `NameMemory_CS.csv` | `NameTrash_CS.csv` | Zamítnuté produktové názvy |
| `ProductTypeMemory_CS.csv` | `ProductTypeTrash_CS.csv` | Špatné typy produktů |
| `ProductBrandMemory_CS.csv` | `ProductBrandTrash_CS.csv` | Špatné značky |
| `ProductModelMemory_CS.csv` | `ProductModelTrash_CS.csv` | Špatné modely |
| `DescMemory_CS.csv` | `DescTrash_CS.csv` | Špatné popisy |
| `KeywordsGoogle_CS.csv` | `KeywordsGoogleTrash_CS.csv` | Špatné Google klíčová slova |
| `KeywordsZbozi_CS.csv` | `KeywordsZboziTrash_CS.csv` | Špatné Zbozi klíčová slova |
| `CategoryMemory_CS.csv` | `CategoryTrash_CS.csv` | Špatné kategorie |
| `CategoryMappingHeureka_CS.csv` | `CategoryMappingHeurekaTrash_CS.csv` | Špatné Heureka mapování |
| `CategoryMappingGlami_CS.csv` | `CategoryMappingGlamiTrash_CS.csv` | Špatné Glami mapování |
| `CategoryMappingGoogle_CS.csv` | `CategoryMappingGoogleTrash_CS.csv` | Špatné Google mapování |
| `CategoryMappingZbozi_CS.csv` | `CategoryMappingZboziTrash_CS.csv` | Špatné Zbozi mapování |

## Formát CSV

**Stejný formát jako Memory soubory:**

```csv
"KEY","VALUE"
"original_product_name","rejected_value"
"another_product","bad_value"
```

### Příklad: NameTrash_CS.csv

```csv
"KEY","VALUE"
"Butterfly Tenergy 05 2.1mm","Potah Butterfly Tenergy 05 2.1mm"
"Joola Flash Ball","Míček Joola Flash"
"Gewo Neottec XXP 50","Guma Gewo Neottec XXP 50"
```

**Proč jsou tyto špatné?**
- Obsahují tloušťku v názvu (2.1mm)
- Chybí správná kategorizace
- Použití "guma" místo "potah"

### Příklad: ProductTypeTrash_CS.csv

```csv
"KEY","VALUE"
"Butterfly Tenergy 05","Guma"
"Joola Carbon Pro","Raketa"
"Donic Schildkröt Ball","Kulička"
```

**Proč jsou tyto špatné?**
- "Guma" místo "Potah"
- "Raketa" místo "Pálka" nebo "Dřevo"
- "Kulička" místo "Míček"

### Příklad: KeywordsGoogleTrash_CS.csv

```csv
"KEY","VALUE"
"Butterfly Tenergy 05","tenergy, butterfly, 05, rubber, tenis"
"Joola Flash Ball","ball, flash, joola"
```

**Proč jsou tyto špatné?**
- Méně než 5 klíčových slov (Google vyžaduje 5)
- Použití anglických termínů místo českých
- Nesouvisející klíčová slova

## Použití při fine-tuningu

### Pozitivní příklad (Memory):
```json
{
  "messages": [
    {"role": "user", "content": "Analyzuj produkt: Butterfly Tenergy 05"},
    {"role": "assistant", "content": "{\"type\": \"Potah\", \"brand\": \"Butterfly\", \"model\": \"Tenergy 05\"}"}
  ]
}
```

### Negativní příklad (Trash):
```json
{
  "messages": [
    {"role": "user", "content": "Analyzuj produkt: Butterfly Tenergy 05"},
    {"role": "assistant", "content": "{\"error\": \"REJECTED\", \"reason\": \"Incorrect terminology\", \"rejected_type\": \"Guma\", \"note\": \"Should use 'Potah' not 'Guma'\"}"}
  ]
}
```

## Jak vytvořit Trash soubory

### 1. Manuální tvorba
Procházejte historii zamítnutých produktů a přidejte je do odpovídajících Trash souborů.

### 2. Export z logů
```bash
# Najděte zamítnuté produkty v logách
grep "REJECTED" H:/Logs/*.log > rejected_products.txt

# Zpracujte a přidejte do Trash souborů
```

### 3. Automatická detekce
Při běhu unifier.py, pokud uživatel odmítne AI návrh, uložte ho do Trash souboru.

## Minimální počet příkladů

Pro efektivní fine-tuning:
- **Memory příklady:** Minimálně 50-100 pozitivních příkladů
- **Trash příklady:** Minimálně 20-50 negativních příkladů
- **Poměr:** Ideálně 2:1 až 3:1 (pozitivní:negativní)

## Doporučené workflow

1. Nashromážděte alespoň 100 Memory příkladů
2. Nashromážděte 30-50 Trash příkladů
3. Spusťte fine-tuning s oběma sadami dat
4. Model se naučí:
   - Co je správně (z Memory)
   - Co je špatně (z Trash)
   - Rozdíly mezi dobrými a špatnými odpověďmi

## Výhody contrastive learning

✅ Model lépe rozpozná špatné odpovědi
✅ Sníží se false positives (špatné návrhy)
✅ Zvýší se precision (přesnost správných návrhů)
✅ Model se naučí "red flags" (varovné signály)

## Údržba

- **Pravidelně aktualizujte:** Přidávejte nové příklady z produkce
- **Validujte konzistenci:** Ujistěte se, že Trash příklady jsou opravdu špatné
- **Balancujte data:** Udržujte poměr 2:1 až 3:1 (Memory:Trash)
- **Logujte zdroje:** Poznamenejte si, odkud příklady pocházejí

## Poznámka

Trash soubory jsou **volitelné**. Pokud neexistují, fine-tuning použije pouze Memory soubory (pozitivní příklady). Ale kombinace obou typů dat poskytuje nejlepší výsledky.
