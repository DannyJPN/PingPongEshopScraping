import logging
from urllib.parse import urljoin
from tqdm import tqdm
from shared.html_loader import load_html_as_dom_tree
from gewolib.product_attribute_extractor import get_self_link

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

def extract_category_pages_links(category_page_dom):
    try:
        category_url = get_self_link(category_page_dom)
        #last_page_element_li = category_page_dom.find('li', class_='page-item page-last')
        last_page_element = category_page_dom.find('input', {'type': 'radio', 'name': 'p', 'id':'p-last'})

        if last_page_element:
            last_page_num = int(last_page_element['value'])
        else:
            last_page_num = 1

        logging.debug(f"Category URL: {category_url}, Last Page Number: {last_page_num}")

        page_links = set()
        for page_num in range(1, last_page_num + 1):
            page_url = f"{category_url}?p={page_num}"
            page_links.add(page_url)

        return sorted(page_links)
    except Exception as e:
        logging.error(f"Error extracting category pages links: {e}", exc_info=True)
        return set()










