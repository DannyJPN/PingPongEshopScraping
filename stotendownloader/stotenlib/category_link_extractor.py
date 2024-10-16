import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from stotenlib.constants import MAIN_URL
from tqdm import tqdm

def extract_category_links(main_page_html):
    """
    Extracts category links from the main page HTML.

    :param main_page_html: BeautifulSoup object of the main page HTML.
    :return: Set of unique and sorted absolute URLs of the category pages.
    """
    try:
        category_links = set()
        categories_div = main_page_html.find('div', id='categories')
        if not categories_div:
            logging.error("No 'categories' div found in the main page HTML.")
            return set()
        a_tags=categories_div.find_all('a', href=True)
        with tqdm(total=len(a_tags), desc="Extracting category links") as pbar:
            for a_tag in a_tags:
                href = a_tag['href']
                absolute_url = urljoin(MAIN_URL, href)
                category_links.add(absolute_url)
                pbar.update(1)

        
        logging.debug(f"Extracted category links: {sorted(category_links)}")
        return category_links

    except Exception as e:
        logging.error(f"Error extracting category links: {e}", exc_info=True)
        return set()