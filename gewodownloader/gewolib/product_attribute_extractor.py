# product_attribute_extractor.py
import os
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from shared.image_downloader import download_image
from shared.utils import sanitize_filename
from shared.html_loader import load_html_as_dom_tree
from tqdm import tqdm


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
        # Ensure key_value_pairs is a dictionary with string values, not lists
        self.key_value_pairs = {}
        for key, value in key_value_pairs.items():
            if isinstance(value, list):
                if value:  # If the list is not empty
                    self.key_value_pairs[key] = value[0]  # Take the first value
            else:
                self.key_value_pairs[key] = value
        
        # Convert price to float if it's a string
        if isinstance(current_price, str):
            try:
                # Remove currency symbols and convert to float
                import re
                price_match = re.search(r'(\d+[,.]\d+)', current_price)
                if price_match:
                    self.current_price = float(price_match.group(1).replace(',', '.'))
                else:
                    self.current_price = 0
            except:
                self.current_price = 0
        else:
            self.current_price = current_price
        
        # Same for basic_price
        if isinstance(basic_price, str):
            try:
                import re
                price_match = re.search(r'(\d+[,.]\d+)', basic_price)
                if price_match:
                    self.basic_price = float(price_match.group(1).replace(',', '.'))
                else:
                    self.basic_price = 0
            except:
                self.basic_price = 0
        else:
            self.basic_price = basic_price
        
        self.stock_status = stock_status

def get_self_link(page_dom):
    meta_tag = page_dom.find('link', rel='canonical')
    if meta_tag:
        return meta_tag['href']
    else:
        return ""

def extract_product_name(dom_tree):
    try:
        name_tag = dom_tree.find('h1', class_='product-detail-buy__name')
        if name_tag:
            return name_tag.get_text(strip=True)
        return ""
    except Exception as e:
        logging.error(f"Error extracting product name: {e}", exc_info=True)
        return ""

def extract_product_link(dom_tree):
    return get_self_link(dom_tree)

def extract_product_short_description(dom_tree):
    try:
        short_desc_tag = dom_tree.find('div', class_='product-detail-description-text')
        if short_desc_tag:
            first_p = short_desc_tag.find('p')
            if first_p:
                return " ".join(line.strip() for line in first_p.decode_contents().splitlines())
        return ""
    except Exception as e:
        logging.error(f"Error extracting product short description: {e}", exc_info=True)
        return ""

def extract_product_description(dom_tree):
    try:
        desc_tag = dom_tree.find('div', class_='product-detail-description-text')
        if desc_tag:
            return " ".join(line.strip() for line in desc_tag.decode_contents().splitlines())
        return ""
    except Exception as e:
        logging.error(f"Error extracting product description: {e}", exc_info=True)
        return ""

def extract_product_variants(dom_tree):
    try:
        variants = []

        # First, try to extract variants using the existing method
        variant_root_divs = dom_tree.find_all('div', {'data-testid': 'productVariant'})
        if variant_root_divs:
            for variant_root_div in variant_root_divs:
                key_value_pairs = {}
                for group in variant_root_div.find_all('div', class_='product-detail-buy__group'):
                    key = group.get_text(strip=True).strip(':')
                    values = []
                    for li in group.find_all('li', class_='tile-select__list-item'):
                        input_radio = li.find('input', class_='product-detail-configurator-option-input')
                        if input_radio and 'checked' in input_radio.attrs:
                            value = li.find('label')
                            if value:
                                values.append(value.get_text(strip=True))
                    if values:
                        key_value_pairs[key] = values
                current_price_tag = variant_root_div.find('div', class_='product-price__price')
                current_price = current_price_tag.get_text(strip=True) if current_price_tag else ""
                # basic_price = 0 for now, as mentioned
                basic_price = 0
                stock_status = ""
                for li in variant_root_div.find_all('li', class_='tile-select__list-item'):
                    input_radio = li.find('input', class_='product-detail-configurator-option-input')
                    if input_radio and 'checked' in input_radio.attrs:
                        stock_status_tag = li.find('label')
                        if stock_status_tag:
                            stock_status = stock_status_tag.get_text(strip=True)
                variants.append(Variant(key_value_pairs, current_price, basic_price, stock_status))
        else:
            # Alternative method for sites like contra.de
            # Find variant groups (like Farbe, Größe)
            variant_groups = {}
            price = 0
            stock_status = ""

            # Extract price
            price_tag = dom_tree.find('div', class_='product-detail-price')
            if price_tag:
                price_text = price_tag.get_text(strip=True)
                # Extract numeric value from price text (e.g., "35,90 €" -> 35.90)
                import re
                price_match = re.search(r'(\d+[,.]\d+)', price_text)
                if price_match:
                    price = float(price_match.group(1).replace(',', '.'))

            # Extract stock status
            stock_tag = dom_tree.find('div', class_='delivery-information')
            if stock_tag:
                stock_status = stock_tag.get_text(strip=True)

            # Find variant groups
            variant_elements = dom_tree.find_all('div', class_='product-detail-configurator-group')
            for element in variant_elements:
                # Extract group name (e.g., Farbe, Größe)
                group_name_tag = element.find('div', class_='product-detail-buy__group')
                if group_name_tag:
                    group_name = group_name_tag.get_text(strip=True).replace(':', '')
                    # Extract all possible values for this group
                    values = []
                    value_elements = element.find_all('li', class_=['tile-select__list-item', 'tile-select__list-item--is-text'])
                    for value_element in value_elements:
                        # Try different ways to extract the value
                        value_text = None
                        # Method 1: Look for label
                        label = value_element.find('label')
                        if label:
                            value_text = label.get_text(strip=True)
                        # Method 2: Look for span with class tile-select__preview--is-text
                        if not value_text:
                            span = value_element.find('span', class_='tile-select__preview--is-text')
                            if span:
                                value_text = span.get_text(strip=True)
                        if value_text:
                            values.append(value_text)
                    if values:
                        variant_groups[group_name] = values

            # Generate all combinations of variants
            if variant_groups:
                from itertools import product
                for combination in product(*variant_groups.values()):
                    key_value_pairs = {}
                    for i, key in enumerate(variant_groups.keys()):
                        key_value_pairs[key] = combination[i]
                    variants.append(Variant(key_value_pairs, price, price, stock_status))

        return variants
    except Exception as e:
        logging.error(f"Error extracting product variants: {e}", exc_info=True)
        return []

def extract_product_main_photo_link(dom_tree):
    try:
        gallery_div = dom_tree.find('div', class_='base-slider gallery-slider')
        if gallery_div:
            main_photo_tag = gallery_div.find('img')
            if main_photo_tag:
                return main_photo_tag['src']
        return ""
    except Exception as e:
        logging.error(f"Error extracting product main photo link: {e}", exc_info=True)
        return ""

def extract_product_photogallery_links(dom_tree):
    try:
        photogallery_links = set()
        gallery_div = dom_tree.find('div', class_='base-slider gallery-slider')
        if gallery_div:
            gallery_tags = gallery_div.find_all('img')[1:]
            for tag in gallery_tags:
                photogallery_links.add(tag['src'])
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
