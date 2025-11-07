"""
Extracts product detail page links from Gambler category pages.

Shopify product URLs: /products/{product-handle}
"""
import logging
from urllib.parse import urljoin
from tqdm import tqdm
from shared.html_loader import load_html_as_dom_tree
from gamblerlib.constants import MAIN_URL


def extract_all_product_detail_links(category_pages_downloaded_paths):
    """
    Extract all product detail page links from all category pages.

    :param category_pages_downloaded_paths: List of file paths to category pages
    :return: Sorted list of unique product detail URLs
    """
    product_links = set()

    with tqdm(total=len(category_pages_downloaded_paths),
              desc="Extracting product detail links") as pbar:
        for page_path in category_pages_downloaded_paths:
            page_dom = load_html_as_dom_tree(page_path)
            if page_dom:
                links = extract_product_detail_links_from_page(page_dom)
                product_links.update(links)
            pbar.update(1)

    logging.info(f"Found {len(product_links)} unique product links")
    return sorted(product_links)


def extract_product_detail_links_from_page(page_dom):
    """
    Extract product links from a single category page.

    Shopify specific: looks for /products/ URLs in product grid.

    :param page_dom: BeautifulSoup object of a category page
    :return: Set of product detail URLs
    """
    product_links = set()

    try:
        # Pattern 1: Shopify standard /products/ links
        product_url_links = page_dom.find_all('a', href=lambda x: x and '/products/' in x)
        logging.debug(f"Found {len(product_url_links)} links with /products/ in href")

        for link in product_url_links:
            href = link.get('href')
            if href:
                absolute_url = urljoin(MAIN_URL, href)
                # Exclude variant URLs with ? or #
                if '?' not in absolute_url and '#' not in absolute_url:
                    product_links.add(absolute_url)

        # Pattern 2: Product card/item links
        product_cards = page_dom.find_all(['div', 'article', 'li'], class_=lambda x: x and ('product' in x.lower() or 'item' in x.lower() or 'card' in x.lower()))
        logging.debug(f"Found {len(product_cards)} product card elements")

        for card in product_cards:
            # Find first link in the card
            link = card.find('a', href=lambda x: x and '/products/' in x)
            if link:
                href = link.get('href')
                if href:
                    absolute_url = urljoin(MAIN_URL, href)
                    if '?' not in absolute_url and '#' not in absolute_url:
                        product_links.add(absolute_url)

        # Pattern 3: Product grid links
        grid_links = page_dom.select('.product-grid a[href*="/products/"], .product-list a[href*="/products/"]')
        for link in grid_links:
            href = link.get('href')
            if href:
                absolute_url = urljoin(MAIN_URL, href)
                if '?' not in absolute_url and '#' not in absolute_url:
                    product_links.add(absolute_url)

        # Filter out collection/category URLs that might have been caught
        filtered_links = set()
        for url in product_links:
            # Must contain /products/ and not be a collection
            if '/products/' in url and '/collections/' not in url:
                filtered_links.add(url)

        logging.debug(f"Extracted {len(filtered_links)} product links from page")
        return filtered_links

    except Exception as e:
        logging.error(f"Error extracting product links: {e}", exc_info=True)
        return set()
