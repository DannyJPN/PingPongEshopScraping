import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from stotenlib.constants import MAIN_URL
from tqdm import tqdm
from shared.html_loader import load_html_as_dom_tree
from stotenlib.product_attribute_extractor import get_self_link


def extract_all_category_pages_links(category_firstpage_paths):
    category_page_links = set()
    with tqdm(total=len(category_firstpage_paths), desc="Extracting all category page links") as pbar:
        for firstpage_path in category_firstpage_paths:
            firstpage_dom = load_html_as_dom_tree(firstpage_path)
            category_page_links.update(extract_category_pages_links(firstpage_dom))
            pbar.update(1)
    logging.debug(category_page_links)
    return category_page_links

def extract_category_pages_links(category_page_dom):
    """
    Extracts page URLs from the category page HTML.

    :param category_page_dom: BeautifulSoup object of the category page HTML.
    :param self_link: The URL of the current category page.
    :return: List of sorted unique absolute URLs of the category pages.
    """
    try:
        page_links = set()
        pagination_div = category_page_dom.find('div', class_='pagination', attrs={'data-testid': 'gridPagination'})
        category_main_url = get_self_link(category_page_dom)
        if not pagination_div:
            # Only one page exists
            logging.debug(f"Base URL from meta tag: {category_main_url}")
            first_page_url = f"{category_main_url.rstrip('/')}/strana-1/"
            logging.debug(f"Only one page URL: {first_page_url}")
            page_links.add(first_page_url)
            return page_links

        link_last_page = pagination_div.find('a', attrs={'data-testid': 'linkLastPage'})
        if link_last_page:
            # More than 3 pages exist
            logging.debug("Found linkLastPage element, indicating more than 3 pages exist.")
            last_page_url = urljoin(MAIN_URL, link_last_page['href'])
            last_page_number = int(last_page_url.strip("/").split('strana-')[-1])
            base_url = category_main_url.rsplit('strana-', 1)[0]
            for i in range(1, last_page_number + 1):
                page_links.add(f"{base_url}strana-{i}")
            logging.debug(f"Extracted URLs for more than 3 pages: {page_links}")
            return page_links

        # 2-3 pages exist
        logging.debug("Pagination div exists but no linkLastPage element found, indicating 2-3 pages exist.")
        pagination_links = pagination_div.find_all('a', class_='pagination-page', attrs={'data-testid': 'linkPage'})
        page_links.add(f"{category_main_url.rstrip('/')}/strana-1/")
        for link in pagination_links:
            page_links.add(urljoin(MAIN_URL, link['href']))
        logging.debug(f"Extracted URLs for 2-3 pages: {page_links}")
        return page_links

    except Exception as e:
        logging.error(f"Error extracting category pages links: {e}", exc_info=True)
        return {}










