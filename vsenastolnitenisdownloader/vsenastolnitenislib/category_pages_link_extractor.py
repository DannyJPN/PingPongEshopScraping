import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from vsenastolnitenislib.constants import MAIN_URL
from tqdm import tqdm
from shared.html_loader import load_html_as_dom_tree
from vsenastolnitenislib.product_attribute_extractor import get_self_link

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
    try:
        # Initialize a set to store the unique page links
        page_links = set()

        # Find the "konec" element which indicates the last page (case-insensitive search)
        konec_element = category_page_dom.find('a', title=lambda value: value and value.lower() == "konec")

        # If the "konec" element is found, extract the maximum limitstart value
        if konec_element:
            last_page_url = konec_element['href']
            logging.debug(f"Found 'konec' element with relative URL: {last_page_url}")
            last_limitstart = int(last_page_url.split('limitstart=')[-1])
        else:
            last_limitstart = 0
            logging.debug("No 'konec' element found, setting last_limitstart to 0")

        # Generate URLs for all pages from limitstart=0 to limitstart=last_limitstart with step of 20
        for i in range(0, last_limitstart + 1, 20):
            if konec_element:
                page_url = last_page_url.replace(f"limitstart={last_limitstart}", f"limitstart={i}")
                absolute_page_url = urljoin(MAIN_URL, page_url)
                logging.debug(f"Generated page URL: {absolute_page_url}")
                page_links.add(absolute_page_url)
            else:
                # If no "konec" element, generate the URL directly
                page_url = f"{get_self_link(category_page_dom)}?limitstart=0"
                logging.debug(f"Generated page URL without 'konec': {page_url}")
                page_links.add(page_url)

        # Return the sorted set of unique URLs
        sorted_page_links = sorted(page_links)
        logging.debug(f"Sorted unique page links: {sorted_page_links}")
        return sorted_page_links

    except Exception as e:
        logging.error(f"Error extracting category pages links: {e}", exc_info=True)
        return set()










