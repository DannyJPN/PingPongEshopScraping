import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from nittakulib.constants import MAIN_URL
from tqdm import tqdm
from shared.html_loader import load_html_as_dom_tree
from nittakulib.product_attribute_extractor import get_self_link
import json

def extract_all_category_pages_links(category_firstpage_paths):
    category_page_links = set()
    with tqdm(total=len(category_firstpage_paths), desc="Extracting all category page links") as pbar:
        for firstpage_path in category_firstpage_paths:
            logging.debug(f"Extracting from {firstpage_path}")
            firstpage_dom = load_html_as_dom_tree(firstpage_path)
            if firstpage_dom:
                extracted_links = extract_category_pages_links(firstpage_dom)
                logging.debug(f"Extracted links from {firstpage_path}: {extracted_links}")
                category_page_links.update(extracted_links)
            else:
                logging.error(f"Failed to load DOM for {firstpage_path}")
            pbar.update(1)
    logging.debug(f"All extracted category page links: {category_page_links}")
    return category_page_links

def generate_page_urls(base_url, last_page_number):
    """
    Generates all page URLs from the first to the last page using the base URL and last page number.

    :param base_url: The base URL of the category pages.
    :param last_page_number: The last page number.
    :return: A set of URLs for all pages from the first to the last page.
    """
    page_urls = set()
    for page_number in range(1, last_page_number + 1):
        page_url = f"{base_url}?page={page_number}"
        page_urls.add(page_url)
    return page_urls

def extract_category_pages_links(category_page_dom):
    """
    Extracts all category page links from the category page HTML DOM.

    :param category_page_dom: BeautifulSoup object of the category page HTML.
    :return: A set of unique, sorted category page URLs.
    """
    try:
        # Extract the base URL from the self link
        logging.debug("Attempting to extract self link.")
        base_url = get_self_link(category_page_dom)
        logging.debug(f"Extracted base URL: {base_url}")
        if not base_url:
            logging.error("Failed to extract self link.")
            return set()

        # Extract the last page number
        logging.debug("Attempting to extract last page number.")
        last_page_number = extract_last_page_number(category_page_dom)
        logging.debug(f"Extracted last page number: {last_page_number}")

        # Generate all page URLs
        logging.debug(f"Generating page URLs from base URL: {base_url} to last page number: {last_page_number}.")
        page_urls = generate_page_urls(base_url, last_page_number)
        logging.debug(f"Generated page URLs: {page_urls}")

        # Ensure the URLs are unique and sorted
        unique_sorted_page_urls = sorted(page_urls)
        logging.debug(f"Unique sorted page URLs: {unique_sorted_page_urls}")
        return unique_sorted_page_urls

    except Exception as e:
        logging.error(f"Error extracting category page links: {e}", exc_info=True)
        return set()

def extract_last_page_number(category_page_dom):
    """
    Extracts the last page number from the category page HTML DOM.

    :param category_page_dom: BeautifulSoup object of the category page HTML.
    :return: The last page number as an integer.
    """
    try:
        pagination_next = category_page_dom.find('a', class_='pagination__next link')
        logging.debug(f"Pagination next element: {pagination_next}")
        if pagination_next and 'data-page' in pagination_next.attrs:
            last_page_number = int(pagination_next['data-page'])
            logging.debug(f"Last page number extracted: {last_page_number}")
            return last_page_number
        else:
            logging.debug("Pagination next link not found or missing 'data-page' attribute.")
            return 1  # Default to 1 if pagination element is not found
    except Exception as e:
        logging.error(f"Error extracting last page number: {e}", exc_info=True)
        return 1  # Default to 1 in case of error