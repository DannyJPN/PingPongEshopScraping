"""
Extracts category links from Avalox main page.
"""
import logging
from urllib.parse import urljoin
from tqdm import tqdm
from avaloxlib.constants import MAIN_URL


def extract_category_links(main_page_soup):
    """
    Extract all category links from the main page DOM.

    :param main_page_soup: BeautifulSoup object of the main page
    :return: Sorted list of unique absolute category URLs
    """
    try:
        category_links = set()

        # Pattern 1: Navigation menu links
        nav_links = main_page_soup.find_all('a', class_=lambda x: x and ('nav' in x.lower() or 'menu' in x.lower() or 'category' in x.lower()))
        logging.debug(f"Found {len(nav_links)} navigation/menu links")

        for link in tqdm(nav_links, desc="Extracting navigation links"):
            href = link.get('href')
            if href:
                absolute_url = urljoin(MAIN_URL, href)
                # Filter for category-like URLs
                if '/products/' in absolute_url or '/collections/' in absolute_url or '/category/' in absolute_url:
                    category_links.add(absolute_url)

        # Pattern 2: Direct category links
        category_elements = main_page_soup.select('a[href*="category"], a[href*="collection"], a[href*="products"]')
        logging.debug(f"Found {len(category_elements)} category-like links")

        for link in tqdm(category_elements, desc="Extracting category links"):
            href = link.get('href')
            if href:
                absolute_url = urljoin(MAIN_URL, href)
                category_links.add(absolute_url)

        sorted_links = sorted(category_links)
        logging.info(f"Found {len(sorted_links)} unique category links")
        return sorted_links

    except Exception as e:
        logging.error(f"Error extracting category links: {e}", exc_info=True)
        return []
