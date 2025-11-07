"""
Extracts category links from Hanno main page.

Hanno uses German e-commerce platform (Shopware/WooCommerce):
- German/English category patterns
- Navigation structure extraction
- URL pattern matching for categories
"""
import logging
from urllib.parse import urljoin
from tqdm import tqdm
from hannolib.constants import MAIN_URL


def extract_category_links(main_page_soup):
    """
    Extract all category links from the main page DOM.

    :param main_page_soup: BeautifulSoup object of the main page
    :return: Sorted list of unique absolute category URLs
    """
    try:
        category_links = set()

        # Pattern 1: Navigation menu extraction
        nav_elements = (
            main_page_soup.select('nav a') +
            main_page_soup.select('.navigation a') +
            main_page_soup.select('.nav a') +
            main_page_soup.select('.menu a') +
            main_page_soup.select('.main-menu a') +
            main_page_soup.select('header nav a')
        )

        logging.debug(f"Found {len(nav_elements)} navigation links")

        for link in tqdm(nav_elements, desc="Extracting navigation links"):
            href = link.get('href')
            if href:
                absolute_url = urljoin(MAIN_URL, href)

                # German/English category patterns
                if any(pattern in absolute_url for pattern in [
                    '/kategorie/', '/category/', '/product-category/',
                    '/produktkategorie/', '/produkte/', '/products/',
                    '/sortiment/', '/shop/', '/collections/'
                ]):
                    # Exclude non-category pages
                    if not any(x in absolute_url.lower() for x in [
                        '/cart', '/warenkorb', '/checkout', '/kasse',
                        '/account', '/konto', '/contact', '/kontakt',
                        '/about', '/ueber', '/impressum', '/datenschutz',
                        '/agb', '/terms'
                    ]):
                        category_links.add(absolute_url)

        # Pattern 2: Category cards/tiles
        category_cards = (
            main_page_soup.find_all('a', class_=lambda x: x and ('category' in x.lower() or 'kategorie' in x.lower())) +
            main_page_soup.find_all('div', class_=lambda x: x and ('category' in x.lower() or 'kategorie' in x.lower()))
        )

        logging.debug(f"Found {len(category_cards)} category cards")

        for card in tqdm(category_cards, desc="Extracting category cards"):
            link = card if card.name == 'a' else card.find('a')
            if link:
                href = link.get('href')
                if href:
                    absolute_url = urljoin(MAIN_URL, href)
                    category_links.add(absolute_url)

        # Pattern 3: URL pattern scanning
        all_links = main_page_soup.find_all('a', href=True)

        for link in tqdm(all_links, desc="Scanning all links"):
            href = link.get('href')
            absolute_url = urljoin(MAIN_URL, href)

            # Match category URL patterns
            if any(pattern in absolute_url for pattern in [
                '/kategorie/', '/category/', '/product-category/',
                '/produktkategorie/', '/c/', '/cat/', '/collections/'
            ]):
                # Exclude product and system pages
                if not any(x in absolute_url.lower() for x in [
                    '/product/', '/produkt/', '/p/', '/detail/',
                    '?', '#', '/cart', '/checkout', '/account'
                ]):
                    category_links.add(absolute_url)

        # Filter and clean
        filtered_links = set()
        for url in category_links:
            clean_url = url.rstrip('/')
            path = clean_url.replace(MAIN_URL, '')
            if len(path) > 3:
                filtered_links.add(url)

        sorted_links = sorted(filtered_links)
        logging.info(f"Found {len(sorted_links)} unique category links")
        return sorted_links

    except Exception as e:
        logging.error(f"Error extracting category links: {e}", exc_info=True)
        return []
