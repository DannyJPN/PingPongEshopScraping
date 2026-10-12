# Pincesobchod – kontrola CZ vs SK a kontroly v rámci e-shopu

Sada skriptů nad JSON exporty Pincesobchodu (`Pincesobchod_CS.json` a `Pincesobchod_SK.json`).
Hledají rozpory mezi CZ a SK e-shopem a také nekonzistence uvnitř každého e-shopu
(např. cena vs. cena běžná, název vs. SEO titulek a titulky ve feedech).

* **Jeden skript pro každou vlastnost** – `check_<vlastnost>.py`
* **Hromadný skript** – `check_all.py` (libovolná kombinace kontrol, souhrnný report)
* **Kontroly v rámci jednoho e-shopu** – `check_shop_all.py` (skupina `shop`, CZ i SK zvlášť)
* **OpenAI vizuální kontrola fotek** – `check_photos_vision.py` (vybrané produkty)
  a `check_photos_vision_all.py` (všechny produkty)

Všechny skripty používají **stejný formát reportu**, takže dílčí reporty jsou podmnožinou
hromadného.

## Zdroje dat (`--pullnewest`)

Bez přepínače skript najde nejnovější `Full_<dd.mm.yyyy>/Pincesobchod_<LANG>.json`
ve složkách downloaderu (výchozí `H:/Desaka/Pincesobchod_CS` a `H:/Desaka/Pincesobchod_SK`,
mění se `--cs-dir` / `--sk-dir`).

S `--pullnewest` se JSONy nejdřív stáhnou **mechanismem pincesobchod downloaderu**
(`API_URL_PATTERN` z `pincesobchodlib/constants.py`, `shared/json_downloader.py`) do dnešní
složky `Full_<datum>`. Potřebné proměnné prostředí: `JZ_BEARER_TOKEN_CS`, `JZ_BEARER_TOKEN_SK`.

Konkrétní soubory lze zadat přes `--cs-json` / `--sk-json`.

`--active-only` omezí porovnání na produkty, které jsou aspoň na jedné straně aktivní
(viditelné a nearchivované).

## Identita

* **Produkt** = kód (`catalogNumber`) + název (`translations.*.name`). Produkty se stejným kódem
  a jiným názvem nejsou stejný produkt (nahlásí je kontrola `identity`).
* **Varianta** = kód + variantní parametry (`options`: název + hodnota, např. `Barva=černá,
  Velikost=XL`). Varianta se stejnými parametry musí mít v CZ i SK stejný kód.

Ostatní kontroly porovnávají jen spárované produkty / varianty.

## Kontroly

Seznam všech kontrol: `python check_all.py --list-checks`.

| skupina | kontroly | pravidlo |
|---|---|---|
| identity | `identity` | produkty jen v CZ / jen v SK, stejný kód s jiným názvem, duplicitní kódy |
| product | `guid`, `ean`, `visibility`, `archive`, `feeds`, `categories`, … (každá vlastnost zvlášť) | stejná hodnota v CZ i SK (u vnořených hodnot report vypíše, které podčásti se liší) |
| product | `translations_nameext`, `translations_slug`, `translations_metaTitle`, `translations_metaDescription`, `translations_annotation`, `translations_description` | stejný text |
| product | `other_fields` | vlastnosti, které API přidá a žádná jiná kontrola je nezná |
| price | `price`, `standardPrice` | přepočet CZ → SK dle značky (viz níže) |
| variant | `variants` | identita variant: jen v CZ / jen v SK, jiný kód, jiné parametry, duplicitní parametry |
| variant | `variant_<vlastnost>` | stejná hodnota u každé spárované varianty |
| variant | `variant_price`, `variant_standardPrice` | přepočet CZ → SK i pro varianty (cena varianty `null` = cena produktu) |
| images | `images_path` | počet, pořadí, cesty a hlavní fotka (cesta URL bez domény .cz/.sk) |
| images | `images_hash` | obsah fotek (SHA-256), fotky se stahují do cache `--image-cache-dir` |
| vision | `vision` | OpenAI: zobrazuje fotka produkt / souvisí s ním? (ve výchozím stavu vypnuto) |
| shop | viz níže | kontroly v rámci jednoho e-shopu |

