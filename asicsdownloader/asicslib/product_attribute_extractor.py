"""
Extracts product attributes from Asics product detail pages.
"""
import logging
import json
import re
from urllib.parse import urljoin
from tqdm import tqdm
from shared.html_loader import load_html_as_dom_tree
from asicslib.constants import MAIN_URL


class Product:
    """Product data model (IDENTICAL structure for all downloaders)."""
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
    """Product variant data model (IDENTICAL structure for all downloaders)."""
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
    # Try canonical tag
    canonical = dom_tree.find('link', rel='canonical')
    if canonical and canonical.get('href'):
        return canonical.get('href')

    # Try og:url meta tag
    og_url = dom_tree.find('meta', property='og:url')
    if og_url and og_url.get('content'):
        return og_url.get('content')

    # Try JSON-LD
    json_ld_product = extract_json_ld_product(dom_tree)
    if json_ld_product and json_ld_product.get('url'):
        return json_ld_product['url']

    return ""


def extract_json_ld_product(dom_tree):
    """
    Extract JSON-LD structured data (Schema.org Product).

    :param dom_tree: BeautifulSoup object
    :return: Dict with product data or None
    """
    try:
        json_ld_scripts = dom_tree.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            if script.string:
                data = json.loads(script.string)

                # Handle single object
                if isinstance(data, dict):
                    if data.get('@type') == 'Product':
                        return data
                    # Handle nested graph structure
                    if data.get('@graph'):
                        for item in data['@graph']:
                            if item.get('@type') == 'Product':
                                return item

                # Handle array
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('@type') == 'Product':
                            return item

    except Exception as e:
        logging.debug(f"Could not extract JSON-LD: {e}")

    return None


def extract_product_name(dom_tree):
    """
    Extract product name.

    :param dom_tree: BeautifulSoup object of product page
    :return: Product name as string
    """
    try:
        # Try JSON-LD first
        json_ld = extract_json_ld_product(dom_tree)
        if json_ld and json_ld.get('name'):
            logging.debug(f"Extracted name from JSON-LD: {json_ld['name']}")
            return json_ld['name']

        # Try common selectors
        selectors = [
            ('h1', {'class': lambda x: x and 'product' in x.lower()}),
            ('h1', {'class': lambda x: x and 'title' in x.lower()}),
            ('h1', {}),
            ('h2', {'class': lambda x: x and 'product' in x.lower()}),
        ]

        for tag, attrs in selectors:
            element = dom_tree.find(tag, attrs)
            if element:
                name = element.get_text(strip=True)
                if name:
                    logging.debug(f"Extracted name: {name}")
                    return name

        # Try og:title
        og_title = dom_tree.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title.get('content')

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
        json_ld = extract_json_ld_product(dom_tree)
        if json_ld and json_ld.get('description'):
            desc = json_ld['description']
            desc = desc.replace('\n', '<br>').replace('\r', '')
            return desc

        # Try common selectors
        selectors = [
            ('div', {'class': lambda x: x and 'short' in x.lower() and 'desc' in x.lower()}),
            ('div', {'class': lambda x: x and 'summary' in x.lower()}),
            ('p', {'class': lambda x: x and 'short' in x.lower()}),
        ]

        for tag, attrs in selectors:
            element = dom_tree.find(tag, attrs)
            if element:
                desc_html = str(element)
                desc_html = desc_html.replace('\n', '<br>').replace('\r', '')
                logging.debug("Extracted short description")
                return desc_html

        # Try meta description
        meta_desc = dom_tree.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc.get('content').replace('\n', '<br>')

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
        # Try common selectors
        selectors = [
            ('div', {'class': lambda x: x and 'description' in x.lower() and 'product' in x.lower()}),
            ('div', {'class': lambda x: x and 'detail' in x.lower()}),
            ('div', {'id': lambda x: x and 'description' in x.lower()}),
            ('div', {'class': lambda x: x and 'content' in x.lower()}),
        ]

        for tag, attrs in selectors:
            element = dom_tree.find(tag, attrs)
            if element:
                desc_html = str(element)
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
        # Try JSON-LD first
        json_ld = extract_json_ld_product(dom_tree)
        if json_ld:
            image = json_ld.get('image')
            if image:
                if isinstance(image, str):
                    absolute_url = urljoin(MAIN_URL, image)
                    logging.debug(f"Extracted main photo from JSON-LD: {absolute_url}")
                    return absolute_url
                elif isinstance(image, list) and len(image) > 0:
                    img_url = image[0] if isinstance(image[0], str) else image[0].get('url')
                    if img_url:
                        absolute_url = urljoin(MAIN_URL, img_url)
                        logging.debug(f"Extracted main photo from JSON-LD: {absolute_url}")
                        return absolute_url
                elif isinstance(image, dict):
                    img_url = image.get('url') or image.get('@id')
                    if img_url:
                        absolute_url = urljoin(MAIN_URL, img_url)
                        logging.debug(f"Extracted main photo from JSON-LD: {absolute_url}")
                        return absolute_url

        # Try common selectors
        selectors = [
            ('img', {'class': lambda x: x and 'main' in x.lower() and 'image' in x.lower()}),
            ('img', {'class': lambda x: x and 'product' in x.lower() and 'image' in x.lower()}),
            ('img', {'class': lambda x: x and 'primary' in x.lower()}),
            ('img', {'id': lambda x: x and 'main' in x.lower()}),
        ]

        for tag, attrs in selectors:
            img_element = dom_tree.find(tag, attrs)
            if img_element:
                img_url = img_element.get('src') or img_element.get('data-src') or img_element.get('data-original')
                if img_url:
                    absolute_url = urljoin(MAIN_URL, img_url)
                    logging.debug(f"Extracted main photo: {absolute_url}")
                    return absolute_url

        # Try og:image
        og_image = dom_tree.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            absolute_url = urljoin(MAIN_URL, og_image.get('content'))
            logging.debug(f"Extracted main photo from og:image: {absolute_url}")
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
        # Try JSON-LD first
        json_ld = extract_json_ld_product(dom_tree)
        if json_ld:
            image = json_ld.get('image')
            if isinstance(image, list):
                for img in image:
                    img_url = img if isinstance(img, str) else (img.get('url') or img.get('@id'))
                    if img_url:
                        absolute_url = urljoin(MAIN_URL, img_url)
                        gallery_urls.append(absolute_url)

        # Try common selectors for gallery
        gallery_containers = dom_tree.find_all(['div', 'ul'], class_=lambda x: x and (
            'gallery' in x.lower() or 'images' in x.lower() or 'thumbnails' in x.lower()
        ))

        for container in gallery_containers:
            images = container.find_all('img')
            for img in images:
                img_url = img.get('src') or img.get('data-src') or img.get('data-original')
                if img_url:
                    # Skip placeholder/loading images
                    if not any(skip in img_url.lower() for skip in ['placeholder', 'loading', 'spinner']):
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

    return gallery_urls


