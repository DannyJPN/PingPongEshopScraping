# product_attribute_extractor.py
import os
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from shared.image_downloader import download_image
from shared.utils import sanitize_filename
from shared.html_loader import load_html_as_dom_tree
from tqdm import tqdm
import json
from nittakulib.constants import MAIN_URL
import re

class Product:
    def __init__(self):
        self.name = ""
        self.short_description = ""
        self.description = ""
        self.variants = []
        self.main_photo_link = ""
        self.photogallery_links = set()
        self.main_photo_filepath = ""
        self.photogallery_filepaths = []
        self.url=""

class Variant:
    def __init__(self, key_value_pairs, current_price, basic_price, stock_status):
        self.key_value_pairs = key_value_pairs
        self.current_price = current_price
        self.basic_price = basic_price
        self.stock_status = stock_status

def get_self_link(category_page_dom):
    """
    Extracts the self link URL from the category page HTML DOM.

    :param category_page_dom: BeautifulSoup object of the category page HTML.
    :return: The longest self link URL as a string.
    """
    try:
        script_tags = category_page_dom.find_all('script', type='application/ld+json')
        logging.debug(f"Found {len(script_tags)} <script type='application/ld+json'> elements.")
        valid_urls = []

        for script_tag in script_tags:
            try:
                json_content = json.loads(script_tag.string)
                logging.debug(f"JSON content: {json_content}")
                item_list = json_content.get('itemListElement', [])
                for item in item_list:
                    self_link = item.get('item')
                    logging.debug(f"Self link found: {self_link}")
                    if self_link and self_link.startswith(MAIN_URL) and self_link != MAIN_URL:
                        valid_urls.append(self_link)
                        logging.debug(f"Valid self link found: {self_link}")
            except json.JSONDecodeError as e:
                logging.error(f"Error decoding JSON from script tag: {e}", exc_info=True)

        if valid_urls:
            longest_url = max(valid_urls, key=len)
            logging.debug(f"Longest self link selected: {longest_url}")
            return longest_url
        else:
            logging.error("No valid self link found.")
            return None
    except Exception as e:
        logging.error(f"Error extracting self link: {e}", exc_info=True)
        return None

def extract_product_name(dom_tree):
    """
    Extracts the product name from the product detail page HTML DOM.

    :param dom_tree: BeautifulSoup object of the product detail page HTML.
    :return: The product name as a string.
    """
    try:
        product_name_element = dom_tree.find('h1', class_='product-meta__title heading h1')
        if product_name_element:
            # Extract text content and remove any HTML tags
            product_name = ''.join(product_name_element.stripped_strings)
            product_name = re.sub(r'<[^>]+>', '', product_name).strip()
            logging.debug(f"Product name extracted: {product_name}")
            return product_name
        else:
            logging.error("Product name element not found.")
            return None
    except Exception as e:
        logging.error(f"Error extracting product name: {e}", exc_info=True)
        return None

def extract_product_link(dom_tree):
    return get_self_link(dom_tree)

def extract_product_short_description(dom_tree):
    """
    Extracts the product short description from the product detail page HTML DOM.

    :param dom_tree: BeautifulSoup object of the product detail page HTML.
    :return: The product short description as a string containing HTML.
    """
    try:
        short_desc_container = dom_tree.find('div', class_='rte text--pull')
        if short_desc_container:
            # Find the first child element that is either a <p>, <div>, or header element
            for child in short_desc_container.children:
                if child.name in ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    short_description_html = str(child)
                    # Replace newline characters with spaces
                    short_description_html = short_description_html.replace('\n', ' ')
                    logging.debug(f"Product short description extracted: {short_description_html}")
                    return short_description_html
        logging.error("Product short description element not found.")
        return None
    except Exception as e:
        logging.error(f"Error extracting product short description: {e}", exc_info=True)
        return None

def extract_product_description(dom_tree):
    """
    Extracts the product description from the product detail page HTML DOM.

    :param dom_tree: BeautifulSoup object of the product detail page HTML.
    :return: The product description as a string containing HTML.
    """
    try:
        description_container = dom_tree.find('div', class_='rte text--pull')
        if description_container:
            # Extract the inner HTML content of the description container
            description_html = str(description_container)
            # Replace newline characters with spaces
            description_html = description_html.replace('\n', ' ')
            logging.debug(f"Product description extracted: {description_html}")
            return description_html
        logging.error("Product description element not found.")
        return None
    except Exception as e:
        logging.error(f"Error extracting product description: {e}", exc_info=True)
        return None

