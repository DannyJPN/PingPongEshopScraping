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
        self.key_value_pairs = key_value_pairs
        self.current_price = current_price
        self.basic_price = basic_price
        self.stock_status = stock_status

def get_self_link(page_dom):
    meta_tag = page_dom.find('meta', property='og:url')
    if meta_tag:
        return meta_tag['content']
    return ""


def extract_product_name(dom_tree):
    title_tag = dom_tree.select_one('h1.product_title')
    if title_tag:
        return title_tag.get_text(strip=True)
    return ""

def extract_product_short_description(dom_tree):
    try:
        short_desc_tag = dom_tree.find('div', class_='product-params-short')
        if short_desc_tag:
            return " ".join(line.strip() for line in short_desc_tag.decode_contents().splitlines())
    except Exception as e:
        logging.error(f"Error extracting product short description: {e}", exc_info=True)
    return ""
    
def extract_product_link(dom_tree):
    return get_self_link(dom_tree)
    
def extract_product_description(dom_tree):
    try:
        desc_tag = dom_tree.find('div', class_='product-detail-description')
        if desc_tag:
            return " ".join(line.strip() for line in desc_tag.decode_contents().splitlines())
    except Exception as e:
        logging.error(f"Error extracting product description: {e}", exc_info=True)
    return ""

def extract_product_variants(dom_tree):
    variants = []
    price=0
    availability = extract_availability_tag(dom_tree)
    variant_form = dom_tree.select_one('form.variations_form')
    if not variant_form:
        variants.append(Variant({}, price, price, availability))
        return variants
    selects = variant_form.select('table.variations select')
    keys = [select.get('name').replace('attribute_', '') for select in selects if select.get('name')]
    options_per_select = [[option.get('value') for option in select.find_all('option') if option.get('value')] for select in selects]
    from itertools import product
    for combination in product(*options_per_select):
        key_value = dict(zip(keys, combination))
        variants.append(Variant(key_value, price, price, availability))
    return variants

def extract_product_prices(dom_tree):
    price_tag = dom_tree.select_one('p.price span.woocommerce-Price-amount')
    if price_tag:
        text = price_tag.get_text()
        number = text.replace('€', '').replace(',', '.').strip()
        try:
            price = float(number)
            return price, price
        except ValueError:
            return 0, 0
    return 0, 0

def extract_availability_tag(dom_tree):
    stock_info = dom_tree.select_one('form.variations_form.cart p.stock')
    if stock_info:
        return stock_info.get_text(strip=True)
    return ""

def extract_product_main_photo_link(dom_tree):
    try:
        gallery_wrapper = dom_tree.find('div', class_='woocommerce-product-gallery__wrapper')
        if gallery_wrapper:
            first_image = gallery_wrapper.find('img')
            if first_image and first_image.get('src'):
                return first_image['src']
    except Exception as e:
        logging.error(f"Error extracting main photo link: {e}", exc_info=True)
    return ""

def extract_product_photogallery_links(dom_tree):
    photogallery_links = set()
    try:
        image_tags = dom_tree.select('div.woocommerce-product-gallery__wrapper img')
        for tag in image_tags:
            src = tag.get('src')
            if src:
                photogallery_links.add(src)
    except Exception as e:
        logging.error(f"Error extracting photogallery links: {e}", exc_info=True)
    return sorted(photogallery_links)

def extract_product(filepath):
    try:
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
        product.url = get_self_link(dom_tree)
        return product
    except Exception as e:
        logging.error(f"Error extracting product from {filepath}: {e}", exc_info=True)
        return None

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