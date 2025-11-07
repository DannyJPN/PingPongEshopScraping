"""
Extracts product detail page links from Der Materialspezialist category pages.

German e-commerce patterns:
- Shopware: /detail/, /produkt/, /product/
- WooCommerce: /product/, /produkt/
- Product cards with specific CSS classes
"""
import logging
from urllib.parse import urljoin
from tqdm import tqdm
from shared.html_loader import load_html_as_dom_tree
from dermaterialspezialistlib.constants import MAIN_URL


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
        # Pattern 1: German/English product URL patterns in links
        all_links = page_dom.find_all('a', href=True)

        for link in all_links:
            href = link.get('href')
            if href:
                absolute_url = urljoin(MAIN_URL, href)

                # Match German/English product URL patterns
                if any(pattern in absolute_url for pattern in [
                    '/product/', '/produkt/', '/detail/', '/p/',
                    '/artikel/', '/item/'
                ]):
                    # Exclude category pages and system pages
                    if not any(x in absolute_url.lower() for x in [
                        '/category/', '/kategorie/', '/collection/',
                        '?page=', '&page=', '/cart', '/checkout',
                        '/account', '#', '?filter', '&filter'
                    ]):
                        # Ensure it's not just a category with 'product' in name
                        if not absolute_url.endswith('/products') and not absolute_url.endswith('/produkte'):
                            product_links.add(absolute_url)

        # Pattern 2: Shopware/WooCommerce product cards
        product_cards = (
            page_dom.find_all('article', class_=lambda x: x and ('product' in x.lower() or 'item' in x.lower())) +
            page_dom.find_all('div', class_=lambda x: x and ('product' in x.lower() or 'item' in x.lower())) +
            page_dom.find_all('li', class_=lambda x: x and ('product' in x.lower() or 'item' in x.lower()))
        )

        for card in product_cards:
            # Find link within card
            link = card.find('a', href=True)
            if link:
                href = link.get('href')
                absolute_url = urljoin(MAIN_URL, href)

                # Verify it's a product link
                if any(pattern in absolute_url for pattern in [
                    '/product/', '/produkt/', '/detail/', '/p/', '/artikel/'
                ]):
                    product_links.add(absolute_url)

        # Pattern 3: Product title/name links (common pattern)
        product_titles = (
            page_dom.select('.product-name a') +
            page_dom.select('.product-title a') +
            page_dom.select('.produkt-name a') +
            page_dom.select('h2 a') +
            page_dom.select('h3 a')
        )

        for title_link in product_titles:
            href = title_link.get('href')
            if href:
                absolute_url = urljoin(MAIN_URL, href)

                # Verify it looks like a product
                if any(pattern in absolute_url for pattern in [
                    '/product/', '/produkt/', '/detail/', '/p/', '/artikel/'
                ]):
                    product_links.add(absolute_url)

        # Pattern 4: Image links in product cards
        product_images = page_dom.select('.product-image a, .product-img a, .produkt-bild a')

        for img_link in product_images:
            href = img_link.get('href')
            if href:
                absolute_url = urljoin(MAIN_URL, href)
                if any(pattern in absolute_url for pattern in [
                    '/product/', '/produkt/', '/detail/', '/p/', '/artikel/'
                ]):
                    product_links.add(absolute_url)

        # Filter out unwanted URLs
        filtered_links = set()
        for url in product_links:
            # Remove query parameters and anchors for cleaner URLs
            clean_url = url.split('?')[0].split('#')[0]

            # Ensure minimum path length (not just domain)
            path = clean_url.replace(MAIN_URL, '')
            if len(path) > 5:  # At least /p/xxx
                filtered_links.add(clean_url)

        logging.debug(f"Extracted {len(filtered_links)} product links from page")

    except Exception as e:
        logging.error(f"Error extracting product links: {e}", exc_info=True)

    return filtered_links
