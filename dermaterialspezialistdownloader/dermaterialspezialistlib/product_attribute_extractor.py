"""
Extracts product attributes from Der Materialspezialist product detail pages.

Der Materialspezialist uses Shopware/WooCommerce platform - German e-commerce:
- JSON-LD structured data extraction (Schema.org Product)
- Shopware standard CSS selectors and data attributes
- WooCommerce standard classes and meta tags
- German language price and stock patterns
"""
import json
import logging
import re
from urllib.parse import urljoin
from tqdm import tqdm
from shared.html_loader import load_html_as_dom_tree
from dermaterialspezialistlib.constants import MAIN_URL


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
    try:
        # Pattern 1: canonical tag
        canonical = dom_tree.find('link', rel='canonical')
        if canonical:
            return canonical.get('href', '')

        # Pattern 2: og:url meta tag
        og_url = dom_tree.find('meta', property='og:url')
        if og_url:
            return og_url.get('content', '')

        return ""
    except Exception as e:
        logging.error(f"Error extracting canonical URL: {e}", exc_info=True)
        return ""


def extract_json_ld_product(dom_tree):
    """
    Extract JSON-LD structured data (Schema.org Product).

    Common in German e-commerce (Shopware, WooCommerce, etc.)

    :param dom_tree: BeautifulSoup object
    :return: Dict with product data or None
    """
    try:
        # Find JSON-LD structured data
        json_ld_scripts = dom_tree.find_all('script', type='application/ld+json')

        for script in json_ld_scripts:
            if script.string:
                try:
                    data = json.loads(script.string)

                    # Handle single object
                    if isinstance(data, dict):
                        if data.get('@type') == 'Product':
                            return data
                        # Sometimes nested in @graph
                        if '@graph' in data:
                            for item in data['@graph']:
                                if isinstance(item, dict) and item.get('@type') == 'Product':
                                    return item

                    # Handle array
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get('@type') == 'Product':
                                return item

                except json.JSONDecodeError:
                    continue

        return None

    except Exception as e:
        logging.debug(f"Could not extract JSON-LD: {e}")
        return None


