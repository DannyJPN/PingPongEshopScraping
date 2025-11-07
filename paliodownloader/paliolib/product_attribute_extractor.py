"""
Extracts product attributes from Palio product detail pages.

Palio uses Shopify platform - utilizes Shopify standard structure:
- Product JSON data in page
- Standard Shopify CSS selectors
- Meta tags (og:*, twitter:*)
"""
import json
import logging
import re
from urllib.parse import urljoin
from tqdm import tqdm
from shared.html_loader import load_html_as_dom_tree
from paliolib.constants import MAIN_URL


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


def extract_shopify_product_json(dom_tree):
    """
    Extract Shopify product JSON data from page.

    Shopify embeds product data in <script type="application/json"> or <script type="application/ld+json">

    :param dom_tree: BeautifulSoup object
    :return: Dict with product data or None
    """
    try:
        # Try Shopify product JSON
        scripts = dom_tree.find_all('script', type='application/json')
        for script in scripts:
            if script.string and 'product' in script.string.lower():
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'product' in data:
                        return data['product']
                    if 'title' in data and 'variants' in data:
                        return data
                except:
                    continue

        # Try JSON-LD structured data
        json_ld_scripts = dom_tree.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            if script.string:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('@type') == 'Product':
                        return data
                except:
                    continue

        return None
    except Exception as e:
        logging.debug(f"Could not extract Shopify JSON: {e}")
        return None


def extract_product_name(dom_tree):
    """
    Extract product name using multiple methods.

    :param dom_tree: BeautifulSoup object of product page
    :return: Product name as string
    """
    try:
        # Try Shopify JSON first
        product_json = extract_shopify_product_json(dom_tree)
        if product_json and 'title' in product_json:
            return product_json['title']
        if product_json and 'name' in product_json:
            return product_json['name']

        # Try Shopify standard selectors
        name_element = (
            dom_tree.find('h1', class_=lambda x: x and 'product' in x.lower() and 'title' in x.lower()) or
            dom_tree.select_one('.product-single__title') or
            dom_tree.select_one('.product__title') or
            dom_tree.select_one('.product-title') or
            dom_tree.find('h1')
        )

        if name_element:
            name = name_element.get_text(strip=True)
            logging.debug(f"Extracted name: {name}")
            return name

        # Fallback to og:title
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
        # Try meta description
        meta_desc = dom_tree.find('meta', {'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc.get('content', '')

        # Try og:description
        og_desc = dom_tree.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc.get('content', '')

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
        # Shopify product description selectors
        desc_element = (
            dom_tree.find('div', class_=lambda x: x and 'product' in x.lower() and 'description' in x.lower()) or
            dom_tree.select_one('.product-single__description') or
            dom_tree.select_one('.product__description') or
            dom_tree.select_one('.product-description') or
            dom_tree.find('div', class_=lambda x: x and 'description' in x.lower())
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
        # Try og:image first (usually best quality)
        og_image = dom_tree.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            img_url = og_image.get('content', '')
            if img_url and not img_url.startswith('data:'):
                absolute_url = urljoin(MAIN_URL, img_url)
                logging.debug(f"Extracted main photo from og:image: {absolute_url}")
                return absolute_url

        # Try Shopify product image selectors
        img_element = (
            dom_tree.select_one('.product-single__photo img') or
            dom_tree.select_one('.product__main-photos img') or
            dom_tree.select_one('.product-featured-img') or
            dom_tree.find('img', class_=lambda x: x and 'product' in x.lower() and ('main' in x.lower() or 'featured' in x.lower()))
        )

        if img_element:
            img_url = img_element.get('src') or img_element.get('data-src') or img_element.get('data-original')
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
        # Shopify thumbnail/gallery selectors
        gallery_elements = (
            dom_tree.select('.product-single__thumbnails img') +
            dom_tree.select('.product__thumbs img') +
            dom_tree.select('.product-thumbnails img') +
            dom_tree.find_all('img', class_=lambda x: x and 'product' in x.lower() and ('thumb' in x.lower() or 'gallery' in x.lower()))
        )

        for img in gallery_elements:
            img_url = img.get('src') or img.get('data-src') or img.get('data-original')
            if img_url and not img_url.startswith('data:'):
                # Skip placeholder and icon images
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
    Extract product variants (sizes, colors, etc.) from Shopify product.

    :param dom_tree: BeautifulSoup object
    :return: List of Variant objects
    """
    variants = []

    try:
        # Try to extract from Shopify JSON first
        product_json = extract_shopify_product_json(dom_tree)
        if product_json and 'variants' in product_json:
            json_variants = product_json['variants']
            for json_var in json_variants:
                variant = Variant()

                # Extract variant options (size, color, etc.)
                if 'option1' in json_var and json_var['option1']:
                    variant.key_value_pairs['Option 1'] = json_var['option1']
                if 'option2' in json_var and json_var['option2']:
                    variant.key_value_pairs['Option 2'] = json_var['option2']
                if 'option3' in json_var and json_var['option3']:
                    variant.key_value_pairs['Option 3'] = json_var['option3']

                # Extract price
                if 'price' in json_var:
                    variant.current_price = float(json_var['price']) / 100  # Shopify stores in cents
                if 'compare_at_price' in json_var and json_var['compare_at_price']:
                    variant.basic_price = float(json_var['compare_at_price']) / 100
                else:
                    variant.basic_price = variant.current_price

                # Extract stock status
                if 'available' in json_var:
                    variant.stock_status = "In stock" if json_var['available'] else "Out of stock"
                else:
                    variant.stock_status = "Unknown"

                variants.append(variant)

            if variants:
                logging.debug(f"Extracted {len(variants)} variants from JSON")
                return variants

        # Fallback: Extract from HTML selectors
        variant = Variant()

        # Extract price from HTML
        price_elements = (
            dom_tree.select('.product-single__price') +
            dom_tree.select('.product__price') +
            dom_tree.find_all('span', class_=lambda x: x and 'price' in x.lower())
        )

        if price_elements:
            # Try to find sale/current price
            for price_el in price_elements:
                if 'sale' in price_el.get('class', []) or 'current' in str(price_el.get('class', [])).lower():
                    variant.current_price = parse_price(price_el.get_text())
                    break
            else:
                # Use first price found
                variant.current_price = parse_price(price_elements[0].get_text())

            # Try to find compare/original price
            for price_el in price_elements:
                if 'compare' in str(price_el.get('class', [])).lower() or 'original' in str(price_el.get('class', [])).lower():
                    variant.basic_price = parse_price(price_el.get_text())
                    break
            else:
                variant.basic_price = variant.current_price

        # Extract stock status
        stock_element = dom_tree.find(class_=lambda x: x and 'stock' in x.lower())
        if stock_element:
            stock_text = stock_element.get_text(strip=True).lower()
            if 'in stock' in stock_text or 'available' in stock_text:
                variant.stock_status = "In stock"
            elif 'out of stock' in stock_text or 'sold out' in stock_text:
                variant.stock_status = "Out of stock"
            else:
                variant.stock_status = stock_text
        else:
            variant.stock_status = "Available"

        variants.append(variant)
        logging.debug(f"Extracted {len(variants)} variants from HTML")

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
