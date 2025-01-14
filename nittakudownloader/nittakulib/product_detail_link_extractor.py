import os
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from nittakulib.constants import MAIN_URL
from tqdm import tqdm
from shared.html_loader import load_html_as_dom_tree

def extract_all_product_detail_links(category_pages_downloaded_paths):
    product_detail_links = set()
    with tqdm(total=len(category_pages_downloaded_paths), desc="Extracting product detail links") as pbar:
        for category_page_path in category_pages_downloaded_paths:
            product_detail_links.update(extract_product_detail_links(category_page_path))
            pbar.update(1)
    logging.debug(product_detail_links)
    return product_detail_links

def extract_product_detail_links(category_page_filepath):
    """
    Extracts product detail links from the category page HTML file.

    :param category_page_filepath: The file path to the category page HTML.
    :return: A set of unique, sorted product detail URLs.
    """
    try:
        # Load the HTML content
        category_page_dom = load_html_as_dom_tree(category_page_filepath)
        if not category_page_dom:
            logging.error(f"Failed to load HTML content from {category_page_filepath}")
            return set()

        # Find all product detail links
        product_links = category_page_dom.find_all('a', class_='product-item__title text--strong link')
        product_urls = set()

        for link in product_links:
            relative_url = link.get('href')
            if relative_url:
                absolute_url = urljoin(MAIN_URL, relative_url)
                product_urls.add(absolute_url)

        # Ensure the URLs are unique and sorted
        unique_sorted_product_urls = sorted(product_urls)
        logging.debug(f"Extracted product detail URLs: {unique_sorted_product_urls}")
        return unique_sorted_product_urls

    except Exception as e:
        logging.error(f"Error extracting product detail links: {e}", exc_info=True)
        return set()