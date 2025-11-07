"""
Extracts paginated category page links from Asics.
"""
import logging
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
from tqdm import tqdm
from shared.html_loader import load_html_as_dom_tree
from asicslib.product_attribute_extractor import get_self_link


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
    category_url = get_self_link(category_page_dom)
    page_links = set()
    page_links.add(category_url)  # Always include the first page

    try:
        # Pattern 1: Find pagination links
        pagination_elements = category_page_dom.find_all(['a', 'button'], class_=lambda x: x and (
            'page' in x.lower() or 'pagination' in x.lower()
        ))

        if pagination_elements:
            for element in pagination_elements:
                href = element.get('href')
                if href:
                    absolute_url = urljoin(category_url, href)
                    page_links.add(absolute_url)

        # Pattern 2: Find last page number and generate URLs
        # Look for page numbers in pagination
        page_numbers = []
        for element in pagination_elements:
            text = element.get_text(strip=True)
            if text.isdigit():
                page_numbers.append(int(text))

        if page_numbers:
            last_page = max(page_numbers)
            parsed_url = urlparse(category_url)

            # Try different pagination patterns
            for page_num in range(1, last_page + 1):
                # Pattern: ?page=X
                query_params = parse_qs(parsed_url.query)
                query_params['page'] = [str(page_num)]
                new_query = urlencode(query_params, doseq=True)
                page_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{new_query}"
                page_links.add(page_url)

        logging.debug(f"Found {len(page_links)} pages for category {category_url}")

    except Exception as e:
        logging.error(f"Error extracting pagination: {e}", exc_info=True)

    return page_links
