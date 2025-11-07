"""
Extracts product detail page links from Yinhe category pages.
"""
import logging
from urllib.parse import urljoin
from tqdm import tqdm
from shared.html_loader import load_html_as_dom_tree
from yinhelib.constants import MAIN_URL


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

    :param page_dom: BeautifulSoup object of a category page
    :return: Set of product detail URLs
    """
    product_links = set()

    # Try multiple patterns for product links
    # Pattern 1: Links with "product" in class or href
    product_elements = page_dom.find_all('a', href=True)

    for element in product_elements:
        href = element.get('href')
        if href:
            href_lower = href.lower()
            # Look for product-like URLs
            if any(pattern in href_lower for pattern in [
                '/product/', '/item/', '/p/', '/products/',
                '-p-', '/detail/', '/pd/'
            ]):
                # Skip non-product pages
                if not any(skip in href_lower for skip in [
                    'cart', 'checkout', 'account', 'login',
                    'category', 'collection', 'search', 'filter'
                ]):
                    absolute_url = urljoin(MAIN_URL, href)
                    # Only add if it looks like a valid product URL
                    if len(absolute_url.split('/')) >= 4:  # At least domain + path
                        product_links.add(absolute_url)

    # Pattern 2: Look for product cards/tiles
    if not product_links:
        product_cards = page_dom.find_all(['div', 'article'], class_=lambda x: x and (
            'product' in x.lower() or 'item' in x.lower() or 'card' in x.lower()
        ))

        for card in product_cards:
            link = card.find('a', href=True)
            if link:
                href = link.get('href')
                if href:
                    absolute_url = urljoin(MAIN_URL, href)
                    product_links.add(absolute_url)

    return product_links
