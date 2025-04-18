import os
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from vsenastolnitenislib.constants import MAIN_URL
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
    try:
        # Load the HTML content of the category page
        category_page_dom = load_html_as_dom_tree(category_page_filepath)
        if category_page_dom is None:
            return set()

        # Initialize a set to store the unique product detail links
        product_links = set()

        # Find all product detail link elements by class name
        product_link_elements = category_page_dom.find_all('a', class_='pp-prod-card')

        # Extract and construct absolute URLs
        for element in product_link_elements:
            relative_url = element.get('href')
            absolute_url = urljoin(MAIN_URL, relative_url)
            product_links.add(absolute_url)
            logging.debug(f"Extracted product detail URL: {absolute_url}")

        # Return the sorted set of unique URLs
        sorted_product_links = sorted(product_links)
        logging.debug(f"Sorted unique product detail links: {sorted_product_links}")
        return sorted_product_links

    except Exception as e:
        logging.error(f"Error extracting product detail links from {category_page_filepath}: {e}", exc_info=True)
        return set()