def extract_product_name(dom_tree):
    """
    Extract product name using multiple methods.

    :param dom_tree: BeautifulSoup object of product page
    :return: Product name as string
    """
    try:
        # Try JSON-LD first (most reliable)
        product_json = extract_json_ld_product(dom_tree)
        if product_json and 'name' in product_json:
            return product_json['name']

        # Try Shopware/WooCommerce standard selectors
        name_element = (
            # Shopware patterns
            dom_tree.select_one('.product--title') or
            dom_tree.select_one('.product-detail-name') or
            dom_tree.select_one('.product-name') or
            # WooCommerce patterns
            dom_tree.select_one('.product_title') or
            dom_tree.select_one('h1.entry-title') or
            # Generic German patterns
            dom_tree.find('h1', class_=lambda x: x and ('product' in x.lower() or 'produkt' in x.lower())) or
            dom_tree.find('h1', class_=lambda x: x and 'title' in x.lower()) or
            # Fallback to any h1
            dom_tree.find('h1')
        )

        if name_element:
            name = name_element.get_text(strip=True)
            logging.debug(f"Extracted name: {name}")
            return name

        # Try og:title meta tag
        og_title = dom_tree.find('meta', property='og:title')
        if og_title:
            return og_title.get('content', '')

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
        # Try JSON-LD first
        product_json = extract_json_ld_product(dom_tree)
        if product_json and 'description' in product_json:
            # JSON-LD description is often the short one
            desc = product_json['description']
            if len(desc) < 500:  # Short description heuristic
                return desc

        # Try meta description
        meta_desc = dom_tree.find('meta', {'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc.get('content', '')

        # Try og:description
        og_desc = dom_tree.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc.get('content', '')

        # Try Shopware/WooCommerce short description patterns
        desc_element = (
            dom_tree.select_one('.product--description-short') or
            dom_tree.select_one('.product-short-description') or
            dom_tree.select_one('.woocommerce-product-details__short-description') or
            dom_tree.find('div', class_=lambda x: x and 'short' in x.lower() and 'desc' in x.lower())
        )

        if desc_element:
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
        # Try Shopware/WooCommerce description patterns
        desc_element = (
            # Shopware patterns
            dom_tree.select_one('.product--description') or
            dom_tree.select_one('.product-detail--description') or
            dom_tree.select_one('[itemprop="description"]') or
            # WooCommerce patterns
            dom_tree.select_one('.woocommerce-Tabs-panel--description') or
            dom_tree.select_one('#tab-description') or
            # Generic patterns
            dom_tree.find('div', class_=lambda x: x and 'description' in x.lower() and ('product' in x.lower() or 'produkt' in x.lower())) or
            dom_tree.find('div', class_=lambda x: x and 'beschreibung' in x.lower()) or
            dom_tree.find('div', id=lambda x: x and ('description' in x.lower() or 'beschreibung' in x.lower()))
        )

        if desc_element:
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
        # Try JSON-LD first (highest quality)
        product_json = extract_json_ld_product(dom_tree)
        if product_json and 'image' in product_json:
            image = product_json['image']
            # Can be string or array
            if isinstance(image, str):
                img_url = image
            elif isinstance(image, list) and len(image) > 0:
                img_url = image[0] if isinstance(image[0], str) else image[0].get('url', '')
            elif isinstance(image, dict):
                img_url = image.get('url', '')
            else:
                img_url = None

            if img_url and not img_url.startswith('data:'):
                absolute_url = urljoin(MAIN_URL, img_url)
                logging.debug(f"Extracted main photo from JSON-LD: {absolute_url}")
                return absolute_url

        # Try og:image (usually best quality)
        og_image = dom_tree.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            img_url = og_image.get('content', '')
            if img_url and not img_url.startswith('data:'):
                absolute_url = urljoin(MAIN_URL, img_url)
                logging.debug(f"Extracted main photo from og:image: {absolute_url}")
                return absolute_url

        # Try Shopware/WooCommerce image patterns
        img_element = (
            # Shopware patterns
            dom_tree.select_one('.product--image img') or
            dom_tree.select_one('.image-slider--item img') or
            dom_tree.select_one('[itemprop="image"]') or
            # WooCommerce patterns
            dom_tree.select_one('.woocommerce-product-gallery__image img') or
            dom_tree.select_one('.product-image img') or
            # Generic patterns
            dom_tree.find('img', class_=lambda x: x and ('product' in x.lower() or 'produkt' in x.lower())) or
            dom_tree.find('img', class_=lambda x: x and 'main' in x.lower())
        )

        if img_element:
            img_url = (
                img_element.get('src') or
                img_element.get('data-src') or
                img_element.get('data-original') or
                img_element.get('data-lazy-src')
            )
            if img_url and not img_url.startswith('data:'):
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
        # Try Shopware/WooCommerce gallery patterns
        gallery_elements = (
            # Shopware patterns
            dom_tree.select('.image-slider--item img') +
            dom_tree.select('.product--image-thumbnails img') +
            # WooCommerce patterns
            dom_tree.select('.woocommerce-product-gallery__image img') +
            dom_tree.select('.product-thumbnails img') +
            # Generic patterns
            dom_tree.find_all('img', class_=lambda x: x and ('gallery' in x.lower() or 'thumbnail' in x.lower() or 'thumb' in x.lower())) +
            dom_tree.find_all('img', class_=lambda x: x and ('product' in x.lower() or 'produkt' in x.lower()))
        )

        for img in gallery_elements:
            img_url = (
                img.get('src') or
                img.get('data-src') or
                img.get('data-original') or
                img.get('data-lazy-src')
            )
            if img_url and not img_url.startswith('data:'):
                # Skip placeholder and icon images
                if not any(x in img_url.lower() for x in ['placeholder', 'icon', 'logo', 'sprite']):
                    absolute_url = urljoin(MAIN_URL, img_url)
                    gallery_urls.append(absolute_url)

        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in gallery_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        logging.debug(f"Extracted {len(unique_urls)} gallery photos")
        return unique_urls

    except Exception as e:
        logging.error(f"Error extracting gallery photos: {e}", exc_info=True)
        return []


def parse_price(price_text):
    """
    Parse price from text to float.

    :param price_text: Price as string (e.g., "€29.99", "$19,99", "299 Kč")
    :return: Price as float
    """
    if not price_text:
        return 0.0

    try:
        # Remove currency symbols and letters
        price_clean = re.sub(r'[^\d,.\s]', '', str(price_text))
        # Remove whitespace
        price_clean = price_clean.strip().replace(' ', '')

        # Handle European format (1.299,99 -> 1299.99)
        if ',' in price_clean and '.' in price_clean:
            last_comma = price_clean.rfind(',')
            last_dot = price_clean.rfind('.')
            if last_comma > last_dot:
                # Comma is decimal separator
                price_clean = price_clean.replace('.', '').replace(',', '.')
            else:
                # Dot is decimal separator
                price_clean = price_clean.replace(',', '')
        elif ',' in price_clean:
            # Only comma - assume decimal separator
            price_clean = price_clean.replace(',', '.')

        return float(price_clean)
    except:
        return 0.0


def extract_product_variants(dom_tree):
    """
    Extract product variants (colors, sizes, etc.) from Shopware/WooCommerce.

    :param dom_tree: BeautifulSoup object
    :return: List of Variant objects
    """
    variants = []

    try:
        # Try JSON-LD first for structured offers data
        product_json = extract_json_ld_product(dom_tree)
        if product_json and 'offers' in product_json:
            offers = product_json['offers']

            # Handle single offer
            if isinstance(offers, dict):
                offers = [offers]

            # Handle multiple offers (variants)
            if isinstance(offers, list):
                for offer in offers:
                    variant = Variant()

                    # Extract price from JSON-LD
                    if 'price' in offer:
                        variant.current_price = float(offer['price'])
                        variant.basic_price = variant.current_price

                    # Handle price specifications
                    if 'priceSpecification' in offer:
                        price_spec = offer['priceSpecification']
                        if 'price' in price_spec:
                            variant.current_price = float(price_spec['price'])

                    # Extract stock status
                    if 'availability' in offer:
                        availability = offer['availability']
                        if 'InStock' in availability:
                            variant.stock_status = "In stock"
                        elif 'OutOfStock' in availability:
                            variant.stock_status = "Out of stock"
                        elif 'LimitedAvailability' in availability:
                            variant.stock_status = "Limited stock"
                        else:
                            variant.stock_status = "Available"
                    else:
                        variant.stock_status = "Available"

                    variants.append(variant)

                if variants:
                    logging.debug(f"Extracted {len(variants)} variants from JSON-LD")
                    return variants

        # Fallback: Try to extract from HTML selectors
        # Pattern 1: Shopware/WooCommerce variant select boxes
        variant_selects = (
            dom_tree.select('select.product-variant') +
            dom_tree.select('select[name*="attribute"]') +
            dom_tree.select('select.variations select') +
            dom_tree.find_all('select', class_=lambda x: x and ('variant' in x.lower() or 'variante' in x.lower() or 'option' in x.lower()))
        )

        if variant_selects:
            # Complex variant extraction (multiple select boxes)
            # This creates a variant for each combination - simplified to just list all options
            variant_options = {}

            for select in variant_selects:
                option_name = select.get('name', select.get('id', 'Option'))
                option_name = option_name.replace('attribute', '').replace('[]', '').strip('_')

                options = []
                for option in select.find_all('option'):
                    value = option.get('value')
                    text = option.get_text(strip=True)
                    if value and text and text.lower() not in ['', 'select', 'wählen', 'choose']:
                        options.append(text)

                if options:
                    variant_options[option_name] = options

            # If we found variant options, create a single variant with first options
            if variant_options:
                variant = Variant()
                for key, values in variant_options.items():
                    variant.key_value_pairs[key] = values[0] if values else ""

                # Extract price and stock
                variant.current_price = _extract_price_from_html(dom_tree)
                variant.basic_price = variant.current_price
                variant.stock_status = _extract_stock_status(dom_tree)

                variants.append(variant)
        else:
            # Simple product without variants - create default variant
            variant = Variant()

            # Extract price
            variant.current_price = _extract_price_from_html(dom_tree)
            variant.basic_price = variant.current_price

            # Extract stock status
            variant.stock_status = _extract_stock_status(dom_tree)

            variants.append(variant)

        logging.debug(f"Extracted {len(variants)} variants")

    except Exception as e:
        logging.error(f"Error extracting variants: {e}", exc_info=True)
        # Create a default variant as fallback
        if not variants:
            variant = Variant()
            variant.stock_status = "Unknown"
            variants.append(variant)

    return variants


def _extract_price_from_html(dom_tree):
    """
    Helper function to extract price from HTML.

    :param dom_tree: BeautifulSoup object
    :return: Price as float
    """
    try:
        # Shopware/WooCommerce price patterns
        price_elements = (
            dom_tree.select('.product--price') +
            dom_tree.select('.price .amount') +
            dom_tree.select('[itemprop="price"]') +
            dom_tree.select('.woocommerce-Price-amount') +
            dom_tree.find_all('span', class_=lambda x: x and 'price' in x.lower() and 'preis' not in x.lower())
        )

        if price_elements:
            # Try to find current/sale price first
            for price_el in price_elements:
                classes = price_el.get('class', [])
                if any(x in str(classes).lower() for x in ['sale', 'current', 'special', 'angebot']):
                    return parse_price(price_el.get_text())

            # Use first price found
            return parse_price(price_elements[0].get_text())

        return 0.0

    except Exception as e:
        logging.debug(f"Error extracting price from HTML: {e}")
        return 0.0


def _extract_stock_status(dom_tree):
    """
    Helper function to extract stock status from HTML.

    :param dom_tree: BeautifulSoup object
    :return: Stock status as string
    """
    try:
        # Shopware/WooCommerce stock patterns (German/English)
        stock_element = (
            dom_tree.select_one('.product--delivery') or
            dom_tree.select_one('[itemprop="availability"]') or
            dom_tree.select_one('.stock') or
            dom_tree.find(class_=lambda x: x and ('stock' in x.lower() or 'lieferbar' in x.lower() or 'verfügbar' in x.lower()))
        )

        if stock_element:
            stock_text = stock_element.get_text(strip=True).lower()

            # German patterns
            if any(x in stock_text for x in ['auf lager', 'lieferbar', 'verfügbar', 'sofort']):
                return "In stock"
            elif any(x in stock_text for x in ['nicht lieferbar', 'ausverkauft', 'nicht verfügbar']):
                return "Out of stock"

            # English patterns
            elif any(x in stock_text for x in ['in stock', 'available']):
                return "In stock"
            elif any(x in stock_text for x in ['out of stock', 'sold out', 'unavailable']):
                return "Out of stock"

            # Return the text as-is if no pattern matches
            return stock_text.capitalize()

        return "Available"

    except Exception as e:
        logging.debug(f"Error extracting stock status: {e}")
        return "Unknown"


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
