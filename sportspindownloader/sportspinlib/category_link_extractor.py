﻿import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from tqdm import tqdm
from sportspinlib.constants import MAIN_URL

from shared.html_loader import load_html_as_dom_tree
def extract_category_links(main_page_html):
    """
    Extracts category links from the main page HTML.

    :param main_page_html: BeautifulSoup object containing the HTML DOM of the main page.
    :return: Set of absolute URLs for the category links.
    """
    try:
        # Find all category links
        category_links = set()
        category_link_elements = main_page_html.find_all('a', {'data-testid': 'headerMenuItem'})
        if not category_link_elements:
            logging.warning("No category links found.")
            return set()

        with tqdm(total=len(category_link_elements), desc="Extracting category links") as pbar:
            for link in category_link_elements:
                href = link.get('href')
                if href:
                    # Convert to absolute URL
                    absolute_url = urljoin(MAIN_URL, href)
                    category_links.add(absolute_url)
                pbar.update(1)

        # Return sorted set of unique URLs
        unique_sorted_links = sorted(category_links)
        logging.debug(f"Unique sorted links: {len(unique_sorted_links)}")
        return unique_sorted_links

    except Exception as e:
        logging.error(f"Error extracting category links: {e}", exc_info=True)
        return set()










