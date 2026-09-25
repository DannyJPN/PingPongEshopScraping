# Report: Převod RepairedProduct na ExportProduct

## Přehled procesu

Proces převodu probíhá v `parser.py` metodou `repaired_to_export_product()`, která vytváří:
1. **Jeden ExportMainProduct** - hlavní produkt
2. **N ExportProductVariant** - pro každou variantu z RepairedProduct.Variants

---

## Kompletní přehled všech 96 vlastností

### Legenda
- **Hodnota pro produkt**: Výchozí hodnota z `ExportMainProduct.__init__()`
- **Hodnota pro variantu**: Výchozí hodnota z `ExportProductVariant.__init__()`
- **Mapování z RepairedProduct**: Jak se hodnota nastavuje při převodu

---

## 1. ZÁKLADNÍ IDENTIFIKACE PRODUKTU

### 1. `id` (int)
- **Produkt výchozí**: `0`
- **Varianta výchozí**: `0`
- **Mapování**: Nenastavuje se při převodu (zůstává 0)

### 2. `typ` (str)
- **Produkt výchozí**: `"produkt"`
- **Varianta výchozí**: `"varianta"`
- **Mapování**:
  - Produkt: Pevně `"produkt"`
  - Varianta: Pevně `"varianta"`

### 3. `varianta_id` (str)
- **Produkt výchozí**: `"#"`
- **Varianta výchozí**: `""`
- **Mapování**:
  - Produkt: Pevně `"#"`
  - Varianta: `f"{repaired.code}-V{variant_index:02d}"` (např. "PROD123-V01")

---

## 2. VARIANTA PARAMETRY (názvy a hodnoty)

### 4. `varianta1_nazev` (str)
- **Produkt výchozí**: `"#"`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"#"`
  - Varianta: `variant.key_value_pairs[0][0]` (klíč první vlastnosti) nebo `""`

### 5. `varianta1_hodnota` (str)
- **Produkt výchozí**: `"#"`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"#"`
  - Varianta: `variant.key_value_pairs[0][1]` (hodnota první vlastnosti) nebo `""`

### 6. `varianta2_nazev` (str)
- **Produkt výchozí**: `"#"`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"#"`
  - Varianta: `variant.key_value_pairs[1][0]` nebo `""`

### 7. `varianta2_hodnota` (str)
- **Produkt výchozí**: `"#"`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"#"`
  - Varianta: `variant.key_value_pairs[1][1]` nebo `""`

### 8. `varianta3_nazev` (str)
- **Produkt výchozí**: `"#"`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"#"`
  - Varianta: `variant.key_value_pairs[2][0]` nebo `""`

### 9. `varianta3_hodnota` (str)
- **Produkt výchozí**: `"#"`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"#"`
  - Varianta: `variant.key_value_pairs[2][1]` nebo `""`

### 10. `varianta_stejne` (str)
- **Produkt výchozí**: `"#"`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"#"`
  - Varianta: Pevně `"1"`

---

## 3. VIDITELNOST A STAV

### 11. `zobrazit` (int)
- **Produkt výchozí**: `1`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: `"1"` pokud `repaired.price > 0`, jinak `"0"`
  - Varianta: Pevně `"#"` (dědí z hlavního produktu)

### 12. `archiv` (int)
- **Produkt výchozí**: `0`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"0"`
  - Varianta: Pevně `"0"` (ne "#" jako ve výchozí hodnotě!)

---

## 4. KÓDY A IDENTIFIKÁTORY

### 13. `kod` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `""`
- **Mapování**:
  - Produkt: `repaired.code`
  - Varianta: `variant.variantcode` pokud existuje, jinak `f"{repaired.code}-V{variant_index:02d}"`

### 14. `kod_vyrobcu` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `""`
- **Mapování**: Zůstává prázdné `""`

### 15. `ean` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `""`
- **Mapování**: Zůstává prázdné `""`

### 16. `isbn` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Zůstává prázdné `""`
  - Varianta: Zůstává `"#"` (dědí)

---

## 5. NÁZEV A POPIS