def extract_product_variants(dom_tree):
    """
    Extracts the product variants from the product detail page HTML DOM.

    :param dom_tree: BeautifulSoup object of the product detail page HTML.
    :return: A list of Variant objects.
    """
    try:
        variants = []
        variant_containers = dom_tree.find_all('div', class_='product-form__option')
        for container in variant_containers:
            key_element = container.find('span', class_='product-form__option-name text--strong')
            if key_element:
                key = ''.join(key_element.stripped_strings).split(':')[0].strip()
                values = []
                value_elements = container.find_all('span', class_='block-swatch__item-text')
                for value_element in value_elements:
                    value = ''.join(value_element.stripped_strings).strip()
                    values.append(value)

                # Create key-value pairs
                key_value_pairs = [(key, value) for value in values]

                # Placeholder for current price and basic price
                current_price = ""
                basic_price = ""

                # Extract stock status
                stock_status = ""
                availability_script = dom_tree.find('script', text=re.compile('var availability_txt'))
                if availability_script:
                    availability_text = availability_script.string
                    availability_match = re.search(r'availability_txt\s*=\s*(\[[^\]]+\])', availability_text)
                    if availability_match:
                        availability_json = json.loads(availability_match.group(1))
                        stock_status = availability_json[0] if availability_json else ""

                variant = Variant(key_value_pairs, current_price, basic_price, stock_status)
                variants.append(variant)
                logging.debug(f"Variant extracted: {variant.__dict__}")
        return variants
    except Exception as e:
        logging.error(f"Error extracting product variants: {e}", exc_info=True)
        return []

def extract_product_main_photo_link(dom_tree):
    """
    Extracts the main photo link from the product detail page HTML DOM.

    :param dom_tree: BeautifulSoup object of the product detail page HTML.
    :return: The main photo link as a string.
    """
    try:
        image_elements = dom_tree.find_all('img', class_=lambda x: x and 'product-gallery__image' in x and 'image--blur-up' in x)

        # Log the number of image elements found
        logging.debug(f"Number of image elements found: {len(image_elements)}")

        for img in image_elements:
            logging.debug(f"Image element: {img}")
            logging.debug(f"Image element classes: {img.get('class')}")
            logging.debug(f"Image element data-zoom: {img.get('data-zoom')}")

        main_photo_element = image_elements[0] if image_elements else None
        if main_photo_element:
            main_photo_link = main_photo_element.get('data-zoom')
            if main_photo_link and main_photo_link.startswith('//'):
                main_photo_link = 'https:' + main_photo_link
            logging.debug(f"Main photo link extracted: {main_photo_link}")
            return main_photo_link
        else:
            logging.error("Main photo element not found.")
            return None
    except Exception as e:
        logging.error(f"Error extracting main photo link: {e}", exc_info=True)
        return None

def extract_product_photogallery_links(dom_tree):
    """
    Extracts the product photogallery links from the product detail page HTML DOM.

    :param dom_tree: BeautifulSoup object of the product detail page HTML.
    :return: A set of photogallery links as strings.
    """
    try:
        photogallery_links = set()
        image_elements = dom_tree.find_all('img', class_=lambda x: x and 'product-gallery__image' in x and 'image--blur-up' in x)
        # Skip the first image element which is the main photo
        for image_element in image_elements[1:]:
            data_zoom = image_element.get('data-zoom')
            if data_zoom:
                # Ensure the URL includes the scheme
                if data_zoom.startswith('//'):
                    data_zoom = 'https:' + data_zoom
                photogallery_links.add(data_zoom)
        logging.debug(f"Product photogallery links extracted: {photogallery_links}")
        return photogallery_links
    except Exception as e:
        logging.error(f"Error extracting product photogallery links: {e}", exc_info=True)
        return set()

def extract_product(filepath):
    try:
        # Ensure the filepath is absolute
        filepath = os.path.abspath(filepath)
        logging.debug(f"Extracting product from {filepath}")

        dom_tree = load_html_as_dom_tree(filepath)
        product = Product()
        product.name = extract_product_name(dom_tree)
        product.short_description = extract_product_short_description(dom_tree)
        product.description = extract_product_description(dom_tree)
        product.variants = extract_product_variants(dom_tree)
        product.main_photo_link = extract_product_main_photo_link(dom_tree)
        product.photogallery_links = extract_product_photogallery_links(dom_tree)
        product.url = extract_product_link(dom_tree)

        return product

    except Exception as e:
        logging.error(f"Error extracting product from {filepath}: {e}", exc_info=True)
        return None

def extract_products(product_detail_page_paths):
    products = []
    with tqdm(total=len(product_detail_page_paths), desc="Extracting products") as pbar:
        for product_detail_page_path in product_detail_page_paths:
            product = extract_product(product_detail_page_path)
            if product:
                products.append(product)
            pbar.update(1)
    return products