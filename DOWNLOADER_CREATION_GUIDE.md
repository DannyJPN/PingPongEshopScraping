# KOMPLEXNÍ PRŮVODCE TVORBOU NOVÝCH DOWNLOADERŮ

## Účel dokumentu

Tento dokument poskytuje **kompletní specifikaci** pro vytvoření nových downloaderů pro Desaka systém. Obsahuje:
- Seznam všech požadovaných e-shopů z GitHub issues
- **PŘESNÉ** instrukce, které části kódu musí být IDENTICKÉ s existujícími downloadery
- **PŘESNÉ** instrukce, které části musí být přizpůsobeny pro každý e-shop
- Jmenné konvence, strukturu složek, formát výsledků
- Explicitní instrukce pro web scraping

**KRITICKY DŮLEŽITÉ**: Části označené jako **IDENTICKÉ** nebo **MANDATORY** musí být implementovány PŘESNĚ podle specifikace bez jakýchkoliv změn!

---

## 1. SEZNAM CÍLOVÝCH E-SHOPŮ (Z GITHUB ISSUES)

**Celkem: 45 GitHub issues pro nové downloadery**

### HIGH PRIORITY - Major Brands (11 e-shopů)

| Issue # | Brand | URL | Jazyk | Poznámka |
|---------|-------|-----|-------|----------|
| #10 | Butterfly | https://butterfly.tt | Multi | Hlavní brand, komplexní e-shop |
| #16 | Der Materialspezialist | https://der-materialspezialist.com | DE/EN | Specialist na defensive equipment |
| #19 | Donic | https://donic.com | DE | Německý major brand |
| #20 | Dr. Neubauer | https://drneubauer.com | EN | Specializované defensive vybavení |
| #28 | Joola | https://joola.com | EN | Major brand (US market, Shopify) |
| #40 | Stiga | https://stigasports.com | SV/EN | Švédský major brand |
| #42 | Tibhar | https://tibhar.info | DE/EN/FR | Evropský brand od 1969 |
| #47 | Victas | https://victas.com | EN/JP | Japonský brand (SSL cert issues) |
| #48 | Xiom | https://xiom.eu | EN/Multi | Populární moderní brand |
| #49 | Yasaka | https://yasaka-jp.com | EN/JP | Japonský brand (connection issues) |
| #14 | DHS | https://dhs-sports.com | EN/CN | Čínský major brand |

### MEDIUM PRIORITY - Established Brands (22 e-shopů)

| Issue # | Brand | URL | Jazyk | Poznámka |
|---------|-------|-----|-------|----------|
| #5 | Andro | https://andro.de | DE/EN | Německý brand |
| #7 | Avalox | https://avalox.com | EN/SV | Švédský brand |
| #13 | Cornilleau | https://cornilleau.com | FR/EN | Specialista na stoly |
| #15 | Dawei | https://daweisports.com | EN/CN | Defensive equipment |
| #17 | Desaka | https://desaka.cz | CS | Lokální český brand |
| #18 | Dingo Swiss | https://dingyitt.com | EN/DE | Švýcarský brand |
| #22 | Friendship (729) | https://en.729sports.com | EN/CN | Affordable brand |
| #23 | Gambler | https://gamblertt.com/shop/ | EN | Gambler brand |
| #24 | Giant Dragon | https://giant-dragon.com | EN/CN | Čínský výrobce od 1991 |
| #26 | Hallmark | https://hallmarktabletennis.co.uk | EN | UK brand (connection issues) |
| #27 | Hanno | https://hanno-tischtennis.de/en/ | DE/EN | Německý brand |
| #31 | Lion | https://lionmfg.com | EN | Lion Manufacturing |
| #33 | Mizuno | https://mizuno.com | EN | Shoes/apparel focus |
| #34 | Nexy | https://nexy.com | EN | Nexy brand |
| #35 | Palio | https://palioett.com | EN | Palio brand |
| #36 | PimplePark | https://pimplepark.com | EN/DE | Pimpled rubbers specialist |
| #37 | Sanwei | https://sanweisport.com | EN/CN | Multiple domains |
| #38 | Sauer&Troeger | https://sauer-troeger.com | DE/EN | Německý brand |
| #39 | Spinlord | https://spinlord-tt.de | DE/EN | Německý online shop |
| #41 | Sword | https://swordtt.com | EN | Sword brand |
| #43 | TSP | https://victas.com | EN/JP | Part of Victas catalog |
| #46 | Tuttle | https://tuttle-tabletennis.com | EN | Website under development |

### LOW PRIORITY - Needs Research / No Official Site (12 e-shopů)

| Issue # | Brand | URL | Jazyk | Poznámka |
|---------|-------|-----|-------|----------|
| #6 | Asics | https://asics.com | EN | No dedicated TT products |
| #8 | Barna | via Der Materialspezialist | DE/EN | Product line within DMS |
| #9 | Bomb | TBD | TBD | No official website, may be 729 line |
| #11 | Carlton | https://carlton-sports.com | EN | Possible typo/duplicate of #12 |
| #12 | Cartlon | https://carlton-sports.com | EN | Possible typo/duplicate of #11 |
| #21 | Exacto | TBD | TBD | No official website found |
| #25 | Globe | TBD | TBD | No official e-shop |
| #29 | KTL | TBD | TBD | No official e-shop |
| #30 | Lear | TBD | TBD | Verification needed |
| #32 | Milky Way | TBD | TBD | Yinhe/Galaxy related |
| #44 | Tuning | TBD | TBD | No official website |
| #45 | Turnier | TBD | TBD | No official website |

### POZNÁMKY K E-SHOPŮM

