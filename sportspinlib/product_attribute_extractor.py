# product_attribute_extractor.py
import os
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from shared.image_downloader import download_image
from shared.utils import sanitize_filename  
from shared.html_loader import load_html_as_dom_tree, get_self_link
from tqdm import tqdm

class Product:
    def __init__(self):
        self.name = ""
        self.short_description = ""
        self.description = ""
        self.variants = []
        self.price = 0
        self.discount = 0
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

def extract_product_name(dom_tree):
    try:
        name_tag = dom_tree.find('div', class_='p-detail-inner-header').find('h1')
        if name_tag:
            return name_tag.text.strip()
    except Exception as e:
        logging.error(f"Error extracting product name: {e}", exc_info=True)
    return ""
def extract_product_link(dom_tree):
    return get_self_link(dom_tree)

def extract_product_short_description(dom_tree):
    try:
        short_desc_tag = dom_tree.find('div', {'class': 'p-short-description', 'data-testid': 'productCardShortDescr'})
        if short_desc_tag:
            return " ".join(line.strip() for line in short_desc_tag.decode_contents().splitlines())
    except Exception as e:
        logging.error(f"Error extracting product short description: {e}", exc_info=True)
    return ""

def extract_product_description(dom_tree):
    try:
        desc_tag = dom_tree.find('div', class_='basic-description')
        if desc_tag:
            return " ".join(line.strip() for line in desc_tag.decode_contents().splitlines())
    except Exception as e:
        logging.error(f"Error extracting product description: {e}", exc_info=True)
    return ""

def extract_product_variants(dom_tree):
    variants = []
    try:
        variant_tags = dom_tree.find_all('div', {'class':'table-row', 'data-testid': 'productVariant'})
        for variant_tag in variant_tags:
            key_value_pairs = {}
            name_tag = variant_tag.find('div', {'class':'variant-name', 'data-testid': 'productVariantName'})
            if name_tag:
                pairs = name_tag.text.split(',')
                for pair in pairs:
                    if ':' in pair:
                        key, value = pair.split(':', 1)
                        key_value_pairs[key.strip()] = value.strip()

            current_price = 0
            current_price_tag = variant_tag.find('div', {'class':'price-final', 'data-testid': 'productVariantPrice'})
            if current_price_tag:
                current_price = int(current_price_tag.text.replace(' ', '').replace('Kč', ''))

            basic_price = current_price
            basic_price_tag = variant_tag.find('span', class_='price-standard')
            if basic_price_tag:
                basic_price = int(basic_price_tag.find('span').text.replace(' ', '').replace('Kč', ''))

            stock_status = ""
            stock_status_tag = name_tag.find_next_sibling('span')
            if stock_status_tag:
                stock_status = stock_status_tag.text.strip()

            variant = Variant(key_value_pairs, current_price, basic_price, stock_status)
            variants.append(variant)
    except Exception as e:
        logging.error(f"Error extracting product variants: {e}", exc_info=True)
    return variants

def extract_product_price(variants):
    try:
        if variants:
            return max(variant.current_price for variant in variants)
        return 0
    except Exception as e:
        logging.error(f"Error extracting product price: {e}", exc_info=True)
    return 0

def extract_product_discount(dom_tree, variants):
    try:
        if variants:
            if all(variant.current_price == variants[0].current_price for variant in variants):
                return variants[0].basic_price - variants[0].current_price
            return 0
        discount_tag = dom_tree.find('span', class_='price-save')
        if discount_tag:
            return int(discount_tag.text.strip().replace(' ', '').replace('–', '').replace('%', ''))
    except Exception as e:
        logging.error(f"Error extracting product discount: {e}", exc_info=True)
    return 0

def extract_product_main_photo_link(dom_tree):
    try:
        main_photo_tag = dom_tree.find('a', class_='p-main-image cloud-zoom')
        if main_photo_tag:
            logging.debug(f"MainPhotoLink {main_photo_tag.get('data-href')}")
            return main_photo_tag.get('data-href')
    except Exception as e:
        logging.error(f"Error extracting product main photo link: {e}", exc_info=True)
    return ""

def extract_product_photogallery_links(dom_tree):
    photogallery_links = set()
    try:
        gallery_tags = dom_tree.find_all('a', class_='p-thumbnail')
        for tag in gallery_tags:
            href = tag.get('href')
            if href:
                photogallery_links.add(href)
    except Exception as e:
        logging.error(f"Error extracting product photogallery links: {e}", exc_info=True)
    return sorted(photogallery_links)

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
        product.price = extract_product_price(product.variants)
        product.discount = extract_product_discount(dom_tree, product.variants)
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