### Kontroly v rámci jednoho e-shopu (skupina `shop`)

Každá kontrola běží zvlášť pro CZ i SK JSON (`--sides cs|sk|both`, výchozí oba) a kontroluje
všechny produkty daného e-shopu (nejen spárované). Pravidla byla ověřena na skutečných exportech –
platí pro 90–100 % produktů, zbytek jsou kandidáti na chybu.

| kontrola | pravidlo |
|---|---|
| `vat` | sazba DPH: CZ 21 %, SK 23 % |
| `price_vat`, `variant_price_vat` | cena běžná = cena × (1 + DPH), tolerance 0,1 |
| `shop_name_metaTitle` | název produktu je zkopírován do SEO titulku (`translations.metaTitle`) |
| `shop_name_heurekacs_productname`, `shop_name_heurekacs_product` | název produktu = titulek pro Heureku |
| `shop_name_zbozi_productname`, `shop_name_zbozi_product` | název produktu = titulek pro Zboží |
| `shop_metaDescription` | SEO popis (`metaDescription`) = anotace (`annotation`) |
| `shop_slug` | URL (`slug`) = název bez diakritiky, malými písmeny, oddělený pomlčkami |
| `shop_feed_category` | kategorie je ve všech feedech stejná a rovná se nejhlubší kategorii produktu (`Potahy>Softy>Softy OFF`); prázdná kategorie feedu se ignoruje |
| `shop_feed_cpc` | CPC je ve všech feedech stejné (warning) |
| `shop_images` | právě jedna hlavní fotka, je na 1. pozici, pozice 1..n, žádná fotka dvakrát |
| `shop_variant_codes` | kód varianty = `<kód produktu>-NN`, kódy variant jsou v e-shopu unikátní |
| `shop_brand_in_name` | název produktu obsahuje značku výrobce (warning) |

Kopie názvu se porovnávají přesně (rozdíl ve velikosti písmen je chyba), ignorují se jen mezery
navíc. Prázdný titulek je warning. Pokud titulek ve feedu obsahuje starý SEO titulek, report to uvede.

Interní ID produktu a varianty (`id`) se **nekontrolují** – mezi CZ a SK se mohou lišit.

Prázdné hodnoty (`null`, `""`, `[]`, `{}`) se považují za shodné, pořadí položek v seznamech se
ignoruje, desetinná čísla `320.0` a `320` jsou shodná.

### Ceny

* `price` = cena bez DPH, `standardPrice` = cena běžná (s DPH). Platí
  `standardPrice = price × (1 + DPH)`, DPH CZ 21 %, SK 23 % (`--vat-cs`, `--vat-sk`).
* Přepočet CZ → SK (jen uvedené značky, ostatní ceny se nekontrolují – v reportu `not_applicable`):

  | značka | kategorie | sleva |
  |---|---|---|
  | Butterfly | vše | 5 % |
  | Andro | Potahy, Dřeva | 5 % |
  | Stiga | Potahy | 5 % |
  | Tibhar | vše | 5 % |
  | Victas | Potahy, Dřeva | 10 % |

  `SK standardPrice = CZ standardPrice / 25 × (1 − sleva)`;
  `SK price = CZ price × 1,21 / 25 × (1 − sleva) / 1,23`.
  Kategorie se určuje podle kořene hlavní kategorie CZ produktu. Tolerance přepočtů je 0,1
  (`--tolerance`), kurz `--czk-per-eur` (výchozí 25).

## Spuštění

```bash
cd pincesobchoddownloader/cs_sk_compare

# jedna vlastnost
python check_visibility.py
python check_standardPrice.py --pullnewest

# všechno (kromě drahé OpenAI kontroly)
python check_all.py

# jen vybrané kontroly / skupiny, vypnutí jednotlivých kontrol
python check_all.py --only identity variants price standardPrice
python check_all.py --group price images

# jen kontroly v rámci e-shopu (CZ i SK), případně jen SK
python check_shop_all.py
python check_shop_all.py --sides sk --no-shop_brand_in_name
python check_shop_name_metaTitle.py --sides cs
python check_all.py --no-guid --no-updatedAt --no-images_hash
python check_all.py --skip feeds categories

# včetně OpenAI kontroly fotek (jen 100 produktů značky Butterfly)
python check_all.py --vision --vision-brands Butterfly --vision-limit 100
```