### 17. `nazev` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: `repaired.name`
  - Varianta: `repaired.name` (stejný jako u hlavního produktu)

### 18. `privlastek` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**: Zůstává prázdné `""` pro produkt, `"#"` pro variantu

### 19. `vyrobce` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: `""` pokud je značka "Desaka", jinak `repaired.brand`
  - Varianta: Stejné jako produkt (pokud Desaka → `""`, jinak `repaired.brand`)

### 20. `dodavatel_id` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**: Zůstává prázdné `""` pro produkt, `"#"` pro variantu

---

## 6. CENY

### 21. `cena` (float)
- **Produkt výchozí**: `0.0`
- **Varianta výchozí**: `0.0`
- **Mapování**:
  - Produkt: `float(repaired.price)` nebo `0.0`
  - Varianta: `float(variant.current_price)` nebo `0.0`

### 22. `cena_bezna` (float)
- **Produkt výchozí**: `0.0`
- **Varianta výchozí**: `0.0`
- **Mapování**:
  - Produkt: `float(repaired.price_standard)` nebo použije hodnotu z `cena`
  - Varianta: `float(variant.basic_price)` nebo použije hodnotu z `cena`

### 23. `cena_nakupni` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `""`
- **Mapování**: Zůstává prázdné `""`

### 24. `recyklacni_poplatek` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**: Zůstává prázdné `""` pro produkt, `"#"` pro variantu

### 25. `dph` (int)
- **Produkt výchozí**: `0`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"21"`
  - Varianta: Pevně `"21"` (ne "#"!)

---

## 7. SLEVY

### 26. `sleva` (float)
- **Produkt výchozí**: `0.0`
- **Varianta výchozí**: `"#"`
- **Mapování**: Zůstává prázdné `""` pro produkt, `"#"` pro variantu

### 27. `sleva_od` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**: Zůstává prázdné `""` pro produkt, `"#"` pro variantu

### 28. `sleva_do` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**: Zůstává prázdné `""` pro produkt, `"#"` pro variantu

---

## 8. POPISY

### 29. `popis` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: `repaired.desc`
  - Varianta: `repaired.desc` (stejný jako hlavní produkt)

### 30. `popis_strucny` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: `repaired.shortdesc`
  - Varianta: `repaired.shortdesc` (stejný jako hlavní produkt)

---

## 9. ZOBRAZENÍ A KOŠÍK

### 31. `kosik` (int)
- **Produkt výchozí**: `1`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"1"`
  - Varianta: Pevně `"#"` (dědí)

### 32. `home` (int)
- **Produkt výchozí**: `0`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"0"`
  - Varianta: Pevně `"#"` (dědí)

---

## 10. DOSTUPNOST A SKLADEM

### 33. `dostupnost` (str)
- **Produkt výchozí**: `"#"`
- **Varianta výchozí**: `"."` (tečka!)
- **Mapování**:
  - Produkt: `"#"` pokud má varianty, jinak `"0"`
  - Varianta: Pevně `"-"` (minus, ne tečka!)

### 34. `doprava_zdarma` (int)
- **Produkt výchozí**: `0`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"0"`
  - Varianta: Pevně `"0"` (ne "#"!)

### 35. `dodaci_doba` (str)
- **Produkt výchozí**: `"#"`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"#"`
  - Varianta: Pevně `" "` (mezera!)

### 36. `dodaci_doba_auto` (str)
- **Produkt výchozí**: `"#"`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"1"`
  - Varianta: Pevně `"0"` (ne "#"!)

### 37. `sklad` (str)
- **Produkt výchozí**: `"#"`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: `"#"` pokud má varianty, jinak `"0"`
  - Varianta: Pevně `"0"` (ne "#"!)

### 38. `na_sklade` (str)
- **Produkt výchozí**: `"#"`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: `"#"` pokud má varianty, jinak `"0"`
  - Varianta: Pevně `"0"` (ne "#"!)

---

## 11. ROZMĚRY A HMOTNOST

### 39. `hmotnost` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `""`
- **Mapování**: Zůstává prázdné `""`

### 40. `delka` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `""`
- **Mapování**: Zůstává prázdné `""`

