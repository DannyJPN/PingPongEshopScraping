from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging

from shared.html_loader import load_html_as_dom_tree
from nittakulib.constants import MAIN_URL

def extract_category_links(html_dom):
    """
    Extract category links from the main page soup object.

    :param html_dom: BeautifulSoup object containing the parsed HTML
    :return: Set of category links
    """
    links = set()

    if html_dom is None:
        logging.error("Failed to parse HTML from main page - soup is None")
        return links

    try:
        # Find all links on the page
        for a in html_dom.find_all('a', href=True):
            href = a['href']
            # Check if the link is a category link (contains /collections/ or is a product in a collection)
            if '/collections/' in href and '/products/' not in href:
                full_url = urljoin(MAIN_URL, href)
                links.add(full_url)
    except Exception as e:
        logging.error(f"Error extracting category links: {e}", exc_info=True)

    logging.debug(f"Extracted {len(links)} category links: {links}")
    return links
