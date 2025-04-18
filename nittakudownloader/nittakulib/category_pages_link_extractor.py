from bs4 import BeautifulSoup
from urllib.parse import urljoin
from nittakulib.constants import MAIN_URL
from shared.html_loader import load_html_as_dom_tree
from tqdm import tqdm
import logging

def extract_category_pages_links(category_page_dom):
    soup = category_page_dom
    links = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'page=' in href:
            links.add(urljoin(MAIN_URL, href))
    return links

def extract_all_category_pages_links(category_firstpage_paths):
    category_page_links = set()
    with tqdm(total=len(category_firstpage_paths), desc="Extracting all category page links") as pbar:
        for firstpage_path in category_firstpage_paths:
            firstpage_dom = load_html_as_dom_tree(firstpage_path)
            category_page_links.update(extract_category_pages_links(firstpage_dom))
            pbar.update(1)
    logging.debug(category_page_links)
    return category_page_links