---

## 12. JEDNOTKY A ODBĚR

### 41. `jednotka` (str)
- **Produkt výchozí**: `"ks"`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"ks"`
  - Varianta: Pevně `"#"` (dědí)

### 42. `odber_po` (int)
- **Produkt výchozí**: `1`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"1"`
  - Varianta: Pevně `"#"` (dědí)

### 43. `odber_min` (int)
- **Produkt výchozí**: `1`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"1"`
  - Varianta: Pevně `"#"` (dědí)

### 44. `odber_max` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**: Zůstává prázdné `""` pro produkt, `"#"` pro variantu

### 45. `pocet` (int)
- **Produkt výchozí**: `1`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"1"`
  - Varianta: Pevně `"#"` (dědí)

### 46. `zaruka` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**: Zůstává prázdné `""` pro produkt, `"#"` pro variantu

---

## 13. MARŽE A DODAVATEL

### 47. `marze_dodavatel` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**: Zůstává prázdné `""` pro produkt, `"#"` pro variantu

### 48. `cena_dodavatel` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `""`
- **Mapování**: Zůstává prázdné `""`

---

## 14. SEO

### 49. `seo_titulek` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**: Zůstává prázdné `""` pro produkt, `"#"` pro variantu

### 50. `seo_popis` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**: Zůstává prázdné `""` pro produkt, `"#"` pro variantu

---

## 15. PŘÍZNAKY (FLAGS)

### 51. `eroticke` (int)
- **Produkt výchozí**: `0`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"0"`
  - Varianta: Pevně `"0"` (ne "#"!)

### 52. `pro_dospele` (int)
- **Produkt výchozí**: `0`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"0"`
  - Varianta: Pevně `"0"` (ne "#"!)

### 53. `slevovy_kupon` (int)
- **Produkt výchozí**: `1`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"1"`
  - Varianta: Pevně `"1"` (ne "#"!)

### 54. `darek_objednavka` (int)
- **Produkt výchozí**: `1`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"1"`
  - Varianta: Pevně `"1"` (ne "#"!)

### 55. `priorita` (int)
- **Produkt výchozí**: `0`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"0"`
  - Varianta: Pevně `"0"` (ne "#"!)

---

## 16. POZNÁMKY A DODAVATEL

### 56. `poznamka` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**: Zůstává prázdné `""` pro produkt, `"#"` pro variantu

### 57. `dodavatel_kod` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `""`
- **Mapování**: Zůstává prázdné `""`

### 58. `stitky` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: `repaired.zbozi_keywords`
  - Varianta: Pevně `"#"` (nedědí)

---

## 17. KATEGORIE A SOUVISLOSTI

### 59. `kategorie_id` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: `repaired.category_ids`
  - Varianta: Pevně `"#"` (nedědí)

### 60. `podobne` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**: Zůstává prázdné `""` pro produkt, `"#"` pro variantu

### 61. `prislusenstvi` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**: Zůstává prázdné `""` pro produkt, `"#"` pro variantu

### 62. `variantove` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Seznam kódů variant oddělených čárkou, např. `"PROD-V01,PROD-V02,PROD-V03"`, nebo prázdné pokud žádné varianty
  - Varianta: Pevně `"#"` (nedědí)

### 63. `zdarma` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**: Zůstává prázdné `""` pro produkt, `"#"` pro variantu

### 64. `sluzby` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**: Zůstává prázdné `""` pro produkt, `"#"` pro variantu

### 65. `rozsirujici_obsah` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**: Zůstává prázdné `""` pro produkt, `"#"` pro variantu

---

## 18. ZBOZI.CZ (Vlastnosti 66-74)

### 66. `zbozicz_skryt` (int)
- **Produkt výchozí**: `0`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"0"`
  - Varianta: Pevně `"0"` (ne "#"!)

### 67. `zbozicz_productname` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: `repaired.name`
  - Varianta: Pevně `"#"` (nedědí)

### 68. `zbozicz_product` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: `repaired.name`
  - Varianta: Pevně `"#"` (nedědí)

