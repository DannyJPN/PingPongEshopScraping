import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from tqdm import tqdm
from nittakulib.constants import MAIN_URL

def extract_category_links(main_page_html):
    """
    Extracts category links from the main page HTML.

    :param main_page_html: BeautifulSoup object containing the HTML DOM of the main page.
    :return: Set of absolute URLs for the category links.
    """
    try:
        category_links = set()

        # Find all <a> elements with class containing "link"
        links = main_page_html.find_all('a', class_=lambda x: x and 'link' in x)
        logging.debug(f"Filtered <a> elements count: {len(links)}")

        # Initialize the progress bar with the total number of links
        with tqdm(total=len(links), desc="Extracting category links") as pbar:
            for link in links:
                relative_url = link.get('href')
                # Check if the href attribute contains the string "collections"
                if relative_url and "collections" in relative_url:
                    absolute_url = urljoin(MAIN_URL, relative_url)
                    category_links.add(absolute_url)
                pbar.update(1)  # Update the progress bar

        # Return sorted set of unique URLs
        unique_sorted_links = sorted(category_links)
        logging.debug(f"Unique sorted links: {len(unique_sorted_links)}")
        logging.debug(f"Sorted URLs: {unique_sorted_links}")
        return unique_sorted_links

    except Exception as e:
        logging.error(f"Error extracting category links: {e}", exc_info=True)
        return set()