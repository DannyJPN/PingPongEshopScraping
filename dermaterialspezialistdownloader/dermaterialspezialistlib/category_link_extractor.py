"""
Extracts category links from Der Materialspezialist main page.

Der Materialspezialist uses Shopware/WooCommerce platform - common German patterns:
- Shopware: /kategorie/, /category/, navigation structure
- WooCommerce: /product-category/, /produktkategorie/
- Standard navigation menu extraction
"""
import logging
from urllib.parse import urljoin
from tqdm import tqdm
from dermaterialspezialistlib.constants import MAIN_URL


def extract_category_links(main_page_soup):
    """
    Extract all category links from the main page DOM.

    :param main_page_soup: BeautifulSoup object of the main page
    :return: Sorted list of unique absolute category URLs
    """
    try:
        category_links = set()

        # Pattern 1: Shopware/WooCommerce navigation - common German e-commerce
        nav_elements = (
            main_page_soup.select('nav a') +
            main_page_soup.select('.navigation a') +
            main_page_soup.select('.nav a') +
            main_page_soup.select('.menu a') +
            main_page_soup.select('.main-navigation a') +
            main_page_soup.select('header a')
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
                    '/sortiment/', '/shop/'
                ]):
                    # Exclude non-category pages
                    if not any(x in absolute_url.lower() for x in [
                        '/cart', '/warenkorb', '/checkout', '/kasse',
                        '/account', '/konto', '/contact', '/kontakt',
                        '/about', '/ueber', '/impressum', '/datenschutz'
                    ]):
                        category_links.add(absolute_url)

        # Pattern 2: Category cards/tiles (common in modern e-shops)
        category_cards = (
            main_page_soup.find_all('a', class_=lambda x: x and ('category' in x.lower() or 'kategorie' in x.lower())) +
            main_page_soup.find_all('div', class_=lambda x: x and ('category' in x.lower() or 'kategorie' in x.lower()))
        )

        logging.debug(f"Found {len(category_cards)} category cards")

        for card in tqdm(category_cards, desc="Extracting category cards"):
            # Find link within card
            link = card if card.name == 'a' else card.find('a')
            if link:
                href = link.get('href')
                if href:
                    absolute_url = urljoin(MAIN_URL, href)
                    category_links.add(absolute_url)

        # Pattern 3: Direct URL pattern matching in all links
        all_links = main_page_soup.find_all('a', href=True)

        for link in tqdm(all_links, desc="Scanning all links for category patterns"):
            href = link.get('href')
            absolute_url = urljoin(MAIN_URL, href)

            # Match German/English category URL patterns
            if any(pattern in absolute_url for pattern in [
                '/kategorie/', '/category/', '/product-category/',
                '/produktkategorie/', '/c/', '/cat/'
            ]):
                # Exclude non-category pages
                if not any(x in absolute_url.lower() for x in [
                    '/product/', '/produkt/', '/p/', '/detail/',
                    '?', '#', '/cart', '/checkout', '/account'
                ]):
                    category_links.add(absolute_url)

        # Remove duplicates and filter
        filtered_links = set()
        for url in category_links:
            # Clean URL (remove trailing slashes for comparison)
            clean_url = url.rstrip('/')
            # Exclude very short paths that are likely not categories
            path = clean_url.replace(MAIN_URL, '')
            if len(path) > 3:  # At least some path like /c/x
                filtered_links.add(url)

        sorted_links = sorted(filtered_links)
        logging.info(f"Found {len(sorted_links)} unique category links")
        return sorted_links

    except Exception as e:
        logging.error(f"Error extracting category links: {e}", exc_info=True)
        return []