### 69. `zbozicz_cpc` (int)
- **Produkt výchozí**: `5`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"5"`
  - Varianta: Pevně `"5"` (ne "#"!)

### 70. `zbozicz_cpc_search` (int)
- **Produkt výchozí**: `5`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"5"`
  - Varianta: Pevně `"5"` (ne "#"!)

### 71. `zbozicz_kategorie` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: `repaired.zbozi_category`
  - Varianta: Pevně `"#"` (nedědí)

### 72. `zbozicz_stitek_0` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: První keyword z `repaired.zbozi_keywords.split(',')[0]`
  - Varianta: Pevně `"#"` (nedědí)

### 73. `zbozicz_stitek_1` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Druhý keyword z `repaired.zbozi_keywords.split(',')[1]`
  - Varianta: Pevně `"#"` (nedědí)

### 74. `zbozicz_extra` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**: Zůstává prázdné `""` pro produkt, `"#"` pro variantu

---

## 19. HEUREKA.CZ (Vlastnosti 75-79)

### 75. `heurekacz_skryt` (int)
- **Produkt výchozí**: `0`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"0"`
  - Varianta: Pevně `"0"` (ne "#"!)

### 76. `heurekacz_productname` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: `repaired.name`
  - Varianta: Pevně `"#"` (nedědí)

### 77. `heurekacz_product` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: `repaired.name`
  - Varianta: Pevně `"#"` (nedědí)

### 78. `heurekacz_cpc` (int)
- **Produkt výchozí**: `1`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"1"`
  - Varianta: Pevně `"1"` (ne "#"!)

### 79. `heurekacz_kategorie` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: `repaired.heureka_category`
  - Varianta: Pevně `"#"` (nedědí)

---

## 20. GOOGLE (Vlastnosti 80-86)

### 80. `google_skryt` (int)
- **Produkt výchozí**: `0`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"0"`
  - Varianta: Pevně `"0"` (ne "#"!)

### 81. `google_kategorie` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: `repaired.google_category`
  - Varianta: Pevně `"#"` (nedědí)

### 82. `google_stitek_0` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: První keyword z `repaired.google_keywords.split(',')[0]`
  - Varianta: Pevně `"#"` (nedědí)

### 83. `google_stitek_1` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Druhý keyword z `repaired.google_keywords.split(',')[1]`
  - Varianta: Pevně `"#"` (nedědí)

### 84. `google_stitek_2` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Třetí keyword z `repaired.google_keywords.split(',')[2]`
  - Varianta: Pevně `"#"` (nedědí)

### 85. `google_stitek_3` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Čtvrtý keyword z `repaired.google_keywords.split(',')[3]`
  - Varianta: Pevně `"#"` (nedědí)

### 86. `google_stitek_4` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pátý keyword z `repaired.google_keywords.split(',')[4]`
  - Varianta: Pevně `"#"` (nedědí)

---

## 21. GLAMI (Vlastnosti 87-92)

### 87. `glami_skryt` (int)
- **Produkt výchozí**: `0`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"0"`
  - Varianta: Pevně `"0"` (ne "#"!)

### 88. `glami_kategorie` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: `repaired.glami_category`
  - Varianta: Pevně `"#"` (nedědí)

### 89. `glami_cpc` (int)
- **Produkt výchozí**: `1`
- **Varianta výchozí**: `"#"`
- **Mapování**:
  - Produkt: Pevně `"1"`
  - Varianta: Pevně `"1"` (ne "#"!)

### 90. `glami_voucher` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**: Zůstává prázdné `""` pro produkt, `"#"` pro variantu

### 91. `glami_material` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**: Zůstává prázdné `""` pro produkt, `"#"` pro variantu

### 92. `glamisk_material` (str)
- **Produkt výchozí**: `""`
- **Varianta výchozí**: `"#"`
- **Mapování**: Zůstává prázdné `""` pro produkt, `"#"` pro variantu

---

## 22. SKLAD (Vlastnosti 93-96)

