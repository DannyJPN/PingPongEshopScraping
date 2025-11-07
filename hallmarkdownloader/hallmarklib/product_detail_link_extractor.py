"""
Extracts product detail page links from Hallmark category pages.
"""
import logging
from urllib.parse import urljoin
from tqdm import tqdm
from shared.html_loader import load_html_as_dom_tree
from hallmarklib.constants import MAIN_URL


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

    try:
        # Pattern 1: Product card links
        product_cards = page_dom.find_all('a', class_=lambda x: x and ('product' in x.lower() or 'item' in x.lower()))

        for card in product_cards:
            href = card.get('href')
            if href:
                absolute_url = urljoin(MAIN_URL, href)
                # Filter for product-like URLs
                if '/product/' in absolute_url or '/item/' in absolute_url:
                    product_links.add(absolute_url)

        # Pattern 2: Direct product links
        product_elements = page_dom.select('a[href*="product"], a[href*="/p/"], a[href*="/item/"]')

        for element in product_elements:
            href = element.get('href')
            if href:
                absolute_url = urljoin(MAIN_URL, href)
                product_links.add(absolute_url)

        logging.debug(f"Extracted {len(product_links)} product links from page")

    except Exception as e:
        logging.error(f"Error extracting product links: {e}", exc_info=True)

    return product_links