## OpenAI vizuální kontrola fotek

Model posoudí každou fotku produktu podle názvu, kódu, značky a kategorie:

* `product` – fotka zobrazuje produkt,
* `related` – souvisí s produktem (např. velikostní tabulka u textilu, technologie, logo řady),
* `unrelated` – jiný produkt / nesouvisející obsah → **error**,
* `unclear` – nelze rozhodnout (rozbitá fotka, placeholder) → **warning**.

```bash
# vybrané produkty
python check_photos_vision.py --codes BTY01000001 AND01000044

# všechny produkty – nejdřív odhad, kolik fotek se pošle
python check_photos_vision_all.py --dry-run --active-only
python check_photos_vision_all.py --active-only --limit 200 --max-images 4
```

* Potřebuje `OPENAI_API_KEY` a balíček `openai`.
* Model: `--model` (v `check_all.py` `--vision-model`), případně proměnná
  `PINCESOBCHOD_VISION_MODEL`; výchozí `gpt-4o`.
* Výsledky se ukládají do `vision_cache.jsonl` v `--output-dir` (`--cache`), opakovaný běh
  už zaplacené fotky znovu neposílá (`--refresh` vynutí nové vyhodnocení).
* `--detail low` (výchozí) je nejlevnější. `--embed-images` posílá fotky jako base64
  (když OpenAI nemá přístup na URL e-shopu).
* `--side cs|sk|both` – které JSONy kontrolovat (výchozí CZ).

## Report

Každý běh zapíše do `--output-dir` (výchozí `H:/Desaka/Reports/Pincesobchod/CsSk`):

* `<název>_<čas>.json` – strojově čitelný (schema `pincesobchod-cs-sk-report/1`),
* `<název>_<čas>.csv` – jeden nález na řádek (oddělovač `;`, otevře se v Excelu),
* `<název>_<čas>.txt` – lidsky čitelný: zdroje, párování, souhrnná tabulka kontrol, nálezy
  seskupené podle kontroly (stejný text se vypíše na konzoli; `--quiet` vypíše jen souhrn,
  `--max-text-items N` zkrátí výpis, JSON/CSV jsou vždy kompletní).

Struktura JSON:

```json
{
  "schema": "pincesobchod-cs-sk-report/1",
  "generated_at": "2026-10-12T08:46:54",
  "checks": ["identity", "visibility"],
  "sources": {"cs": {"path": "...", "products": 3900}, "sk": {"path": "...", "products": 3968}},
  "pairing": {"matched": 3894, "cs_only": 4, "sk_only": 72, "name_conflicts": 2, "duplicate_codes_cs": 0, "duplicate_codes_sk": 0},
  "options": {"active_only": false, "sides": "both", "tolerance": 0.1, "vat": {"cs": 21.0, "sk": 23.0}, "czk_per_eur": 25.0},
  "summary": {
    "total_findings": 1,
    "by_severity": {"error": 1},
    "by_check": {"visibility": {"title": "...", "findings": 1, "checked": 3894}}
  },
  "findings": [
    {"check": "visibility", "property": "visibility", "message": "Hodnota se v CZ a SK liší",
     "product_code": "AND01000001", "product_name": "...", "severity": "error", "side": "both",
     "variant_code": "", "variant_options": "", "cs_value": true, "sk_value": false, "expected": null}
  ]
}
```

`side` říká, které straně se nález týká (`cs`, `sk`, `both`), `expected` je očekávaná hodnota
u cenových pravidel, `details` doplňkové údaje (např. seznam rozdílných podčástí).

Návratový kód: `0` bez nálezů, `1` nalezeny rozdíly, `2` chyba (např. chybějící JSON).

## Testy

```bash
cd pincesobchoddownloader/cs_sk_compare
pip install -r requirements.txt
python -m pytest tests
```
