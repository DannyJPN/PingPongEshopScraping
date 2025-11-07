"""
Extracts category links from Dawei main page.

Dawei.tt uses Shopify platform with standard collection structure.
"""
import logging
from urllib.parse import urljoin
from tqdm import tqdm
from daweilib.constants import MAIN_URL


def extract_category_links(main_page_soup):
    """
    Extract all category links from the main page DOM.

    Dawei uses Shopify - looks for /collections/ URLs in navigation.

    :param main_page_soup: BeautifulSoup object of the main page
    :return: Sorted list of unique absolute category URLs
    """
    try:
        category_links = set()

        # Pattern 1: Shopify navigation - header menu
        # Look for header navigation links
        header_nav = main_page_soup.find('nav', class_=lambda x: x and ('site-nav' in x.lower() or 'main-nav' in x.lower() or 'header' in x.lower()))
        if header_nav:
            nav_links = header_nav.find_all('a')
            logging.debug(f"Found {len(nav_links)} links in header navigation")

            for link in nav_links:
                href = link.get('href')
                if href and ('/collections/' in href or '/category/' in href):
                    absolute_url = urljoin(MAIN_URL, href)
                    category_links.add(absolute_url)

        # Pattern 2: Shopify standard collection links
        collection_links = main_page_soup.find_all('a', href=lambda x: x and '/collections/' in x)
        logging.debug(f"Found {len(collection_links)} collection links")

        for link in tqdm(collection_links, desc="Extracting collection links"):
            href = link.get('href')
            if href:
                absolute_url = urljoin(MAIN_URL, href)
                # Exclude "all" collection and pagination
                if '/collections/all' not in absolute_url and '?page=' not in absolute_url:
                    category_links.add(absolute_url)

        # Pattern 3: Menu/dropdown categories
        menu_items = main_page_soup.find_all(['li', 'div'], class_=lambda x: x and ('menu-item' in x.lower() or 'nav-item' in x.lower()))
        for item in menu_items:
            link = item.find('a')
            if link:
                href = link.get('href')
                if href and ('/collections/' in href or '/category/' in href):
                    absolute_url = urljoin(MAIN_URL, href)
                    category_links.add(absolute_url)

        # Pattern 4: Category grid on homepage
        category_grid = main_page_soup.find_all('a', class_=lambda x: x and ('category' in x.lower() or 'collection' in x.lower()))
        for link in category_grid:
            href = link.get('href')
            if href and ('/collections/' in href or '/category/' in href):
                absolute_url = urljoin(MAIN_URL, href)
                category_links.add(absolute_url)

        # Filter out unwanted URLs
        filtered_links = set()
        for url in category_links:
            # Skip: blog, pages, cart, account, search
            if not any(x in url.lower() for x in ['/blogs/', '/pages/', '/cart', '/account', '/search', '/contact']):
                filtered_links.add(url)

        sorted_links = sorted(filtered_links)
        logging.info(f"Found {len(sorted_links)} unique category links")
        return sorted_links

    except Exception as e:
        logging.error(f"Error extracting category links: {e}", exc_info=True)
        return []
