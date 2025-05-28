from bs4 import BeautifulSoup
from nittakulib.constants import MAIN_URL
from shared.html_loader import load_html_as_dom_tree
from tqdm import tqdm
import logging
from urllib.parse import urljoin

def extract_product_detail_links(page_dom):
    """
    Extract product detail links from a category page DOM.

    :param page_dom: BeautifulSoup object containing the parsed HTML of a category page
    :return: Set of links to product detail pages
    """
    links = set()
    if page_dom is None:
        logging.error("Failed to parse HTML from category page - page_dom is None")
        return links

    try:
        # Find all links in the page
        for a in page_dom.find_all('a', href=True):
            href = a['href']
            # Check if the link is a product link
            if '/products/' in href:
                # Normalize the URL
                full_url = urljoin(MAIN_URL, href)
                links.add(full_url)
    except Exception as e:
        logging.error(f"Error extracting product detail links: {e}")

    return links

def extract_all_product_detail_links(category_pages_downloaded_paths):
    product_detail_links = set()
    with tqdm(total=len(category_pages_downloaded_paths), desc="Extracting product detail links") as pbar:
        for category_page_path in category_pages_downloaded_paths:
            product_detail_links.update(extract_product_detail_links(load_html_as_dom_tree(category_page_path)))
            pbar.update(1)
    logging.debug(product_detail_links)
    return sorted(product_detail_links)
