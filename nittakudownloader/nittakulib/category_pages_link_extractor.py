from bs4 import BeautifulSoup
from urllib.parse import urljoin
from nittakulib.constants import MAIN_URL
from shared.html_loader import load_html_as_dom_tree
from tqdm import tqdm
import logging

def extract_category_pages_links(category_page_dom):
    """
    Extract links to all pages of a category from the category page DOM.

    :param category_page_dom: BeautifulSoup object containing the parsed HTML of a category page
    :return: Set of links to all pages of the category
    """
    import re
    links = set()
    if category_page_dom is None:
        logging.error("Failed to parse HTML from category page - DOM is None")
        return links

    try:
        # Get base URL from canonical or meta tags
        base_url = None
        canonical = category_page_dom.find('link', rel='canonical')
        if canonical and canonical.get('href'):
            base_url = canonical['href']

        if not base_url:
            og_url = category_page_dom.find('meta', property='og:url')
            if og_url and og_url.get('content'):
                base_url = og_url['content']

        # Find all pagination links and extract page numbers
        page_numbers = set()
        for a in category_page_dom.find_all('a', href=True):
            href = a['href']
            if 'page=' in href:
                page_match = re.search(r'page=(\d+)', href)
                if page_match:
                    page_numbers.add(int(page_match.group(1)))
                links.add(urljoin(MAIN_URL, href))

        # If no base_url found yet, look for collection links
        if not base_url:
            for a in category_page_dom.find_all('a', href=True):
                href = a['href']
                if 'collections/' in href and 'page=' not in href:
                    base_url = urljoin(MAIN_URL, href)
                    break

        # Generate pagination URLs if we have a base URL
        if base_url:
            # Clean base URL (remove existing page parameter)
            if '?' in base_url:
                base_part, query_part = base_url.split('?', 1)
                query_params = [p for p in query_part.split('&') if not p.startswith('page=')]
                base_url = f"{base_part}?{'&'.join(query_params)}" if query_params else base_part

            # Add page 1
            links.add(f"{base_url}{'&' if '?' in base_url else '?'}page=1")

            # Add other pages
            max_page = max(page_numbers) if page_numbers else 2
            for page in range(2, max_page + 1):
                links.add(f"{base_url}{'&' if '?' in base_url else '?'}page={page}")

    except Exception as e:
        logging.error(f"Error extracting category pages links: {e}")

    return links

def extract_all_category_pages_links(category_firstpage_paths):
    category_page_links = set()
    with tqdm(total=len(category_firstpage_paths), desc="Extracting all category page links") as pbar:
        for firstpage_path in category_firstpage_paths:
            logging.debug(f"Loading HTML from: {firstpage_path}")
            firstpage_dom = load_html_as_dom_tree(firstpage_path)
            if firstpage_dom:
                links = extract_category_pages_links(firstpage_dom)
                logging.debug(f"Extracted links from {firstpage_path}: {links}")
                category_page_links.update(links)
            else:
                logging.error(f"Failed to load DOM for: {firstpage_path}")
            pbar.update(1)

    sorted_links = sorted(category_page_links)
    logging.debug(f"Final sorted category page links: {sorted_links}")
    return sorted_links