def extract_product_variants(dom_tree):
    """
    Extract product variants (colors, sizes, etc.).

    :param dom_tree: BeautifulSoup object
    :return: List of Variant objects
    """
    variants = []

    try:
        # Try JSON-LD first
        json_ld = extract_json_ld_product(dom_tree)
        if json_ld:
            offers = json_ld.get('offers')
            if offers:
                # Handle single offer
                if isinstance(offers, dict):
                    variant = _create_variant_from_offer(offers)
                    if variant:
                        variants.append(variant)
                # Handle multiple offers
                elif isinstance(offers, list):
                    for offer in offers:
                        variant = _create_variant_from_offer(offer)
                        if variant:
                            variants.append(variant)

        # If no variants from JSON-LD, create simple variant from HTML
        if not variants:
            variant = Variant()

            # Extract price
            price_element = dom_tree.find(['span', 'div'], class_=lambda x: x and 'price' in x.lower())
            if price_element:
                price_text = price_element.get_text(strip=True)
                price = parse_price(price_text)
                variant.current_price = price
                variant.basic_price = price

            # Extract stock status
            stock_element = dom_tree.find(['span', 'div'], class_=lambda x: x and (
                'stock' in x.lower() or 'availability' in x.lower()
            ))
            if stock_element:
                variant.stock_status = stock_element.get_text(strip=True)
            else:
                variant.stock_status = "In stock"  # Default assumption

            variants.append(variant)

        logging.debug(f"Extracted {len(variants)} variants")

    except Exception as e:
        logging.error(f"Error extracting variants: {e}", exc_info=True)

    return variants


def _create_variant_from_offer(offer):
    """
    Create a Variant object from a JSON-LD offer.

    :param offer: Dict representing an offer
    :return: Variant object or None
    """
    try:
        variant = Variant()

        # Extract price
        price = offer.get('price')
        if price:
            variant.current_price = float(price)
            variant.basic_price = float(price)

        # Extract availability
        availability = offer.get('availability', '')
        if 'InStock' in availability:
            variant.stock_status = "In stock"
        elif 'OutOfStock' in availability:
            variant.stock_status = "Out of stock"
        else:
            variant.stock_status = availability

        # Extract variant properties (color, size, etc.)
        # These might be in different fields depending on the schema
        for key in ['name', 'sku', 'itemOffered']:
            if key in offer and offer[key]:
                variant.key_value_pairs[key] = str(offer[key])

        return variant

    except Exception as e:
        logging.debug(f"Error creating variant from offer: {e}")
        return None


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
