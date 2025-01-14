import logging
from urllib.parse import urljoin
from tqdm import tqdm
from gewolib.constants import MAIN_URL

def extract_category_links(main_page_soup):
    try:
        # Extract all hyperlink elements with the class 'menu__category' and 'navigation-category__entry'
        category_links = set()

        # Extract links with class 'menu__category'
        menu_category_links = main_page_soup.find_all('a', class_='menu__category')
        logging.debug(f"Found {len(menu_category_links)} links with class 'menu__category'")
        for link in tqdm(menu_category_links, desc="Extracting menu category links"):
            href = link.get('href')
            if href:
                # Convert relative URLs to absolute URLs
                absolute_url = urljoin(MAIN_URL, href)
                category_links.add(absolute_url)

        # Extract links with class 'navigation-category__entry' (and possibly other classes)
        navigation_category_links = main_page_soup.find_all('a', class_=lambda x: x and 'navigation-category__entry' in x.split())
        logging.debug(f"Found {len(navigation_category_links)} links with class 'navigation-category__entry'")
        for link in tqdm(navigation_category_links, desc="Extracting navigation category links"):
            href = link.get('href')
            if href and href.startswith('http'):
                # Add only absolute URLs
                category_links.add(href)

        # Return a sorted set of unique URLs
        sorted_links = sorted(category_links)
        logging.debug(f"Extracted category links: {sorted_links}")
        return sorted_links

    except Exception as e:
        logging.error(f"Error extracting category links: {e}", exc_info=True)
        return set()