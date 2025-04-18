from bs4 import BeautifulSoup
from nittakulib.constants import MAIN_URL
from shared.html_loader import load_html_as_dom_tree
from tqdm import tqdm
import logging
from urllib.parse import urljoin

def extract_product_detail_links(category_page_filepath):
    soup = load_html_as_dom_tree(category_page_filepath)
    links = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/product/' in href or 'product_id=' in href:
            links.add(urljoin(MAIN_URL, href))
    return links

def extract_all_product_detail_links(category_pages_downloaded_paths):
    product_detail_links = set()
    with tqdm(total=len(category_pages_downloaded_paths), desc="Extracting product detail links") as pbar:
        for category_page_path in category_pages_downloaded_paths:
            product_detail_links.update(extract_product_detail_links(category_page_path))
            pbar.update(1)
    logging.debug(product_detail_links)
    return product_detail_links











