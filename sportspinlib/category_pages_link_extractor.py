import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from sportspinlib.constants import MAIN_URL
from tqdm import tqdm
from shared.html_loader import load_html_as_dom_tree 
from sportspinlib.product_attribute_extractor import get_self_link


def extract_all_category_pages_links(category_firstpage_paths):
    category_page_links = set()
    with tqdm(total=len(category_firstpage_paths), desc="Downloading main images") as pbar:
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
    :param MAIN_URL: The base URL of the website.
    :return: List of sorted unique absolute URLs of the category pages.
    """
    try:
        page_links = set()
        next_page_link = category_page_dom.find('a', class_='next pagination-link')
        logging.debug(f"Next page link found: {next_page_link}")

        if next_page_link:
            # Find the neighboring hyperlink element which is the last page link
            last_page_link = next_page_link.find_next_sibling('a')
            logging.debug(f"Last page link found: {last_page_link}")

            if last_page_link:
                last_page_href = last_page_link['href']
                logging.debug(f"Last page href: {last_page_href}")
                last_page_url = urljoin(MAIN_URL, last_page_href)
                logging.debug(f"Last page URL: {last_page_url}")
                last_page_number = int(last_page_href.strip("/").split('strana-')[-1])
                for i in range(1, last_page_number + 1):
                    full_page_url = urljoin(MAIN_URL, f"{last_page_href.split('strana-')[0]}strana-{i}/")
                    logging.debug(f"Adding page URL: {full_page_url}")
                    page_links.add(full_page_url)
        else:
            # Only one page exists
            category_main_url = get_self_link(category_page_dom)
            logging.debug(f"Base URL from meta tag: {category_main_url}")
            first_page_url = f"{category_main_url.rstrip('/')}/strana-1/"
            logging.debug(f"Only one page URL: {first_page_url}")
            page_links.add(first_page_url)

        
        unique_sorted_page_links = sorted(page_links)
        logging.debug(f"Unique sorted page links: {unique_sorted_page_links}")
        return unique_sorted_page_links

    except Exception as e:
        logging.error(f"Error extracting category page links: {e}", exc_info=True)
        return []