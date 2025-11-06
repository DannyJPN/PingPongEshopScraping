# Souhrnný Report - Memory Issues

**Datum vytvoření:** 2025-10-12
**Vytvořeno Issues:** 14
**Celkový počet chybějících záznamů:** 8,902
**Poznámka:** 11 duplicitních issues (#65-#77 kromě #71 a #73) bylo zavřeno

---

## Přehled podle Memory souborů

### ProductBrandMemory_CS.csv (5 issues, 906 záznamů)

| # | E-shop | Počet chybějících | Issue URL |
|---|--------|-------------------|-----------|
| 1 | Nittaku | 29 | https://github.com/DannyJPN/PingPongEshopScraping/issues/53 |
| 2 | SpinWay | 261 | https://github.com/DannyJPN/PingPongEshopScraping/issues/54 |
| 3 | SportSpin | 427 | https://github.com/DannyJPN/PingPongEshopScraping/issues/55 |
| 4 | Stoten | 51 | https://github.com/DannyJPN/PingPongEshopScraping/issues/56 |
| 5 | VseNaStolniTenis | 138 | https://github.com/DannyJPN/PingPongEshopScraping/issues/57 |

**Pravidlo:** Značky (brands) se NEPŘEKLÁDAJÍ - zůstává název výrobce v originále.

---

### ProductModelMemory_CS.csv (5 issues, 5,322 záznamů)

| # | E-shop | Počet chybějících | Issue URL |
|---|--------|-------------------|-----------|
| 6 | Nittaku | 108 | https://github.com/DannyJPN/PingPongEshopScraping/issues/58 |
| 7 | SpinWay | 802 | https://github.com/DannyJPN/PingPongEshopScraping/issues/59 |
| 8 | Stoten | 1,186 | https://github.com/DannyJPN/PingPongEshopScraping/issues/60 |
| 9 | SportSpin | 1,168 | https://github.com/DannyJPN/PingPongEshopScraping/issues/71 |
| 10 | VseNaStolniTenis | 2,058 | https://github.com/DannyJPN/PingPongEshopScraping/issues/73 |

**Pravidlo:** Model se obvykle NEPŘEKLÁDÁ - zůstává originální název (Hurricane 3, Tenergy 05, atd.).

---

### ProductTypeMemory_CS.csv (4 issues, 1,674 záznamů)

| # | E-shop | Počet chybějících | Issue URL |
|---|--------|-------------------|-----------|
| 11 | SpinWay | 3 | https://github.com/DannyJPN/PingPongEshopScraping/issues/61 |
| 12 | SportSpin | 499 | https://github.com/DannyJPN/PingPongEshopScraping/issues/62 |
| 13 | Stoten | 346 | https://github.com/DannyJPN/PingPongEshopScraping/issues/63 |
| 14 | VseNaStolniTenis | 826 | https://github.com/DannyJPN/PingPongEshopScraping/issues/64 |

**Pravidlo:** Typ MUSÍ být ČESKY! ("Potah" ne "Rubber", "Dřevo" ne "Blade", "Míček" ne "Ball").

---

## Kritické pravidlo pro všechny Issues

```
KEY (klíč)      = Originální jazyk a podoba (z eshopu)
VALUE (hodnota) = VŽDY ČESKY! (soubor končí _CS.csv)
```

## Statistiky podle e-shopů

| E-shop | ProductBrand | ProductModel | ProductType | **Celkem** |
|--------|--------------|--------------|-------------|------------|
| **Nittaku** | 29 | 108 | - | **137** |
| **SpinWay** | 261 | 802 | 3 | **1,066** |
| **SportSpin** | 427 | 1,168 | 499 | **2,094** |
| **Stoten** | 51 | 1,186 | 346 | **1,583** |
| **VseNaStolniTenis** | 138 | 2,058 | 826 | **3,022** |
| **CELKEM** | **906** | **5,322** | **1,674** | **8,902** |

*(Poznámka: Nittaku nemá ProductType issues, protože všechny typy už byly doplněny)*

---

## Prioritizace podle obtížnosti

### ✅ Rychlé úkoly (< 100 položek)
- #53 Nittaku ProductBrandMemory (29)
- #56 Stoten ProductBrandMemory (51)
- #61 SpinWay ProductTypeMemory (3)

### ⚠️ Střední úkoly (100-500 položek)
- #58 Nittaku ProductModelMemory (108)
- #57 VseNaStolniTenis ProductBrandMemory (138)
- #54 SpinWay ProductBrandMemory (261)
- #63 Stoten ProductTypeMemory (346)
- #55 SportSpin ProductBrandMemory (427)
- #62 SportSpin ProductTypeMemory (499)

### 🔴 Velké úkoly (500+ položek)
- #59 SpinWay ProductModelMemory (802)
- #64 VseNaStolniTenis ProductTypeMemory (826)
- #71 SportSpin ProductModelMemory (1,168)
- #60 Stoten ProductModelMemory (1,186)
- #73 VseNaStolniTenis ProductModelMemory (2,058) ⚠️ **NEJVĚTŠÍ**

---

## Užitečné zdroje pro všechny úkoly

### České a slovenské e-shopy
- https://pincesobchod.cz - **hlavní zdroj** pro stolní tenis
- https://www.stoten.cz
- https://www.sportspin.cz
- https://www.vsenastolnitenis.cz
- https://www.spinway.sk

### Oficiální stránky výrobců
- https://nittaku.com | https://nittaku.tt
- https://butterfly.tt | https://butterfly-global.com
- https://tibhar.com | https://tibhar.de
- https://xiom.eu | https://xiom.global
- https://yasaka-jp.com
- https://victas.com
- https://joola.com
- https://donic.com
- https://andro.de
- https://gewo-tt.com

### Konfigurační soubory
- `desaka_unifier/Memory/BrandCodeList.csv` - seznam známých značek
- `desaka_unifier/Memory/CategoryCodeList.csv` - kategorie produktů

---

## Postup zpracování Issues

1. **Přečíst MISSING soubor** (UTF-16 LE encoding)
2. **Pro každý klíč:**
   - Zachovat KEY v originální podobě
   - Určit VALUE v češtině (podle typu memory)
   - Vyhledat informace na webu (pincesobchod.cz, výrobci)
   - Použít existující záznamy jako referenci
3. **Doplnit do CSV:**
   ```csv
   "ORIGINÁLNÍ_KEY","ČESKÁ_VALUE"
   ```
4. **Zachovat formát:** CSV s uvozovkami, kódování UTF-8

---

## Stolní tenis terminologie (pro ProductType)

```
"rubber" = "Potah" (NIKDY "Guma"!)
"blade" = "Dřevo" (NIKDY "Čepel"!)
"ball" = "Míček"
"paddle/racket" = "Pálka"
"case" = "Pouzdro"
"cleaner" = "Čistič"
"glue" = "Lepidlo"
"sponge" = "Houba"
"shirt" = "Tričko" / "Dres"
"shorts" = "Kraťasy"
"shoes" = "Boty"
"bag" = "Taška"
"net" = "Síťka"
"table" = "Stůl"
```

---

**Generováno pomocí:** `MISSINGDETECTOR.ps1` a `create_issues.py`
**GitHub Repository:** https://github.com/DannyJPN/PingPongEshopScraping
