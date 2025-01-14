# vsenastolnitenislib/product_attribute_extractor.py
import os
import logging
import re
import itertools
import ast
from bs4 import BeautifulSoup
from datetime import datetime
from shared.image_downloader import download_image
from shared.utils import sanitize_filename
from shared.html_loader import load_html_as_dom_tree
from tqdm import tqdm
from vsenastolnitenislib.constants import MAIN_URL

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
        self.url = ""

class Variant:
    def __init__(self, key_value_pairs, current_price, basic_price, stock_status):
        self.key_value_pairs = key_value_pairs
        self.current_price = current_price
        self.basic_price = basic_price
        self.stock_status = stock_status

def get_self_link(page_dom):
    try:
        base_element = page_dom.find('base')
        if base_element and base_element.has_attr('href'):
            base_url = base_element['href']
        else:
            base_url = MAIN_URL
        logging.debug(f"Extracted base URL: {base_url}")
        return base_url
    except Exception as e:
        logging.error(f"Error extracting self link: {e}", exc_info=True)
        return MAIN_URL

def extract_product_name(dom_tree):
    try:
        h1_tag = dom_tree.find('h1', class_='pp-dash')
        if h1_tag:
            product_name = ''.join(h1_tag.stripped_strings)
            product_name = re.sub('<[^<]+?>', '', product_name)  # Remove any HTML tags
            return product_name.strip()
        return ""
    except Exception as e:
        logging.error(f"Error extracting product name: {e}", exc_info=True)
        return ""

def extract_product_short_description(dom_tree):
    try:
        span_tag = dom_tree.find('span', class_='sdesc')
        if span_tag:
            return " ".join(line.strip() for line in span_tag.decode_contents().splitlines())
        return ""
    except Exception as e:
        logging.error(f"Error extracting product short description: {e}", exc_info=True)
        return ""

def extract_product_description(dom_tree):
    try:
        div_tag = dom_tree.find('div', id='collapseOne', class_='collapse show')
        if div_tag:
            return " ".join(line.strip() for line in div_tag.decode_contents().splitlines())
        return ""
    except Exception as e:
        logging.error(f"Error extracting product description: {e}", exc_info=True)
        return ""

def extract_product_js_variants(dom_tree):
    try:
        script_tag = dom_tree.find('script', text=re.compile('var product_variants ='))
        if script_tag:
            script_content = script_tag.string
            json_text = re.search(r'var product_variants = (\[.*?\]);', script_content, re.DOTALL).group(1)
            # Convert JavaScript array to JSON-compatible format
            json_text = json_text.replace("'", '"')  # Replace single quotes with double quotes
            json_text = re.sub(r'(\w+):', r'"\1":', json_text)  # Ensure property names are quoted
            # Use ast.literal_eval to safely evaluate the JSON-like structure
            js_variants = ast.literal_eval(json_text)
            logging.debug(f"Extracted JS variants: {js_variants}")
            return js_variants
        else:
            logging.debug("No JS variants found")
            return []
    except Exception as e:
        logging.error(f"Error extracting JS variants: {e}", exc_info=True)
        return []

def extract_product_variants(dom_tree):
    try:
        variants = []
        key_value_pairs = []
        div_tags = dom_tree.find_all('div', class_='mb-2 pp-detail-options')
        logging.debug(f"Found {len(div_tags)} div tags with class 'mb-2 pp-detail-options'")
        variant_values = {}
        all_input_tags = []
        for div_tag in div_tags:
            input_tags = div_tag.find_all('input', type='radio')
            all_input_tags.extend(input_tags)
            variant_single_vals = []
            for input_tag in input_tags:
                parent = input_tag.find_parent()
                if parent:
                    variant_single_vals.append({"name": input_tag['name'], "value_id": input_tag['value'], "value": parent.text.strip()})
            for single_val in variant_single_vals:
                if single_val['name'] not in variant_values:
                    variant_values[single_val['name']] = []
                variant_values[single_val['name']].append(single_val['value'])
        keys = variant_values.keys()
        values = variant_values.values()
        combinations = itertools.product(*values)
        for combo in combinations:
            result_dict = dict(zip(keys, combo))
            key_value_pairs.append(result_dict)
            logging.debug(f"Extracted key-value pair: {result_dict}")

        # Extract JS variants data
        js_variants = extract_product_js_variants(dom_tree)
        logging.debug(f"Extracted {len(js_variants)} JS variants")

        for key_value_pair in key_value_pairs:
            keylist = list(key_value_pair.keys())
            search_vals = []
            for i in range(len(keylist)):
                matches = []
                for input in all_input_tags:
                    if input['name'] == keylist[i]:
                        parent = input.find_parent()
                        if parent and parent.text.strip() == key_value_pair[keylist[i]]:
                            matches.append({input['name']: input['value']})
                search_vals.append(matches)
            search_terms = list(itertools.chain.from_iterable(search_vals))
            search_list = {}
            for d in search_terms:
                search_list.update(d)

            logging.debug(f"Processing combination: {key_value_pair}")
            pairkeys = search_list.keys()
            # Find matching JS variant
            matching_js_variant = next((js_variant for js_variant in js_variants if all(search_list[key] == js_variant.get(key.lower(), "") for key in pairkeys)), {})
            logging.debug(f"Matching JS variant: {matching_js_variant}")
            current_price = matching_js_variant.get('price_raw', 0)
            basic_price = matching_js_variant.get('priceold_raw', current_price)
            stock_status = matching_js_variant.get('availability_txt', '')
            variant = Variant(key_value_pair, current_price, basic_price, stock_status)
            variants.append(variant)

        logging.debug(f"Extracted HTML variants: {variants}")
        return variants
    except Exception as e:
        logging.error(f"Error extracting product HTML variants: {e}", exc_info=True)
        return []

def extract_product_main_photo_link(dom_tree):
    try:
        img_tag = dom_tree.find('img', class_='myzoom img-fluid m-auto')
        if img_tag and img_tag.has_attr('src'):
            return MAIN_URL + img_tag['src']
        return ""
    except Exception as e:
        logging.error(f"Error extracting product main photo link: {e}", exc_info=True)
        return ""

def extract_product_photogallery_links(dom_tree):
    try:
        photo_links = set()
        picture_tags = dom_tree.find_all('picture')
        for picture in picture_tags:
            source_tag = picture.find('source')
            if source_tag and source_tag.has_attr('srcset'):
                photo_links.add(MAIN_URL + source_tag['srcset'])
        return photo_links
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
        product.variants = extract_product_variants(dom_tree)  # Extract HTML variants and JS data
        product.main_photo_link = extract_product_main_photo_link(dom_tree)
        product.photogallery_links = extract_product_photogallery_links(dom_tree)
        product.url = get_self_link(dom_tree)

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