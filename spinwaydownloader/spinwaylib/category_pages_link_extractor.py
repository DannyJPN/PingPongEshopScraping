import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from spinwaylib.constants import MAIN_URL
from tqdm import tqdm
from shared.html_loader import load_html_as_dom_tree
from spinwaylib.product_attribute_extractor import get_self_link


def extract_all_category_pages_links(category_firstpage_paths):
    category_page_links = set()
    with tqdm(total=len(category_firstpage_paths), desc="Extracting all category page links") as pbar:
        for firstpage_path in category_firstpage_paths:
            firstpage_dom = load_html_as_dom_tree(firstpage_path)
            category_page_links.update(extract_category_pages_links(firstpage_dom))
            pbar.update(1)
    logging.debug(category_page_links)
    return category_page_links

def extract_category_pages_links(category_page_dom):
    try:
        page_links = set()
        pagination_links = category_page_dom.select('a.page-numbers[href*="/page/"]')
        for link in pagination_links:
            href = link.get('href')
            if href and "/page/" in href:
                page_links.add(href)
        return sorted(page_links)
    except Exception as e:
        logging.error(f"Error extracting category page links: {e}", exc_info=True)
        return []