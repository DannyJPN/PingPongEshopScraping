import os
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from spinwaylib.constants import MAIN_URL
from tqdm import tqdm

def extract_all_product_detail_links(category_pages_downloaded_paths):
    product_detail_links = set()
    with tqdm(total=len(category_pages_downloaded_paths), desc="Extracting product detail links") as pbar:
        for category_page_path in category_pages_downloaded_paths:
            product_detail_links.update(extract_product_detail_links(category_page_path))
            pbar.update(1)
    logging.debug(product_detail_links)
    return product_detail_links

def extract_product_detail_links(category_page_filepath):
    try:
        category_page_filepath = os.path.abspath(category_page_filepath)
        if not os.path.exists(category_page_filepath):
            logging.error(f"File does not exist: {category_page_filepath}")
            return set()
        with open(category_page_filepath, 'r', encoding='utf-8') as file:
            content = file.read()
        category_page_dom = BeautifulSoup(content, 'lxml')
        product_links = set()
        product_items = category_page_dom.select('div.wf-cell a.alignnone[href*="/produkt/"]')
        for link in product_items:
            href = link.get('href')
            if href:
                full_url = urljoin(MAIN_URL, href)
                product_links.add(full_url)
        return sorted(product_links)
    except Exception as e:
        logging.error(f"Error extracting product detail links: {e}", exc_info=True)
        return set()