### 93. `sklad_umisteni` (str)
- **Produkt výchozí**: `"#"`
- **Varianta výchozí**: `""`
- **Mapování**:
  - Produkt: Pevně `"#"`
  - Varianta: Pevně `"#"` (ne ""!)

### 94. `sklad_minimalni` (str)
- **Produkt výchozí**: `"#"`
- **Varianta výchozí**: `""`
- **Mapování**:
  - Produkt: Pevně `"#"`
  - Varianta: Pevně `"#"` (ne ""!)

### 95. `sklad_optimalni` (str)
- **Produkt výchozí**: `"#"`
- **Varianta výchozí**: `""`
- **Mapování**:
  - Produkt: Pevně `"#"`
  - Varianta: Pevně `"#"` (ne ""!)

### 96. `sklad_maximalni` (str)
- **Produkt výchozí**: `"#"`
- **Varianta výchozí**: `""`
- **Mapování**:
  - Produkt: Pevně `"#"`
  - Varianta: Pevně `"#"` (ne ""!)

---

## Souhrnné poznámky

### Důležité rozdíly mezi výchozími hodnotami a mapováním

U mnoha vlastností variant se **skutečně nastavená hodnota liší od výchozí**:

| Vlastnost | Výchozí hodnota varianty | Skutečně nastavená hodnota |
|-----------|--------------------------|----------------------------|
| `archiv` | `"#"` | `"0"` |
| `dostupnost` | `"."` (tečka) | `"-"` (minus) |
| `doprava_zdarma` | `"#"` | `"0"` |
| `dodaci_doba` | `"#"` | `" "` (mezera) |
| `dodaci_doba_auto` | `"#"` | `"0"` |
| `sklad` | `"#"` | `"0"` |
| `na_sklade` | `"#"` | `"0"` |
| `dph` | `"#"` | `"21"` |
| Všechny flagy (`eroticke`, `pro_dospele`, atd.) | `"#"` | konkrétní hodnoty (`"0"`, `"1"`) |
| Všechny `*_skryt` | `"#"` | `"0"` |
| Všechny `*_cpc` | `"#"` | konkrétní hodnoty (`"5"`, `"1"`) |
| Všechny `sklad_*` | `""` | `"#"` |

### Speciální chování vlastnosti "Desaka"

Pokud `repaired.brand` obsahuje "Desaka" (ověřováno pomocí `_is_desaka_brand()`), pak se `vyrobce` nastaví na prázdný řetězec `""` místo názvu značky.

### Zpracování variant klíčů

Varianta může mít až 3 páry klíč-hodnota (`key_value_pairs`), které se mapují do:
- `varianta1_nazev` / `varianta1_hodnota`
- `varianta2_nazev` / `varianta2_hodnota`
- `varianta3_nazev` / `varianta3_hodnota`

### Generování variant kódů

Pokud varianta nemá vlastní `variantcode`, generuje se automaticky ve formátu:
`{kod_hlavniho_produktu}-V{cislo_varianty:02d}`

Např: `"BUTTERFLY-123-V01"`, `"BUTTERFLY-123-V02"`, atd.

### Seznam variant kódů v hlavním produktu

Vlastnost `variantove` v hlavním produktu obsahuje čárkou oddělený seznam všech kódů variant:
`"BUTTERFLY-123-V01,BUTTERFLY-123-V02,BUTTERFLY-123-V03"`

---

## Zdrojové soubory

- **Definice tříd**: `desaka_unifier/unifierlib/export_product.py`
  - `ExportProduct` (řádky 7-146) - základní třída
  - `ExportMainProduct` (řádky 149-197) - hlavní produkt s výchozími hodnotami
  - `ExportProductVariant` (řádky 199-291) - varianta s výchozími hodnotami

- **Převodní logika**: `desaka_unifier/unifierlib/parser.py`
  - `repaired_to_export_product()` (řádek 1700) - hlavní funkce převodu
  - `_create_main_export_product_complete()` (řádky 1825-2016) - převod hlavního produktu
  - `_create_variant_export_product_complete()` (řádky 2018-2228) - převod variant

---

*Report vygenerován: 2025-11-10*
*Analyzováno 96 vlastností ExportProduct*
