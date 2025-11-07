"""
Extracts product attributes from Donic product detail pages.
"""
import logging
import re
from urllib.parse import urljoin
from tqdm import tqdm
from shared.html_loader import load_html_as_dom_tree
from doniclib.constants import MAIN_URL


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


def extract_product_name(dom_tree):
    """
    Extract product name.

    :param dom_tree: BeautifulSoup object of product page
    :return: Product name as string
    """
    try:
        # Try multiple common patterns
        name_element = (
            dom_tree.find('h1', class_=lambda x: x and 'product' in x.lower()) or
            dom_tree.find('h1', class_=lambda x: x and 'title' in x.lower()) or
            dom_tree.find('h1') or
            dom_tree.find('meta', property='og:title')
        )

        if name_element:
            if name_element.name == 'meta':
                name = name_element.get('content', '')
            else:
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
        # Try meta description first
        meta_desc = dom_tree.find('meta', {'name': 'description'})
        if meta_desc:
            desc = meta_desc.get('content', '')
            if desc:
                logging.debug("Extracted short description from meta tag")
                return desc

        # Try common short description patterns
        desc_element = (
            dom_tree.find('div', class_=lambda x: x and 'short' in x.lower() and 'desc' in x.lower()) or
            dom_tree.find('p', class_=lambda x: x and 'product' in x.lower() and 'desc' in x.lower())
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
        # Try common description patterns
        desc_element = (
            dom_tree.find('div', class_=lambda x: x and 'description' in x.lower() and 'product' in x.lower()) or
            dom_tree.find('div', class_=lambda x: x and 'desc' in x.lower()) or
            dom_tree.find('div', id=lambda x: x and 'description' in x.lower())
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
        # Try og:image first (usually the main image)
        og_image = dom_tree.find('meta', property='og:image')
        if og_image:
            img_url = og_image.get('content', '')
            if img_url:
                absolute_url = urljoin(MAIN_URL, img_url)
                logging.debug(f"Extracted main photo from og:image: {absolute_url}")
                return absolute_url

        # Try common product image patterns
        img_element = (
            dom_tree.find('img', class_=lambda x: x and ('product' in x.lower() or 'main' in x.lower())) or
            dom_tree.find('img', id=lambda x: x and 'product' in x.lower())
        )

        if img_element:
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
        # Try common gallery patterns
        gallery_elements = (
            dom_tree.find_all('img', class_=lambda x: x and ('gallery' in x.lower() or 'thumbnail' in x.lower())) or
            dom_tree.find_all('img', class_=lambda x: x and 'product' in x.lower())
        )

        for img in gallery_elements:
            img_url = img.get('src') or img.get('data-src') or img.get('data-original')
            if img_url:
                # Skip placeholders and icons
                if 'placeholder' not in img_url.lower() and 'icon' not in img_url.lower():
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
    Extract product variants (colors, sizes, etc.).

    :param dom_tree: BeautifulSoup object
    :return: List of Variant objects
    """
    variants = []

    try:
        # Try to find variant selectors
        variant_selects = dom_tree.find_all('select', class_=lambda x: x and ('variant' in x.lower() or 'option' in x.lower()))

        if variant_selects:
            # Complex variant extraction (multiple select boxes)
            for select in variant_selects:
                option_name = select.get('name', 'Variant')
                for option in select.find_all('option'):
                    if option.get('value'):
                        variant = Variant()
                        variant.key_value_pairs[option_name] = option.get_text(strip=True)

                        # Extract price (usually same for all variants or specified per variant)
                        price_element = dom_tree.find('span', class_=lambda x: x and 'price' in x.lower())
                        if price_element:
                            price = parse_price(price_element.get_text())
                            variant.current_price = price
                            variant.basic_price = price

                        variant.stock_status = "Available"
                        variants.append(variant)
        else:
            # Simple product without variants - create default variant
            variant = Variant()

            # Extract price
            price_elements = dom_tree.find_all('span', class_=lambda x: x and 'price' in x.lower())
            if price_elements:
                # Try to find current and basic price
                if len(price_elements) >= 2:
                    variant.current_price = parse_price(price_elements[0].get_text())
                    variant.basic_price = parse_price(price_elements[1].get_text())
                else:
                    price = parse_price(price_elements[0].get_text())
                    variant.current_price = price
                    variant.basic_price = price

            # Extract stock status
            stock_element = dom_tree.find(class_=lambda x: x and 'stock' in x.lower())
            if stock_element:
                variant.stock_status = stock_element.get_text(strip=True)
            else:
                variant.stock_status = "Available"

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
