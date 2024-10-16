# product_attribute_extractor.py
import os
import logging
from bs4 import BeautifulSoup
from shared.image_downloader import download_image
from shared.utils import sanitize_filename
from shared.html_loader import load_html_as_dom_tree
from tqdm import tqdm
import csv
import json

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
    else:
        return ""

def extract_product_name(dom_tree):
    try:
        name_tag = dom_tree.find('h1', itemprop='name', attrs={'data-testid': 'textProductName'})
        if name_tag:
            return name_tag.text.strip()
        return ""
    except Exception as e:
        logging.error(f"Error extracting product name: {e}", exc_info=True)
        return ""

def extract_product_link(dom_tree):
    return get_self_link(dom_tree)

def extract_product_short_description(dom_tree):
    try:
        short_description_tag = dom_tree.find('div', class_='description-inner', attrs={'data-testid': 'productCardDescr'})
        if short_description_tag and short_description_tag.p:
            return str(short_description_tag.p)
        return ""
    except Exception as e:
        logging.error(f"Error extracting product short description: {e}", exc_info=True)
        return ""

def extract_product_description(dom_tree):
    try:
        description_tag = dom_tree.find('div', class_='description-inner', attrs={'data-testid': 'productCardDescr'})
        if description_tag:
            return str(description_tag)
        return ""
    except Exception as e:
        logging.error(f"Error extracting product description: {e}", exc_info=True)
        return ""

def extract_product_variants(dom_tree):
    variants = []
    try:
        variant_tags = dom_tree.find_all('tr', {'data-testid': 'productVariant'})
        current_prices = []

        if variant_tags:
            for variant_tag in variant_tags:
                key_value_pairs = {}
                name_tag = variant_tag.find('td', {'class': 'variant', 'data-testid': 'productVariantName'})
                if name_tag:
                    # Replace both <br /> and <br/> with a newline character
                    raw_content = name_tag.decode_contents().replace('<br />', '\n').replace('<br/>', '\n')
                    raw_pairs = raw_content.split('\n')
                    for pair in raw_pairs:
                        if ':' in pair:
                            key, value = pair.split(':', 1)
                            key_value_pairs[key.strip()] = value.strip()

                current_price = 0
                current_price_tag = variant_tag.find('td', {'class': 'tari variant-price', 'data-testid': 'productVariantPrice'})
                if current_price_tag:
                    strong_tag = current_price_tag.find('strong')
                    if strong_tag:
                        current_price = float(strong_tag.text.replace(' ', '').replace('Kč', '').replace(',', '.'))
                        current_prices.append(current_price)
                        logging.debug(f"Found current price for variant: {current_price}")

                basic_price = current_price

                stock_status = ""
                stock_status_tag = variant_tag.find('td', {'class': 'variant-availability'}).find('span', {'class': 'show-tooltip acronym'})
                if stock_status_tag:
                    # Correctly handle nested elements
                    stock_status = stock_status_tag.text.strip()

                variant = Variant(key_value_pairs, current_price, basic_price, stock_status)
                variants.append(variant)
        else:
            basic_price, current_price = extract_product_prices(dom_tree)
            stock_status = ""
            key_value_pairs = {}
            variant = Variant(key_value_pairs, current_price, basic_price, stock_status)
            variants.append(variant)

        if current_prices:
            highest_price = max(current_prices)
            for variant in variants:
                variant.basic_price = highest_price
                logging.debug(f"Set basic price for variant: {highest_price}")

    except Exception as e:
        logging.error(f"Error extracting product variants: {e}", exc_info=True)
    return variants

def extract_product_prices(dom_tree):
    try:
        # Extract current price
        current_price_tag = dom_tree.find('strong', class_='price sub-left-position', attrs={'data-testid': 'productCardPrice'})
        if current_price_tag:
            current_price = float(current_price_tag.text.replace(' ', '').replace('Kč', '').replace(',', '.'))
            logging.debug(f"Found current price: {current_price}")
        else:
            logging.warning("No current price found.")
            return 0.0, 0.0

        # Extract basic price
        basic_price_tag = dom_tree.find('td', class_='td-normal-price')
        if basic_price_tag and basic_price_tag.find('span', class_='line'):
            basic_price = float(basic_price_tag.find('span', class_='line').text.replace(' ', '').replace('Kč', '').replace(',', '.'))
            logging.debug(f"Found basic price: {basic_price}")
        else:
            basic_price = current_price
            logging.debug(f"No basic price found, setting basic price to current price: {basic_price}")

        return basic_price, current_price
    except Exception as e:
        logging.error(f"Error extracting product prices: {e}", exc_info=True)
        return 0.0, 0.0

def extract_product_main_photo_link(dom_tree):
    try:
        main_photo_link_tag = dom_tree.find('a', id='gallery-image')
        logging.debug(f"Found mainphotolink {main_photo_link_tag}")
        if main_photo_link_tag:
            return main_photo_link_tag['href']
        return ""
    except Exception as e:
        logging.error(f"Error extracting product main photo link: {e}", exc_info=True)
        return ""

def extract_product_photogallery_links(dom_tree):
    try:
        photogallery_link_tags = dom_tree.find_all('a', attrs={'data-gallery': 'lightbox[gallery]'})
        photogallery_links = {tag['href'] for tag in photogallery_link_tags}
        return photogallery_links
    except Exception as e:
        logging.error(f"Error extracting product photogallery links: {e}", exc_info=True)
        return set()

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

def export_to_csv(csv_output_path, products):
    try:
        with open(csv_output_path, 'w', newline='', encoding='utf-8') as csvfile:
            csvwriter = csv.writer(csvfile)
            # Write the header
            csvwriter.writerow(['Name', 'Short Description', 'Description',  'Main Photo Filepath', 'Gallery Filepaths', 'Variants','URL'])
            # Write product data
            with tqdm(total=len(products), desc="Exporting to csv") as pbar:
                for product in products:
                    csvwriter.writerow([
                        product.name,
                        product.short_description,
                        product.description,
                        product.main_photo_filepath,
                        '|'.join(product.photogallery_filepaths),
                        '|'.join([json.dumps({"key_value_pairs": variant.key_value_pairs,"current_price": variant.current_price,"basic_price": variant.basic_price,"stock_status": variant.stock_status}, ensure_ascii=False) for variant in product.variants]),
                        product.url
                    ])
                    pbar.update(1)

        logging.info(f"CSV output generated at: {csv_output_path}")
    except Exception as e:
        logging.error(f"Error exporting to CSV: {e}", exc_info=True)