**Technické problémy**:
- **Victas** (#47): SSL certificate issues
- **Yasaka** (#49): Connection issues
- **Hallmark** (#26): Connection issues

**Multi-domain brands**:
- **Sanwei** (#37): Má více domén, vyžaduje research

**Product lines (ne samostatné e-shopy)**:
- **Barna** (#8): Je součástí Der Materialspezialist
- **TSP** (#43): Je součástí Victas katalogu
- **Bomb** (#9): Možná součást 729

**Vyžaduje další research**:
- **Carlton/Cartlon** (#11, #12): Možné duplikáty, clarify
- **Low priority** e-shopy: Ověřit existenci oficiálních e-shopů

---

## 2. ARCHITEKTURA DOWNLOADERU - POVINNÁ STRUKTURA

### STRUKTURA SLOŽEK A SOUBORŮ (IDENTICKÁ PRO VŠECHNY)

```
{brand}downloader/                          # Název složky: lowercase + "downloader"
│
├── {brand}_downloader.py                   # Hlavní spustitelný soubor
│
├── {brand}lib/                             # Site-specific knihovna
│   ├── constants.py                        # PŘIZPŮSOBIT
│   ├── category_link_extractor.py          # PŘIZPŮSOBIT
│   ├── category_pages_link_extractor.py    # PŘIZPŮSOBIT
│   ├── product_detail_link_extractor.py    # PŘIZPŮSOBIT
│   ├── product_attribute_extractor.py      # PŘIZPŮSOBIT
│   └── product_variant_detail_link_extractor.py  # VOLITELNÉ - jen pokud e-shop má separátní URLs pro varianty
│
└── shared/                                 # Společné moduly - IDENTICKÉ
    ├── category_firstpage_downloader.py    # KOPÍROVAT BEZ ZMĚN
    ├── category_pages_downloader.py        # KOPÍROVAT BEZ ZMĚN
    ├── directory_manager.py                # KOPÍROVAT BEZ ZMĚN
    ├── html_loader.py                      # KOPÍROVAT BEZ ZMĚN
    ├── image_downloader.py                 # KOPÍROVAT BEZ ZMĚN
    ├── logging_config.py                   # KOPÍROVAT BEZ ZMĚN
    ├── main_page_downloader.py             # KOPÍROVAT BEZ ZMĚN
    ├── product_detail_page_downloader.py   # KOPÍROVAT BEZ ZMĚN
    ├── product_detail_variant_page_downloader.py  # KOPÍROVAT BEZ ZMĚN
    ├── product_image_downloader.py         # KOPÍROVAT BEZ ZMĚN
    ├── product_to_eshop_csv_saver.py       # KOPÍROVAT BEZ ZMĚN
    ├── utils.py                            # KOPÍROVAT BEZ ZMĚN
    ├── webpage_downloader.py               # KOPÍROVAT BEZ ZMĚN
    └── log_colors.json                     # KOPÍROVAT BEZ ZMĚN
```

### JMENNÉ KONVENCE (MANDATORY)

**Složky**:
- Downloader folder: `{brand}downloader` (lowercase, bez podtržítek)
- Library folder: `{brand}lib` (lowercase, bez podtržítek)
- Shared folder: `shared` (vždy stejné)

**Soubory**:
- Main script: `{brand}_downloader.py` (lowercase, s podtržítky)
- Output CSV: `{Brand}Output.csv` (PascalCase)
- Main page HTML: `{brand}.html` (lowercase)

**Proměnné a funkce**:
- Funkce a proměnné: `snake_case`
- Třídy: `PascalCase` (`Product`, `Variant`)
- Konstanty: `UPPER_CASE` (`MAIN_URL`, `CSV_OUTPUT_NAME`)

**Result folder**:
- Default path: `H:/Desaka/{Brand}` (PascalCase)

---

## 3. SHARED MODULY (MUST BE IDENTICAL - KOPÍROVAT BEZ ZMĚN)

Následující moduly jsou **IDENTICKÉ** pro všechny downloadery. **KOPÍRUJTE** je z libovolného existujícího downloaderu (např. `gewodownloader/shared/`) **BEZ JAKÝCHKOLIV ÚPRAV**.

### 3.1 directory_manager.py

**KOPÍROVAT BEZ ZMĚN**

**Funkce**: `ensure_directories(root_folder)`
- Vytvoří strukturu složek pro výsledky
- Vrací: None

**Vytváří**:
```
{root_folder}/Full_{DD.MM.YYYY}/
├── Pages/          # Kategorie stránky
├── Products/       # Produktové stránky
└── Photos/         # Obrázky
    ├── MainImages/
    └── GalleryImages/
```

### 3.2 logging_config.py

**KOPÍROVAT BEZ ZMĚN**

**Funkce**: `setup_logging(debug=False, log_file="default.log")`
- Nastavuje logging s barvami (colorlog)
- DEBUG level pokud `debug=True`, jinak INFO
- Zapisuje do konzole i do souboru

### 3.3 main_page_downloader.py

**KOPÍROVAT BEZ ZMĚN**

**Funkce**: `download_main_page(root_folder, MAIN_URL, MAIN_PAGE_FILENAME, overwrite=False)`
- Stáhne hlavní stránku e-shopu
- Vrací: Absolutní cestu k souboru nebo None

### 3.4 webpage_downloader.py

**KOPÍROVAT BEZ ZMĚN**

**Funkce**: `download_webpage(url, filepath, overwrite=False, debug=False)`
- HTTP GET request pomocí `requests`
- Sanitizace názvů souborů
- Kontrola 404 chyb
- Vrací: True/False

### 3.5 html_loader.py

**KOPÍROVAT BEZ ZMĚN**

**Funkce**: `load_html_as_dom_tree(filepath)`
- Načte HTML soubor
- Vrací: BeautifulSoup object (parser='lxml')

### 3.6 category_firstpage_downloader.py

**KOPÍROVAT BEZ ZMĚN**

**Funkce**: `download_category_firstpages(category_links, root_folder, overwrite)`
- Stáhne první stránky všech kategorií
- Vrací: List cest ke staženým souborům

### 3.7 category_pages_downloader.py

**KOPÍROVAT BEZ ZMĚN**

**Funkce**: `download_category_pages(category_page_links, root_folder, overwrite)`
- Stáhne všechny stránkované stránky kategorií
- Vrací: List cest ke staženým souborům

### 3.8 product_detail_page_downloader.py

**KOPÍROVAT BEZ ZMĚN**

**Funkce**: `download_product_detail_pages(product_detail_links, root_folder, overwrite)`
- Stáhne detailní stránky produktů
- Použití tqdm progress bar
- Vrací: List cest ke staženým souborům

### 3.9 product_detail_variant_page_downloader.py

**KOPÍROVAT BEZ ZMĚN** (použít jen pokud e-shop má varianty)

**Funkce**: `download_product_detail_variant_pages(variant_links, root_folder, overwrite)`
- Stáhne stránky variant produktů
- Vrací: List cest ke staženým souborům

### 3.10 product_image_downloader.py

**KOPÍROVAT BEZ ZMĚN**

**Funkce**:
- `download_product_main_image(products, root_folder, overwrite)`
- `download_product_gallery_images(products, root_folder, overwrite)`

**Úkol**: Stahuje obrázky z Product objektů

### 3.11 product_to_eshop_csv_saver.py

**KOPÍROVAT BEZ ZMĚN**

**Funkce**: `export_to_csv(csv_output_path, products)`
- Exportuje List[Product] do CSV
- Formát: 7 sloupců (viz sekce 7)

### 3.12 utils.py

**KOPÍROVAT BEZ ZMĚN**

**Funkce**:
- `sanitize_filename(filename)` - URL-encode nepovolených znaků
- `get_full_day_folder(root_folder)` - `{root}/Full_{DD.MM.YYYY}`
- `get_pages_folder(root_folder)` - `{root}/Full_{DD.MM.YYYY}/Pages`
- `get_products_folder(root_folder)` - `{root}/Full_{DD.MM.YYYY}/Products`
- `get_photos_folder(root_folder)` - `{root}/Full_{DD.MM.YYYY}/Photos`
- `get_script_name()` - Název spuštěného skriptu
- `get_log_filename(log_dir)` - Generuje: `{script}_Log_{YYYY-MM-DD_HH-MM-SS}.log`

### 3.13 image_downloader.py

**KOPÍROVAT BEZ ZMĚN**

**Funkce**: `download_image(url, filepath, overwrite=False)`
- Stáhne jeden obrázek
- Vrací: True/False

### 3.14 log_colors.json

**KOPÍROVAT BEZ ZMĚN**

JSON konfigurace barevného schématu pro logging.

---

## 4. SITE-SPECIFIC MODULY (MUST BE CUSTOMIZED)

Tyto moduly **MUSÍ BÝT PŘIZPŮSOBENY** pro každý e-shop. Používejte níže uvedené šablony.

### 4.1 constants.py (PŘIZPŮSOBIT)

**Template**:

```python
"""
Constants specific to {BrandName} e-shop.
"""

# Main e-shop URL
MAIN_URL = "https://example.com"  # ZMĚNIT na skutečnou URL e-shopu

# Default result folder (Windows path)
DEFAULT_RESULT_FOLDER = r"H:/Desaka/{BrandName}"  # ZMĚNIT na název brandu (PascalCase)

# Main page filename
MAIN_PAGE_FILENAME = "{brand}.html"  # ZMĚNIT na lowercase název brandu

# CSV output filename
CSV_OUTPUT_NAME = "{Brand}Output.csv"  # ZMĚNIT na PascalCase název brandu

# Log directory
LOG_DIR = r"H:/Logs"  # PONECHAT stejné
```

**Příklad pro Butterfly**:
```python
MAIN_URL = "https://butterfly.tt"
DEFAULT_RESULT_FOLDER = r"H:/Desaka/Butterfly"
MAIN_PAGE_FILENAME = "butterfly.html"
CSV_OUTPUT_NAME = "ButterflyOutput.csv"
LOG_DIR = r"H:/Logs"
```

### 4.2 category_link_extractor.py (PŘIZPŮSOBIT)

**Úkol**: Extrahovat odkazy na všechny kategorie z hlavní stránky.

**Template**:

```python
"""
Extracts category links from {BrandName} main page.
"""
import logging
from urllib.parse import urljoin
from tqdm import tqdm
from {brand}lib.constants import MAIN_URL


def extract_category_links(main_page_soup):
    """
    Extract all category links from the main page DOM.

    :param main_page_soup: BeautifulSoup object of the main page
    :return: Sorted list of unique absolute category URLs
    """
    category_links = set()

    # PŘIZPŮSOBIT: Najít správné CSS selektory pro kategorie
    # Inspirace - typické selektory:
    # - menu_links = main_page_soup.find_all('a', class_='menu__category')
    # - nav_links = main_page_soup.find_all('a', class_='navigation-item')
    # - category_links_elements = main_page_soup.select('.category-menu a')

    menu_links = main_page_soup.find_all('a', class_='YOUR_CATEGORY_CLASS')  # ZMĚNIT!

    for link in tqdm(menu_links, desc="Extracting category links"):
        href = link.get('href')
        if href:
            # Konverze na absolutní URL
            absolute_url = urljoin(MAIN_URL, href)
            category_links.add(absolute_url)

    logging.info(f"Found {len(category_links)} unique category links")
    return sorted(category_links)
```

**Instrukce pro implementaci**:
1. Otevřít e-shop v prohlížeči
2. Použít Developer Tools (F12) → Inspect
3. Najít navigační menu s kategoriemi
4. Identifikovat CSS třídy nebo selektory pro odkazy
5. Implementovat správný selektor v kódu výše

### 4.3 category_pages_link_extractor.py (PŘIZPŮSOBIT)

**Úkol**: Extrahovat všechny URL stránkovaných stránek kategorií (paginace).

**Template**:

```python
"""
Extracts paginated category page links from {BrandName}.
"""
import logging
from urllib.parse import urljoin, urlparse, parse_qs
from tqdm import tqdm
from shared.html_loader import load_html_as_dom_tree
from {brand}lib.product_attribute_extractor import get_self_link


def extract_all_category_pages_links(category_firstpage_paths):
    """
    Extract all paginated category page links.

    :param category_firstpage_paths: List of file paths to first pages of categories
    :return: Sorted list of all category page URLs (including pagination)
    """
    all_page_links = set()

    with tqdm(total=len(category_firstpage_paths), desc="Extracting category page links") as pbar:
        for page_path in category_firstpage_paths:
            page_dom = load_html_as_dom_tree(page_path)
            if page_dom:
                page_links = extract_category_pages_links(page_dom)
                all_page_links.update(page_links)
            pbar.update(1)

    logging.info(f"Total category pages (with pagination): {len(all_page_links)}")
    return sorted(all_page_links)


def extract_category_pages_links(category_page_dom):
    """
    Extract all page links for a single category (handles pagination).

    :param category_page_dom: BeautifulSoup object of a category page
    :return: Set of URLs for all pages in this category
    """
    category_url = get_self_link(category_page_dom)
    page_links = set()

    # PŘIZPŮSOBIT: Implementovat logiku paginace specifickou pro e-shop

    # PATTERN 1: Najít poslední stránku a generovat URL
    # Příklad:
    # last_page_element = category_page_dom.find('a', class_='page-link-last')
    # if last_page_element:
    #     last_page_num = int(last_page_element.get_text(strip=True))
    #     for page_num in range(1, last_page_num + 1):
    #         page_url = f"{category_url}?page={page_num}"  # ZMĚNIT podle URL patternu
    #         page_links.add(page_url)

    # PATTERN 2: Extrahovat všechny stránkovací odkazy
    # Příklad:
    # pagination_links = category_page_dom.find_all('a', class_='pagination-link')
    # for link in pagination_links:
    #     href = link.get('href')
    #     if href:
    #         absolute_url = urljoin(category_url, href)
    #         page_links.add(absolute_url)

    # PATTERN 3: Žádná paginace - jen jedna stránka
    # page_links.add(category_url)

    # TODO: IMPLEMENTOVAT správný pattern!

    return page_links
```

**Typické URL paginace patterns**:
- Query parameter: `?page=1`, `?p=2`, `?page_num=3`
- Path parameter: `/page/1`, `/strana/2`
- Hash: `#page=1`

### 4.4 product_detail_link_extractor.py (PŘIZPŮSOBIT)

**Úkol**: Extrahovat odkazy na všechny produktové stránky ze všech stránek kategorií.

**Template**:

```python
"""
Extracts product detail page links from {BrandName} category pages.
"""
import logging
from urllib.parse import urljoin
from tqdm import tqdm
from shared.html_loader import load_html_as_dom_tree
from {brand}lib.constants import MAIN_URL


def extract_all_product_detail_links(category_pages_downloaded_paths):
    """
    Extract all product detail page links from all category pages.

    :param category_pages_downloaded_paths: List of file paths to category pages
    :return: Sorted list of unique product detail URLs
    """
    product_links = set()

    with tqdm(total=len(category_pages_downloaded_paths),
              desc="Extracting product detail links") as pbar:
        for page_path in category_pages_downloaded_paths:
            page_dom = load_html_as_dom_tree(page_path)
            if page_dom:
                links = extract_product_detail_links_from_page(page_dom)
                product_links.update(links)
            pbar.update(1)

    logging.info(f"Found {len(product_links)} unique product links")
    return sorted(product_links)


def extract_product_detail_links_from_page(page_dom):
    """
    Extract product links from a single category page.

    :param page_dom: BeautifulSoup object of a category page
    :return: Set of product detail URLs
    """
    product_links = set()

    # PŘIZPŮSOBIT: Najít správné CSS selektory pro produktové odkazy
    # Typické selektory:
    # - product_cards = page_dom.find_all('a', class_='product-card__link')
    # - product_items = page_dom.find_all('a', class_='product-item')
    # - products = page_dom.select('.product-list .product-link')

    product_elements = page_dom.find_all('a', class_='YOUR_PRODUCT_LINK_CLASS')  # ZMĚNIT!

    for element in product_elements:
        href = element.get('href')
        if href:
            absolute_url = urljoin(MAIN_URL, href)
            product_links.add(absolute_url)

    return product_links
```

### 4.5 product_attribute_extractor.py (PŘIZPŮSOBIT)

**NEJKOMPLEXNĚJŠÍ MODUL - kompletní site-specific implementace!**

**Template**:

```python
"""
Extracts product attributes from {BrandName} product detail pages.
"""
import logging
from urllib.parse import urljoin
from tqdm import tqdm
from shared.html_loader import load_html_as_dom_tree
from {brand}lib.constants import MAIN_URL


class Product:
    """Product data model (IDENTICKÁ struktura pro všechny downloadery)."""
    def __init__(self):
        self.name = ""
        self.short_description = ""
        self.description = ""
        self.variants = []  # List of Variant objects
        self.main_photo_link = ""
        self.main_photo_filepath = ""
        self.photogallery_links = []
        self.photogallery_filepaths = []
        self.url = ""


class Variant:
    """Product variant data model (IDENTICKÁ struktura pro všechny downloadery)."""
    def __init__(self):
        self.key_value_pairs = {}  # Dict: {"Color": "Red", "Size": "XL"}
        self.current_price = 0.0   # Float
        self.basic_price = 0.0     # Float
        self.stock_status = ""     # String: "In stock", "Out of stock", etc.


def get_self_link(dom_tree):
    """
    Get canonical URL of the product page.

    :param dom_tree: BeautifulSoup object
    :return: Canonical URL as string
    """
    # PŘIZPŮSOBIT: Implementovat extraction kanonické URL
    # Pattern 1: canonical tag
    canonical = dom_tree.find('link', rel='canonical')
    if canonical:
        return canonical.get('href', '')

    # Pattern 2: og:url meta tag
    og_url = dom_tree.find('meta', property='og:url')
    if og_url:
        return og_url.get('content', '')

    # Pattern 3: Jiný způsob...
    # TODO: IMPLEMENTOVAT!

    return ""


def extract_product_name(dom_tree):
    """
    Extract product name.

    :param dom_tree: BeautifulSoup object of product page
    :return: Product name as string
    """
    try:
        # PŘIZPŮSOBIT: Najít správný selektor pro název
        # Typické selektory:
        # - name_element = dom_tree.find('h1', class_='product-title')
        # - name_element = dom_tree.find('h1', class_='product-meta__title')
        # - name_element = dom_tree.select_one('.product-name')

        name_element = dom_tree.find('h1', class_='YOUR_TITLE_CLASS')  # ZMĚNIT!

        if name_element:
            name = name_element.get_text(strip=True)
            logging.debug(f"Extracted name: {name}")
            return name

        logging.warning("Product name not found")
        return ""

    except Exception as e:
        logging.error(f"Error extracting product name: {e}", exc_info=True)
        return ""


def extract_product_short_description(dom_tree):
    """
    Extract short product description.

    :param dom_tree: BeautifulSoup object
    :return: Short description as HTML string (single-line with <br> tags)
    """
    try:
        # PŘIZPŮSOBIT: Najít správný selektor
        desc_element = dom_tree.find('div', class_='YOUR_SHORT_DESC_CLASS')  # ZMĚNIT!

        if desc_element:
            # Konverze na single-line HTML s <br> tagy
            desc_html = str(desc_element)
            desc_html = desc_html.replace('\n', '<br>').replace('\r', '')
            logging.debug("Extracted short description")
            return desc_html

        return ""

    except Exception as e:
        logging.error(f"Error extracting short description: {e}", exc_info=True)
        return ""


def extract_product_description(dom_tree):
    """
    Extract full product description.

    :param dom_tree: BeautifulSoup object
    :return: Description as HTML string (single-line with <br> tags)
    """
    try:
        # PŘIZPŮSOBIT: Najít správný selektor
        desc_element = dom_tree.find('div', class_='YOUR_DESCRIPTION_CLASS')  # ZMĚNIT!

        if desc_element:
            # Konverze na single-line HTML s <br> tagy
            desc_html = str(desc_element)
            desc_html = desc_html.replace('\n', '<br>').replace('\r', '')
            logging.debug("Extracted full description")
            return desc_html

        return ""

    except Exception as e:
        logging.error(f"Error extracting description: {e}", exc_info=True)
        return ""


def extract_product_main_photo(dom_tree):
    """
    Extract main product photo URL.

    :param dom_tree: BeautifulSoup object
    :return: Absolute URL of main photo
    """
    try:
        # PŘIZPŮSOBIT: Najít správný selektor
        img_element = dom_tree.find('img', class_='YOUR_MAIN_IMAGE_CLASS')  # ZMĚNIT!

        if img_element:
            # Zkusit různé atributy
            img_url = img_element.get('src') or img_element.get('data-src') or img_element.get('data-original')

            if img_url:
                absolute_url = urljoin(MAIN_URL, img_url)
                logging.debug(f"Extracted main photo: {absolute_url}")
                return absolute_url

        logging.warning("Main photo not found")
        return ""

    except Exception as e:
        logging.error(f"Error extracting main photo: {e}", exc_info=True)
        return ""


def extract_product_gallery_photos(dom_tree):
    """
    Extract gallery photo URLs.

    :param dom_tree: BeautifulSoup object
    :return: List of absolute URLs
    """
    gallery_urls = []

    try:
        # PŘIZPŮSOBIT: Najít správný selektor
        gallery_elements = dom_tree.find_all('img', class_='YOUR_GALLERY_CLASS')  # ZMĚNIT!

        for img in gallery_elements:
            img_url = img.get('src') or img.get('data-src') or img.get('data-original')
            if img_url:
                absolute_url = urljoin(MAIN_URL, img_url)
                gallery_urls.append(absolute_url)

        logging.debug(f"Extracted {len(gallery_urls)} gallery photos")

    except Exception as e:
        logging.error(f"Error extracting gallery photos: {e}", exc_info=True)

    return gallery_urls


def extract_product_variants(dom_tree):
    """
    Extract product variants (colors, sizes, etc.).

    :param dom_tree: BeautifulSoup object
    :return: List of Variant objects
    """
    variants = []

    try:
        # PŘIZPŮSOBIT: Implementovat extraction variant
        # Toto je VELMI site-specific!

        # PATTERN 1: Varianty jako option elementy
        # variant_selects = dom_tree.find_all('select', class_='product-option')
        # for select in variant_selects:
        #     option_name = select.get('data-option-name')
        #     for option in select.find_all('option'):
        #         variant = Variant()
        #         variant.key_value_pairs[option_name] = option.get_text(strip=True)
        #         # ... extract price, stock
        #         variants.append(variant)

        # PATTERN 2: Jednoduchý produkt bez variant
        # Vytvořit jednu "výchozí" variantu
        variant = Variant()

        # PŘIZPŮSOBIT: Extract ceny
        price_element = dom_tree.find('span', class_='YOUR_PRICE_CLASS')  # ZMĚNIT!
        if price_element:
            price_text = price_element.get_text(strip=True)
            # Parse price (remove currency, convert to float)
            price = parse_price(price_text)
            variant.current_price = price
            variant.basic_price = price

        # PŘIZPŮSOBIT: Extract skladové zásoby
        stock_element = dom_tree.find('div', class_='YOUR_STOCK_CLASS')  # ZMĚNIT!
        if stock_element:
            variant.stock_status = stock_element.get_text(strip=True)

        variants.append(variant)

        logging.debug(f"Extracted {len(variants)} variants")

    except Exception as e:
        logging.error(f"Error extracting variants: {e}", exc_info=True)

    return variants


def parse_price(price_text):
    """
    Parse price from text to float.

    :param price_text: Price as string (e.g., "€29.99", "$19,99", "299 Kč")
    :return: Price as float
    """
    try:
        # Remove currency symbols and whitespace
        import re
        price_clean = re.sub(r'[^\d,.]', '', price_text)
        # Replace comma with dot for European format
        price_clean = price_clean.replace(',', '.')
        return float(price_clean)
    except:
        return 0.0


def extract_products(product_detail_page_paths):
    """
    Extract all products from product detail pages.

    :param product_detail_page_paths: List of file paths to product pages
    :return: List of Product objects
    """
    products = []

    with tqdm(total=len(product_detail_page_paths), desc="Extracting product data") as pbar:
        for page_path in product_detail_page_paths:
            try:
                page_dom = load_html_as_dom_tree(page_path)
                if not page_dom:
                    pbar.update(1)
                    continue

                product = Product()
                product.url = get_self_link(page_dom)
                product.name = extract_product_name(page_dom)
                product.short_description = extract_product_short_description(page_dom)
                product.description = extract_product_description(page_dom)
                product.main_photo_link = extract_product_main_photo(page_dom)
                product.photogallery_links = extract_product_gallery_photos(page_dom)
                product.variants = extract_product_variants(page_dom)

                products.append(product)

            except Exception as e:
                logging.error(f"Error processing {page_path}: {e}", exc_info=True)

            pbar.update(1)

    logging.info(f"Successfully extracted {len(products)} products")
    return products
```

**Instrukce pro implementaci**:
1. Otevřít ukázkový produkt v prohlížeči
2. Použít Developer Tools → Inspect na každý element (název, popis, cena, obrázek)
3. Identifikovat CSS selektory
4. Testovat selektory v konzoli: `document.querySelectorAll('.your-selector')`
5. Implementovat správné selektory v kódu výše

### 4.6 product_variant_detail_link_extractor.py (VOLITELNÉ)

**POUŽÍT JEN POKUD** e-shop má **separátní URL pro varianty** (např. různé barvy mají vlastní URL).

**Template**:

```python
"""
Extracts product variant detail page links from {BrandName}.
Only needed if variants have separate URLs.
"""
import logging
from urllib.parse import urljoin
from tqdm import tqdm
from shared.html_loader import load_html_as_dom_tree
from {brand}lib.constants import MAIN_URL


def extract_all_product_variant_detail_links(product_detail_page_paths):
    """
    Extract variant page links from product pages.

    :param product_detail_page_paths: List of file paths to product pages
    :return: Sorted list of variant URLs
    """
    variant_links = set()

    with tqdm(total=len(product_detail_page_paths),
              desc="Extracting variant links") as pbar:
        for page_path in product_detail_page_paths:
            page_dom = load_html_as_dom_tree(page_path)
            if page_dom:
                links = extract_variant_links_from_page(page_dom)
                variant_links.update(links)
            pbar.update(1)

    logging.info(f"Found {len(variant_links)} variant links")
    return sorted(variant_links)


def extract_variant_links_from_page(page_dom):
    """
    Extract variant links from a product page.

    :param page_dom: BeautifulSoup object
    :return: Set of variant URLs
    """
    variant_links = set()

    # PŘIZPŮSOBIT: Implementovat extraction variant URLs
    # Typický pattern:
    # variant_elements = page_dom.find_all('a', class_='variant-link')
    # for element in variant_elements:
    #     href = element.get('href')
    #     if href:
    #         absolute_url = urljoin(MAIN_URL, href)
    #         variant_links.add(absolute_url)

    # TODO: IMPLEMENTOVAT!

    return variant_links
```

---

## 5. HLAVNÍ SOUBOR DOWNLOADERU (MANDATORY 10-STEP PROCESS)

**Soubor**: `{brand}_downloader.py`

**Template**:

```python
"""
{BrandName} E-shop Downloader

Downloads product data from {BrandName} e-shop and exports to CSV.

Usage:
    python {brand}_downloader.py --result_folder H:/Desaka/{Brand} --debug --overwrite
"""

import os
import logging
from argparse import ArgumentParser

# Shared imports
from shared.directory_manager import ensure_directories
from shared.main_page_downloader import download_main_page
from shared.html_loader import load_html_as_dom_tree
from shared.category_firstpage_downloader import download_category_firstpages
from shared.category_pages_downloader import download_category_pages
from shared.product_detail_page_downloader import download_product_detail_pages
# from shared.product_detail_variant_page_downloader import download_product_detail_variant_pages  # VOLITELNÉ
from shared.product_image_downloader import download_product_main_image, download_product_gallery_images
from shared.product_to_eshop_csv_saver import export_to_csv
from shared.logging_config import setup_logging
from shared.utils import get_full_day_folder, get_log_filename

# Site-specific imports
from {brand}lib.constants import DEFAULT_RESULT_FOLDER, MAIN_URL, MAIN_PAGE_FILENAME, CSV_OUTPUT_NAME, LOG_DIR
from {brand}lib.category_link_extractor import extract_category_links
from {brand}lib.category_pages_link_extractor import extract_all_category_pages_links
from {brand}lib.product_detail_link_extractor import extract_all_product_detail_links
from {brand}lib.product_attribute_extractor import extract_products
# from {brand}lib.product_variant_detail_link_extractor import extract_all_product_variant_detail_links  # VOLITELNÉ


def parse_arguments():
    """Parse command line arguments."""
    parser = ArgumentParser(description="{BrandName} E-shop Downloader")

    parser.add_argument(
        "--result_folder",
        type=str,
        default=DEFAULT_RESULT_FOLDER,
        help="Root folder for the script's output"
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Whether to overwrite existing downloaded resources"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable console logging for non-errors"
    )

    # VOLITELNÉ: Přidat speciální parametry jako country_code, language, etc.
    # parser.add_argument(
    #     "--language",
    #     type=str,
    #     default="en",
    #     help="Language code (e.g., en, de, cs)"
    # )

    return parser.parse_args()


def main():
    """
    Main execution function - MANDATORY 10-STEP PROCESS.

    DO NOT modify the order or structure of these steps!
    """
    # Parse arguments
    args = parse_arguments()

    # Setup logging
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    LOG_FILE = get_log_filename(LOG_DIR)
    setup_logging(args.debug, LOG_FILE)

    logging.info("=" * 80)
    logging.info("{BrandName} Downloader Started")
    logging.info("=" * 80)

    root_folder = args.result_folder
    overwrite = args.overwrite

    # Ensure directory structure exists
    ensure_directories(root_folder)

    # ========== STEP 1: Download main webpage ==========
    logging.info("STEP 1: Downloading main page")
    main_page_path = download_main_page(root_folder, MAIN_URL, MAIN_PAGE_FILENAME, overwrite)

    if not main_page_path:
        logging.error("Failed to download main page. Exiting.")
        return

    # ========== STEP 2: Extract category links from main page ==========
    logging.info("STEP 2: Extracting category links from main page")
    main_page_dom = load_html_as_dom_tree(main_page_path)
    category_links = extract_category_links(main_page_dom)

    if not category_links:
        logging.error("No category links found. Exiting.")
        return

    # ========== STEP 3: Download category first pages ==========
    logging.info("STEP 3: Downloading category first pages")
    category_firstpage_paths = download_category_firstpages(category_links, root_folder, overwrite)

    # ========== STEP 4: Extract all category page links (with pagination) ==========
    logging.info("STEP 4: Extracting category page links (pagination)")
    category_page_links = extract_all_category_pages_links(category_firstpage_paths)

    # ========== STEP 5: Download all category pages ==========
    logging.info("STEP 5: Downloading all category pages")
    category_pages_downloaded_paths = download_category_pages(category_page_links, root_folder, overwrite)

    # ========== STEP 6: Extract product detail links ==========
    logging.info("STEP 6: Extracting product detail links")
    product_detail_links = extract_all_product_detail_links(category_pages_downloaded_paths)

    if not product_detail_links:
        logging.error("No product links found. Exiting.")
        return

    # ========== STEP 7: Download product detail pages ==========
    logging.info("STEP 7: Downloading product detail pages")
    product_detail_page_paths = download_product_detail_pages(product_detail_links, root_folder, overwrite)

    # ========== STEP 7b (VOLITELNÉ): Handle product variants if needed ==========
    # UNCOMMENT pokud e-shop má separátní URLs pro varianty
    # logging.info("STEP 7b: Extracting and downloading variant pages")
    # product_detail_variant_links = extract_all_product_variant_detail_links(product_detail_page_paths)
    # product_detail_variant_page_paths = download_product_detail_variant_pages(
    #     product_detail_variant_links, root_folder, overwrite
    # )
    # # Kombinovat product + variant stránky
    # product_detail_all_page_paths = product_detail_page_paths + product_detail_variant_page_paths

    # Pro většinu e-shopů (bez separátních variant URLs):
    product_detail_all_page_paths = product_detail_page_paths

    # ========== STEP 8: Extract product attributes ==========
    logging.info("STEP 8: Extracting product attributes")
    products = extract_products(product_detail_all_page_paths)

    if not products:
        logging.warning("No products extracted. Check extraction logic.")
        # Pokračovat dál - možná jsou obrázky k exportu

    # ========== STEP 9: Download product images ==========
    logging.info("STEP 9: Downloading product images")
    download_product_main_image(products, root_folder, overwrite)
    download_product_gallery_images(products, root_folder, overwrite)

    # ========== STEP 10: Export to CSV ==========
    logging.info("STEP 10: Exporting to CSV")
    csv_output_path = f"{get_full_day_folder(root_folder)}/{CSV_OUTPUT_NAME}"
    export_to_csv(csv_output_path, products)

    logging.info("=" * 80)
    logging.info(f"Download complete! Results saved to: {csv_output_path}")
    logging.info("=" * 80)


if __name__ == "__main__":
    main()
```

**KRITICKY DŮLEŽITÉ**:
- ❌ **NEMĚNIT** pořadí kroků 1-10
- ❌ **NEMAZAT** žádný krok
- ✅ **ZACHOVAT** strukturu a flow
- ✅ **PŘIDAT** pouze STEP 7b pokud jsou separátní variant URLs

---

## 6. DATOVÉ MODELY (IDENTICKÉ PRO VŠECHNY)

### Product Class (MANDATORY STRUCTURE)

```python
class Product:
    """Product data model."""
    def __init__(self):
        self.name = ""                      # String
        self.short_description = ""         # HTML string (single-line with <br>)
        self.description = ""               # HTML string (single-line with <br>)
        self.variants = []                  # List[Variant]
        self.main_photo_link = ""           # String (absolute URL)
        self.main_photo_filepath = ""       # String (local path) - set by image downloader
        self.photogallery_links = []        # List[String] (absolute URLs)
        self.photogallery_filepaths = []    # List[String] (local paths) - set by image downloader
        self.url = ""                       # String (canonical URL)
```

### Variant Class (MANDATORY STRUCTURE)

```python
class Variant:
    """Product variant data model."""
    def __init__(self):
        self.key_value_pairs = {}   # Dict[str, str]: {"Color": "Red", "Size": "M"}
        self.current_price = 0.0    # Float (aktuální cena)
        self.basic_price = 0.0      # Float (základní/původní cena)
        self.stock_status = ""      # String: "In stock", "Out of stock", "2-3 days", etc.
```

**Příklad Variant objektu**:
```python
variant = Variant()
variant.key_value_pairs = {"Color": "Red", "Size": "Large"}
variant.current_price = 29.99
variant.basic_price = 39.99
variant.stock_status = "In stock"
```

---

## 7. CSV EXPORT FORMÁT (EXACT SPECIFICATION)

### Soubor

**Název**: `{Brand}Output.csv` (PascalCase)
**Umístění**: `{result_folder}/Full_{DD.MM.YYYY}/{Brand}Output.csv`
**Encoding**: UTF-8 with BOM
**Delimiter**: Comma (`,`)
**Quoting**: All fields (QUOTE_ALL)

### Sloupce (MANDATORY ORDER)

| # | Column Name | Content | Format |
|---|-------------|---------|--------|
| 1 | Name | Název produktu | String |
| 2 | Short Description | Krátký popis | HTML (single-line, `<br>` místo `\n`) |
| 3 | Description | Plný popis | HTML (single-line, `<br>` místo `\n`) |
| 4 | Main Photo Filepath | Cesta k hlavnímu obrázku | Absolute path |
| 5 | Gallery Filepaths | Cesty k obrázkům galerie | Pipe-separated: `path1\|path2\|path3` |
| 6 | Variants | Varianty produktu | Pipe-separated JSON objects |
| 7 | URL | URL produktu | Absolute URL |

### Formát Variants sloupce (CRITICAL!)

Pipe-separated (`|`) JSON objekty:

```
{"key_value_pairs": {...}, "current_price": 29.99, "basic_price": 39.99, "stock_status": "In stock"}|{"key_value_pairs": {...}, "current_price": 24.99, "basic_price": 39.99, "stock_status": "In stock"}
```

**Příklad**:
```
{"key_value_pairs": {"Color": "Red", "Size": "M"}, "current_price": 29.99, "basic_price": 39.99, "stock_status": "In stock"}|{"key_value_pairs": {"Color": "Blue", "Size": "L"}, "current_price": 29.99, "basic_price": 39.99, "stock_status": "2-3 days"}
```

### Příklad CSV řádku

```csv
Name,Short Description,Description,Main Photo Filepath,Gallery Filepaths,Variants,URL
"Table Tennis Bat Professional","High quality bat<br>For professionals","<div class='desc'>Professional bat with ITTF approved rubbers<br>Speed: 95<br>Control: 85</div>","H:/Desaka/Brand/Full_21.11.2024/Photos/MainImages/bat_professional_main.jpg","H:/Desaka/Brand/Full_21.11.2024/Photos/GalleryImages/bat_professional_gallery_1.jpg|H:/Desaka/Brand/Full_21.11.2024/Photos/GalleryImages/bat_professional_gallery_2.jpg","{""key_value_pairs"": {""Color"": ""Red""}, ""current_price"": 129.99, ""basic_price"": 149.99, ""stock_status"": ""In stock""}","https://example.com/products/bat-professional"
```

**Export je implementován v `shared/product_to_eshop_csv_saver.py` - KOPÍROVAT BEZ ZMĚN!**

---

## 8. VÝSTUPNÍ STRUKTURA SLOŽEK (MANDATORY)

```
H:/Desaka/{Brand}/                           # Root folder (PascalCase)
│
└── Full_{DD.MM.YYYY}/                       # Složka s datem (formát: DD.MM.YYYY)
    │
    ├── {brand}.html                         # Hlavní stránka e-shopu
    │
    ├── Pages/                               # HTML stránky kategorií
    │   ├── category_page_1.html
    │   ├── category_page_2.html
    │   ├── ...
    │   └── category_page_N.html
    │
    ├── Products/                            # HTML stránky produktů
    │   ├── product_1.html
    │   ├── product_2.html
    │   ├── ...
    │   └── product_M.html
    │
    ├── Photos/                              # Obrázky
    │   ├── MainImages/                      # Hlavní obrázky produktů
    │   │   ├── product1_main.jpg
    │   │   ├── product2_main.jpg
    │   │   └── ...
    │   │
    │   └── GalleryImages/                   # Galeriové obrázky
    │       ├── product1_gallery_1.jpg
    │       ├── product1_gallery_2.jpg
    │       ├── product2_gallery_1.jpg
    │       └── ...
    │
    └── {Brand}Output.csv                    # Výstupní CSV (PascalCase)
```

**Logy** (separátní složka):
```
H:/Logs/
├── {brand}_downloader_Log_2024-11-21_14-30-45.log
├── {brand}_downloader_Log_2024-11-22_10-15-20.log
└── ...
```

**Vytváření struktury**:
- Implementováno v `shared/directory_manager.py` - KOPÍROVAT BEZ ZMĚN
- Názvyy souborů sanitizovány přes `shared/utils.py::sanitize_filename()`

---

## 9. CODING STANDARDS (MANDATORY)

### 9.1 Import Statements Ordering

```python
# 1. Standard library imports (abecedně)
import csv
import json
import logging
import os
import re
from argparse import ArgumentParser
from datetime import datetime
from urllib.parse import urljoin, urlparse

# 2. Third-party imports (abecedně)
from bs4 import BeautifulSoup
import requests
from tqdm import tqdm

# 3. Shared module imports (abecedně)
from shared.category_firstpage_downloader import download_category_firstpages
from shared.category_pages_downloader import download_category_pages
from shared.directory_manager import ensure_directories
from shared.html_loader import load_html_as_dom_tree
# ... další shared imports

# 4. Site-specific imports (abecedně)
from {brand}lib.category_link_extractor import extract_category_links
from {brand}lib.constants import MAIN_URL, DEFAULT_RESULT_FOLDER, CSV_OUTPUT_NAME
from {brand}lib.product_attribute_extractor import extract_products
# ... další site-specific imports
```

### 9.2 Naming Conventions

**Soubory a složky**:
```python
# ✅ CORRECT
gewodownloader/
gewolib/
gewo_downloader.py
category_link_extractor.py

# ❌ WRONG
GewoDownloader/
gewo-lib/
gewoDownloader.py
CategoryLinkExtractor.py
```

**Proměnné a funkce**:
```python
# ✅ CORRECT
def extract_product_name(dom_tree):
    category_links = []
    main_page_path = "..."

# ❌ WRONG
def ExtractProductName(DomTree):
    CategoryLinks = []
    mainPagePath = "..."
```

**Třídy**:
```python
# ✅ CORRECT
class Product:
class Variant:
class ProductExtractor:

# ❌ WRONG
class product:
class VARIANT:
class product_extractor:
```

**Konstanty**:
```python
# ✅ CORRECT
MAIN_URL = "https://example.com"
DEFAULT_RESULT_FOLDER = r"H:/Desaka/Brand"
CSV_OUTPUT_NAME = "BrandOutput.csv"

# ❌ WRONG
main_url = "https://example.com"
defaultResultFolder = r"H:/Desaka/Brand"
CsvOutputName = "BrandOutput.csv"
```

### 9.3 Docstrings

**Funkce**:
```python
def extract_product_name(dom_tree):
    """
    Extract product name from the product detail page DOM.

    :param dom_tree: BeautifulSoup object containing the parsed HTML
    :return: Product name as string, empty string if not found
    """
    # Implementation
```

**Třídy**:
```python
class Product:
    """
    Product data model.

    Represents a single product with all its attributes, variants,
    and associated images.
    """
    def __init__(self):
        # ...
```

**Moduly** (na začátku souboru):
```python
"""
{BrandName} category link extractor.

Extracts category links from the main page of {BrandName} e-shop.
"""
```

### 9.4 Error Handling Patterns

**Try-Except s loggingem**:
```python
# ✅ CORRECT
def extract_something(dom_tree):
    try:
        element = dom_tree.find('div', class_='target')
        if element:
            value = element.get_text(strip=True)
            logging.debug(f"Found value: {value}")
            return value

        logging.warning("Target element not found, trying fallback")
        fallback = dom_tree.find('span', class_='fallback')
        if fallback:
            return fallback.get_text(strip=True)

        logging.error("Could not extract value")
        return ""

    except Exception as e:
        logging.error(f"Error extracting value: {e}", exc_info=True)
        return ""

# ❌ WRONG
def extract_something(dom_tree):
    element = dom_tree.find('div', class_='target')
    value = element.get_text()  # Může způsobit AttributeError!
    return value
```

**Kontrola None hodnot**:
```python
# ✅ CORRECT
href = link.get('href')
if href:
    absolute_url = urljoin(MAIN_URL, href)
    category_links.add(absolute_url)

# ❌ WRONG
href = link.get('href')
absolute_url = urljoin(MAIN_URL, href)  # href může být None!
```

### 9.5 Logging Standards

**Úrovně**:
```python
# DEBUG - Detailní informace (jen s --debug)
logging.debug(f"Found product name in h1.title: {product_name}")
logging.debug(f"Extracted {len(gallery_urls)} gallery images")

# INFO - Důležité události
logging.info("STEP 1: Downloading main page")
logging.info(f"Found {len(category_links)} unique category links")

# WARNING - Varování, fallbacky
logging.warning("Target element not found, trying alternative selector")
logging.warning("No gallery images found for product")

# ERROR - Chyby
logging.error(f"Failed to download {url}: {e}")
logging.error("Product name not found")

# CRITICAL - Kritické chyby (zřídka)
logging.critical("Cannot create output directory - permissions denied")
```

**Informativní zprávy**:
```python
# ✅ CORRECT
logging.error(f"Failed to download {url} to {filepath}: {e}", exc_info=True)
logging.debug(f"Parsing price from text: '{price_text}' -> {price_value}")

# ❌ WRONG
logging.error("Error!")
logging.debug("Parsing...")
```

**Zakázáno používat print()**:
```python
# ❌ WRONG
print("Downloading product...")
print(f"Found {count} items")

# ✅ CORRECT
logging.info("Downloading product...")
logging.info(f"Found {count} items")
```

### 9.6 Progress Bars

**Používat tqdm pro dlouhé operace**:
```python
# ✅ CORRECT
with tqdm(total=len(items), desc="Processing items") as pbar:
    for item in items:
        process_item(item)
        pbar.update(1)

# Nebo jednodušeji:
for item in tqdm(items, desc="Processing items"):
    process_item(item)

# ❌ WRONG
for item in items:  # Bez progress baru pro 1000+ items!
    process_item(item)
```

### 9.7 URL Handling

**Vždy absolutní URLs**:
```python
# ✅ CORRECT
from urllib.parse import urljoin

href = link.get('href')
if href:
    absolute_url = urljoin(MAIN_URL, href)

# ❌ WRONG
href = link.get('href')
# href může být relativní: "/products/item" místo "https://site.com/products/item"
```

**Kontrola None**:
```python
# ✅ CORRECT
img_url = img.get('src') or img.get('data-src') or img.get('data-original')
if img_url:
    absolute_url = urljoin(MAIN_URL, img_url)

# ❌ WRONG
img_url = img.get('src')
absolute_url = urljoin(MAIN_URL, img_url)  # img_url může být None!
```

### 9.8 HTML Processing

**Single-line konverze**:
```python
# ✅ CORRECT
desc_html = str(desc_element)
desc_html = desc_html.replace('\n', '<br>').replace('\r', '')

# ❌ WRONG
desc_html = str(desc_element)  # Obsahuje \n - způsobí problémy v CSV!
```

**Text extraction**:
```python
# ✅ CORRECT
name = name_element.get_text(strip=True)  # Odstraní whitespace

# ❌ WRONG
name = name_element.text  # Může obsahovat leading/trailing whitespace
```

---

## 10. DEPENDENCIES

### Python Version

**Minimum**: Python 3.7+
**Doporučeno**: Python 3.9+

### Required Packages

**requirements.txt**:
```txt
beautifulsoup4>=4.11.0
lxml>=4.9.0
requests>=2.28.0
tqdm>=4.64.0
colorlog>=6.7.0
```

**Instalace**:
```bash
pip install -r requirements.txt
```

**Standard library** (built-in, nevyžaduje instalaci):
- `os`, `sys`, `logging`, `datetime`, `argparse`, `csv`, `json`, `re`, `urllib`

---

## 11. VALIDAČNÍ CHECKLIST

### Před commitem ZKONTROLOVAT:

#### A. Struktura projektu
- [ ] Složka `{brand}downloader/` s lowercase názvem
- [ ] Hlavní soubor `{brand}_downloader.py` existuje
- [ ] Složka `{brand}lib/` s 5-6 moduly
- [ ] Složka `shared/` se 13+ moduly (zkopírovaná bez změn)
- [ ] `constants.py` má správné URL a názvy

#### B. Hlavní soubor
- [ ] 10-stupňový proces je kompletní
- [ ] Všechny kroky jsou v správném pořadí
- [ ] Import statements v správném pořadí
- [ ] Argumenty: `--result_folder`, `--overwrite`, `--debug`
- [ ] Logging je nastaven správně

#### C. Site-specific moduly
- [ ] `category_link_extractor.py` - implementován
- [ ] `category_pages_link_extractor.py` - implementován
- [ ] `product_detail_link_extractor.py` - implementován
- [ ] `product_attribute_extractor.py` - KOMPLETNĚ implementován
- [ ] Product a Variant třídy mají správnou strukturu
- [ ] Všechny extraction funkce vrací správné typy

#### D. Testování
- [ ] Downloader běží bez chyb: `python {brand}_downloader.py --debug`
- [ ] Hlavní stránka se stáhne
- [ ] Kategorie jsou extrahovány (alespoň 1)
- [ ] Produkty jsou extrahovány (alespoň 1)
- [ ] CSV je vygenerován
- [ ] CSV má 7 sloupců v správném pořadí
- [ ] Obrázky se stahují do správných složek
- [ ] Logy jsou čitelné a informativní

#### E. CSV validace
- [ ] Název souboru: `{Brand}Output.csv`
- [ ] Umístění: `Full_{DD.MM.YYYY}/`
- [ ] 7 sloupců v tomto pořadí: Name, Short Description, Description, Main Photo Filepath, Gallery Filepaths, Variants, URL
- [ ] Variants jsou JSON objekty pipe-separated
- [ ] HTML popisy jsou single-line s `<br>`

#### F. Coding standards
- [ ] snake_case pro funkce a proměnné
- [ ] PascalCase pro třídy
- [ ] UPPER_CASE pro konstanty
- [ ] Docstrings pro všechny funkce
- [ ] Error handling s try-except
- [ ] Logging místo print()
- [ ] Progress bary pro dlouhé operace

#### G. Git
- [ ] `.gitignore` má `H:/Desaka/`, `H:/Logs/`, `*.pyc`, `__pycache__/`
- [ ] Commit message: "Add {BrandName} downloader"
- [ ] README aktualizován se jménem nového downloaderu

---

## 12. DEBUGGING GUIDE

### Typické problémy a řešení

#### Problem: Hlavní stránka se nestáhne (404)

**Diagnóza**:
```bash
python {brand}_downloader.py --debug
```
Zkontrolovat log: `Failed to download main page`

**Řešení**:
- Ověřit URL v `constants.py` - otevřít v prohlížeči
- Zkontrolovat, zda web vyžaduje User-Agent header
- Zkontrolovat `shared/webpage_downloader.py` - možná potřebuje headers

#### Problem: Žádné kategorie nejsou extrahovány

**Diagnóza**:
```bash
python {brand}_downloader.py --debug
```
Log: `Found 0 unique category links`

**Řešení**:
1. Otevřít staženou hlavní stránku: `H:/Desaka/{Brand}/Full_{DATE}/{brand}.html`
2. Hledat kategorie ručně (Ctrl+F: "kategorie", "category", "menu")
3. Identifikovat CSS třídy
4. Aktualizovat `{brand}lib/category_link_extractor.py`

#### Problem: Produkty se neextrahují

**Diagnóza**:
```bash
python {brand}_downloader.py --debug
```
Log: `Successfully extracted 0 products`

**Řešení**:
1. Otevřít ukázkovou produktovou stránku: `H:/Desaka/{Brand}/Full_{DATE}/Products/product_*.html`
2. Hledat název produktu, cenu, popis v HTML
3. Použít Developer Tools v prohlížeči na live stránce
4. Aktualizovat selektory v `product_attribute_extractor.py`
5. Přidat debug logging do extraction funkcí:
   ```python
   logging.debug(f"Searching for product name with selector: h1.product-title")
   name_element = dom_tree.find('h1', class_='product-title')
   logging.debug(f"Found element: {name_element}")
   ```

#### Problem: CSV je prázdný nebo má chybějící sloupce

**Diagnóza**:
Otevřít CSV v textovém editoru, zkontrolovat header.

**Řešení**:
- Ověřit, že `shared/product_to_eshop_csv_saver.py` je správně zkopírován
- Zkontrolovat, že Product objekty mají všechny atributy
- Zkontrolovat, že `variants` je List[Variant], ne None

#### Problem: Obrázky se nestahují

**Diagnóza**:
```bash
python {brand}_downloader.py --debug
```
Log: `Failed to download image`

**Řešení**:
- Zkontrolovat, že `main_photo_link` je absolutní URL (ne relativní)
- Zkontrolovat, že URL obrázku je validní (otevřít v prohlížeči)
- Použít `urljoin(MAIN_URL, relative_url)`

#### Problem: Paginace nefunguje (jen první stránka kategorií)

**Diagnóza**:
Log: `Total category pages (with pagination): {same as categories}`

**Řešení**:
1. Otevřít kategorii na webu
2. Najít tlačítko "Next page" nebo čísla stránek
3. Zkontrolovat URL pattern (e.g., `?page=2`, `/page/2`)
4. Implementovat v `category_pages_link_extractor.py`

---

## 13. PŘÍKLADY KÓDU

### Příklad 1: Extraction variant se select elementem

```python
def extract_product_variants(dom_tree):
    """Extract variants from select dropdown."""
    variants = []

    try:
        # Najít select element pro barvy
        color_select = dom_tree.find('select', {'name': 'color'})

        if color_select:
            options = color_select.find_all('option')
            for option in options:
                if option.get('value'):  # Skip empty option
                    variant = Variant()
                    variant.key_value_pairs['Color'] = option.get_text(strip=True)

                    # Extract cenu a stock (obvykle stejné pro všechny barvy)
                    price_element = dom_tree.find('span', class_='price')
                    if price_element:
                        variant.current_price = parse_price(price_element.get_text())
                        variant.basic_price = variant.current_price

                    variant.stock_status = "In stock"  # Nebo extract ze stránky
                    variants.append(variant)
        else:
            # Žádné varianty - vytvořit výchozí variantu
            variant = Variant()
            price_element = dom_tree.find('span', class_='price')
            if price_element:
                variant.current_price = parse_price(price_element.get_text())
                variant.basic_price = variant.current_price

            stock_element = dom_tree.find('div', class_='stock')
            if stock_element:
                variant.stock_status = stock_element.get_text(strip=True)

            variants.append(variant)

        logging.debug(f"Extracted {len(variants)} variants")

    except Exception as e:
        logging.error(f"Error extracting variants: {e}", exc_info=True)

    return variants
```

### Příklad 2: Extraction paginace s "Last page" elementem

```python
def extract_category_pages_links(category_page_dom):
    """Extract paginated category links."""
    category_url = get_self_link(category_page_dom)
    page_links = set()

    try:
        # Najít poslední stránku
        last_page_input = category_page_dom.find('input', {'id': 'p-last'})

        if last_page_input:
            last_page_num = int(last_page_input.get('value', 1))
        else:
            # Zkusit najít v pagination links
            pagination_links = category_page_dom.find_all('a', class_='page-link')
            if pagination_links:
                page_numbers = []
                for link in pagination_links:
                    text = link.get_text(strip=True)
                    if text.isdigit():
                        page_numbers.append(int(text))
                last_page_num = max(page_numbers) if page_numbers else 1
            else:
                last_page_num = 1

        # Generovat URL pro všechny stránky
        for page_num in range(1, last_page_num + 1):
            page_url = f"{category_url}?p={page_num}"
            page_links.add(page_url)

        logging.debug(f"Found {len(page_links)} pages for category {category_url}")

    except Exception as e:
        logging.error(f"Error extracting pagination: {e}", exc_info=True)
        # Fallback - alespoň první stránka
        page_links.add(category_url)

    return page_links
```

### Příklad 3: Extraction ceny s různými formáty

```python
def parse_price(price_text):
    """
    Parse price from various formats to float.

    Supports:
    - "€29.99"
    - "$19,99"
    - "299 Kč"
    - "1 299,00 €"

    :param price_text: Price as string
    :return: Price as float
    """
    if not price_text:
        return 0.0

    try:
        import re

        # Remove currency symbols and letters
        price_clean = re.sub(r'[^\d,.\s]', '', price_text)

        # Remove whitespace
        price_clean = price_clean.strip().replace(' ', '')

        # Handle European format (1.299,99 -> 1299.99)
        if ',' in price_clean and '.' in price_clean:
            # Check which is thousands separator
            last_comma = price_clean.rfind(',')
            last_dot = price_clean.rfind('.')

            if last_comma > last_dot:
                # Comma is decimal separator (European)
                price_clean = price_clean.replace('.', '').replace(',', '.')
            else:
                # Dot is decimal separator (US)
                price_clean = price_clean.replace(',', '')
        elif ',' in price_clean:
            # Only comma - assume decimal separator
            price_clean = price_clean.replace(',', '.')

        return float(price_clean)

    except Exception as e:
        logging.warning(f"Could not parse price '{price_text}': {e}")
        return 0.0
```

### Příklad 4: Extraction galerie s lazy loading

```python
def extract_product_gallery_photos(dom_tree):
    """Extract gallery images (handles lazy loading)."""
    gallery_urls = []

    try:
        # Pattern 1: Standard img tags
        gallery_imgs = dom_tree.find_all('img', class_='gallery-image')

        for img in gallery_imgs:
            # Try multiple attributes (lazy loading uses data- attributes)
            img_url = (img.get('src') or
                      img.get('data-src') or
                      img.get('data-original') or
                      img.get('data-lazy'))

            if img_url:
                # Skip placeholder images
                if 'placeholder' not in img_url and 'loading' not in img_url:
                    absolute_url = urljoin(MAIN_URL, img_url)
                    gallery_urls.append(absolute_url)

        # Pattern 2: JSON data attribute
        gallery_data = dom_tree.find('div', {'data-gallery-images': True})
        if gallery_data:
            import json
            gallery_json = gallery_data.get('data-gallery-images')
            if gallery_json:
                images = json.loads(gallery_json)
                for img_url in images:
                    absolute_url = urljoin(MAIN_URL, img_url)
                    gallery_urls.append(absolute_url)

        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in gallery_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        logging.debug(f"Extracted {len(unique_urls)} unique gallery photos")
        return unique_urls

    except Exception as e:
        logging.error(f"Error extracting gallery photos: {e}", exc_info=True)
        return []
```

---

## 14. SPECIÁLNÍ PŘÍPADY

### A. Multi-language E-shops

Pokud e-shop podporuje více jazyků:

**Option 1: Separátní downloadery**
- `butterflyendownloader/` pro anglickou verzi
- `butterflydedownloader/` pro německou verzi

**Option 2: Language parameter**
```python
def parse_arguments():
    parser = ArgumentParser(...)
    parser.add_argument("--language", type=str, default="en",
                       help="Language code (en, de, cs, etc.)")
    return parser.parse_args()

# V constants.py:
def get_main_url(language):
    return {
        'en': 'https://example.com/en/',
        'de': 'https://example.com/de/',
        'cs': 'https://example.com/cs/'
    }.get(language, 'https://example.com/en/')
```

### B. JSON-based E-shops (API)

Pokud e-shop používá JSON API místo HTML:

**Nepoužívat** standardní HTML downloader pattern!
**Použít** speciální pattern jako `pincesobchoddownloader`:
- `json_downloader.py` místo `webpage_downloader.py`
- `json_processor.py` místo HTML extractors
- Přímo parsovat JSON odpovědi

**Kontaktovat maintainera** pro guidance!

### C. Varianty jako separátní produkty

Pokud každá varianta má vlastní URL a je zobrazena jako samostatný produkt:
- **POUŽÍT** `product_variant_detail_link_extractor.py`
- **POUŽÍT** STEP 7b v main() funkci
- Kombinovat product + variant stránky před extraction

### D. Shopify E-shops

Shopify má standardizovanou strukturu:

**URL patterns**:
- Kategorie: `/collections/{category-name}`
- Produkty: `/products/{product-handle}`
- Paginace: `/collections/{category}?page=2`

**JSON data**:
- Produkty mají JSON data: `/products/{handle}.json`
- Kolekce: `/collections/{name}/products.json`

**Selektory** (obvykle):
```python
category_links = soup.select('.site-nav__link[href*="/collections/"]')
product_links = soup.select('.product-card__link')
product_title = soup.select_one('.product-single__title')
price = soup.select_one('.product-single__price')
```

---

## 15. FINÁLNÍ KONTROLA PŘED COMMITEM

### Spustit následující příkazy:

```bash
# 1. Syntax check
python -m py_compile {brand}_downloader.py
python -m py_compile {brand}lib/*.py

# 2. Test run (debug mode)
python {brand}_downloader.py --result_folder H:/Desaka/{Brand}_TEST --debug

# 3. Zkontrolovat výstupy
ls H:/Desaka/{Brand}_TEST/Full_*/
cat H:/Desaka/{Brand}_TEST/Full_*/{Brand}Output.csv | head -5

# 4. Zkontrolovat logy
tail -50 H:/Logs/{brand}_downloader_Log_*.log
```

### Validovat CSV:

```python
import csv

csv_path = "H:/Desaka/{Brand}/Full_{DATE}/{Brand}Output.csv"

with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    header = next(reader)

    # Zkontrolovat header
    expected = ['Name', 'Short Description', 'Description',
                'Main Photo Filepath', 'Gallery Filepaths', 'Variants', 'URL']
    assert header == expected, f"Wrong header: {header}"

    # Zkontrolovat první řádek
    row = next(reader)
    assert len(row) == 7, f"Wrong number of columns: {len(row)}"

    print("✅ CSV validation passed!")
```

---

## 16. KONTAKT A PODPORA

Pokud narazíte na problémy:

1. **Zkontrolujte existující downloadery** - `gewodownloader/`, `nittakudownloader/` jsou good examples
2. **Přečtěte CLAUDE.md** v root složce projektu
3. **Vytvořte GitHub issue** s detaily:
   - Název e-shopu a URL
   - Error message a logy
   - Co jste už zkusili
4. **Tag** relevantní osoby v issue

---

## ZÁVĚR

Tento dokument poskytuje **KOMPLETNÍ specifikaci** pro vytvoření nového downloaderu.

**KLÍČOVÉ BODY**:

1. ✅ **KOPÍROVAT všechny `shared/` moduly BEZ ZMĚN**
2. ✅ **IMPLEMENTOVAT všechny `{brand}lib/` moduly podle templates**
3. ✅ **DODRŽET 10-stupňový proces v main()**
4. ✅ **POUŽÍVAT správné naming conventions**
5. ✅ **TESTOVAT před commitem**

**Pokud dodržíte všechny MANDATORY části, váš downloader bude fungovat korektně a bude konzistentní se zbytkem systému!**

---

**Verze dokumentu**: 1.0
**Datum**: 2024-11-21
**Poslední update**: Initial version based on analysis of all existing downloaders
