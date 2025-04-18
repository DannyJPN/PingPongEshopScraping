import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from tqdm import tqdm
from spinwaylib.constants import MAIN_URL

def extract_category_links(main_page_html):
    try:
        category_links = set()
        # Najdi všechny odkazy na kategorie ve struktuře mega menu
        nav = main_page_html.find('nav', class_='navigation')
        if not nav:
            logging.warning("No <nav class='navigation'> element found.")
            return set()
        links = nav.select("ul.main-nav a[href*='/kategoria-produktu/']")
        if not links:
            logging.warning("No category links found in mega menu structure.")
            return set()
        with tqdm(total=len(links), desc="Extracting category links") as pbar:
            for link in links:
                href = link.get('href')
                if href and '/kategoria-produktu/' in href:
                    category_links.add(href)
                pbar.update(1)
        return sorted(category_links)
    except Exception as e:
        logging.error(f"Error extracting category links: {e}", exc_info=True)
        return set()
        with tqdm(total=len(category_link_elements), desc="Extracting category links") as pbar:
            for link in category_link_elements:
                href = link.get('href')
                if href:
                    absolute_url = urljoin(MAIN_URL, href)
                    category_links.add(absolute_url)
                pbar.update(1)
        return sorted(category_links)
    except Exception as e:
        logging.error(f"Error extracting category links: {e}", exc_info=True)
        return set()