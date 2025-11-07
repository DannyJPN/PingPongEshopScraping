"""
Extracts paginated category page links from Hallmark.
"""
import logging
from urllib.parse import urljoin, urlparse, parse_qs
from tqdm import tqdm
from shared.html_loader import load_html_as_dom_tree
from hallmarklib.product_attribute_extractor import get_self_link


def extract_all_category_pages_links(category_firstpage_paths):
    """
    Extract all paginated category page links.

    :param category_firstpage_paths: List of file paths to first pages of categories
    :return: Sorted list of all category page URLs (including pagination)
    """
    all_page_links = set()

    with tqdm(total=len(category_firstpage_paths), desc="Extracting category page links") as pbar:
        for page_path in category_firstpage_paths:
            page_dom = load_html_as_dom_tree(page_path)
            if page_dom:
                page_links = extract_category_pages_links(page_dom)
                all_page_links.update(page_links)
            pbar.update(1)

    logging.info(f"Total category pages (with pagination): {len(all_page_links)}")
    return sorted(all_page_links)


def extract_category_pages_links(category_page_dom):
    """
    Extract all page links for a single category (handles pagination).

    :param category_page_dom: BeautifulSoup object of a category page
    :return: Set of URLs for all pages in this category
    """
    try:
        category_url = get_self_link(category_page_dom)
        page_links = set()

        # Pattern 1: Find last page number from pagination
        pagination_links = category_page_dom.find_all('a', class_=lambda x: x and 'page' in x.lower())
        page_numbers = []

        for link in pagination_links:
            text = link.get_text(strip=True)
            if text.isdigit():
                page_numbers.append(int(text))

            # Also check href for page numbers
            href = link.get('href')
            if href:
                parsed = parse_qs(urlparse(href).query)
                if 'page' in parsed:
                    try:
                        page_numbers.append(int(parsed['page'][0]))
                    except:
                        pass

        if page_numbers:
            last_page = max(page_numbers)
            for page_num in range(1, last_page + 1):
                page_url = f"{category_url}?page={page_num}"
                page_links.add(page_url)
        else:
            # No pagination found - just add the category URL itself
            page_links.add(category_url)

        logging.debug(f"Found {len(page_links)} pages for category {category_url}")
        return page_links

    except Exception as e:
        logging.error(f"Error extracting pagination: {e}", exc_info=True)
        # Fallback - at least first page
        try:
            page_links = set()
            page_links.add(get_self_link(category_page_dom))
            return page_links
        except:
            return set()
