"""
Extracts category links from Asics main page.
"""
import logging
from urllib.parse import urljoin
from tqdm import tqdm
from asicslib.constants import MAIN_URL


def extract_category_links(main_page_soup):
    """
    Extract all category links from the main page DOM.

    :param main_page_soup: BeautifulSoup object of the main page
    :return: Sorted list of unique absolute category URLs
    """
    category_links = set()

    # Try multiple patterns for Asics categories
    # Pattern 1: Navigation menu items
    menu_links = main_page_soup.find_all('a', href=True)

    for link in tqdm(menu_links, desc="Extracting category links"):
        href = link.get('href')
        if href:
            # Filter for category-like URLs
            # Common patterns: /table-tennis, /tt/, /sport/table-tennis, /en/table-tennis
            href_lower = href.lower()
            if any(pattern in href_lower for pattern in [
                'table-tennis', 'table_tennis', 'tabletennis',
                '/tt/', '/sport/', '/category/', '/collection/',
                '/products/', '/shop/'
            ]):
                # Skip cart, account, and other non-category pages
                if not any(skip in href_lower for skip in [
                    'cart', 'checkout', 'account', 'login', 'register',
                    'wishlist', 'compare', 'search', 'contact'
                ]):
                    absolute_url = urljoin(MAIN_URL, href)
                    category_links.add(absolute_url)

    # If no categories found, try to extract all navigation links
    if not category_links:
        logging.warning("No category-specific links found, extracting all navigation links")
        nav_elements = main_page_soup.find_all(['nav', 'div'], class_=lambda x: x and ('nav' in x.lower() or 'menu' in x.lower()))
        for nav in nav_elements:
            links = nav.find_all('a', href=True)
            for link in links:
                href = link.get('href')
                if href:
                    href_lower = href.lower()
                    if not any(skip in href_lower for skip in [
                        'cart', 'checkout', 'account', 'login', 'register',
                        'wishlist', 'compare', 'search', 'contact', 'about',
                        'faq', 'help', 'privacy', 'terms', 'shipping'
                    ]):
                        absolute_url = urljoin(MAIN_URL, href)
                        category_links.add(absolute_url)

    logging.info(f"Found {len(category_links)} unique category links")
    return sorted(category_links)
