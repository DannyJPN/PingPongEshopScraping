import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from vsenastolnitenislib.constants import MAIN_URL
from tqdm import tqdm 

def extract_category_links(main_page_html):
    """
    Extracts category links from the main page HTML.

    :param main_page_html: BeautifulSoup object of the main page HTML.
    :return: Set of unique and sorted absolute URLs of the categories.
    """
    try:
        # Initialize an empty set to store unique category links
        category_links = set()

        # Find all div elements with the specific class
        div_elements = main_page_html.find_all("div", class_="col-xs-12 col-xl-3 media align-items-center")
        with tqdm(total=len(div_elements), desc="Extracting category links") as pbar:
            for div in div_elements:
                # Find the anchor tag inside the div
                a_tag = div.find("a", class_="nav-link u-header__sub-menu-nav-link")
                if a_tag and 'href' in a_tag.attrs:
                    relative_url = a_tag['href']
                    absolute_url = urljoin(MAIN_URL, relative_url)
                    category_links.add(absolute_url)
                pbar.update(1)

        # Return a sorted list of unique category links
        sorted_category_links = sorted(category_links)
        logging.debug(f"Extracted category links: {sorted_category_links}")
        return sorted_category_links

    except Exception as e:
        logging.error(f"Error extracting category links: {e}", exc_info=True)
        return set()