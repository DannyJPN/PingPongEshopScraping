import os
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from gewolib.constants import MAIN_URL
from tqdm import tqdm
from shared.html_loader import load_html_as_dom_tree

def extract_all_product_detail_links(category_pages_downloaded_paths):
    product_detail_links = set()
    with tqdm(total=len(category_pages_downloaded_paths), desc="Extracting product detail links") as pbar:
        for category_page_path in category_pages_downloaded_paths:
            product_detail_links.update(extract_product_detail_links(category_page_path))
            pbar.update(1)
    logging.debug(product_detail_links)
    return sorted(product_detail_links)

def extract_product_detail_links(category_page_filepath):
    # Load the HTML content of the category page
    dom_tree = load_html_as_dom_tree(category_page_filepath)
    if dom_tree is None:
        logging.error(f"Failed to load HTML content from {category_page_filepath}")
        return set()

    # Find all product detail links
    product_links = set()
    for link in dom_tree.find_all('a', class_='product-box__link'):
        href = link.get('href')
        if href:
            absolute_url = urljoin(MAIN_URL, href)
            product_links.add(absolute_url)

    return sorted(product_links)










