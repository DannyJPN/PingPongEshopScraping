import logging
import re
from tqdm import tqdm
from urllib.parse import urljoin
from gewolib.product_attribute_extractor import get_self_link
from shared.html_loader import load_html_as_dom_tree
from gewolib.constants import MAIN_URL

def extract_all_product_variant_detail_links(product_detail_page_paths):
    """
    Extracts all product variant detail links from a list of product detail page file paths.

    :param product_detail_page_paths: List of file paths to downloaded product detail pages.
    :return: Set of unique and sorted absolute URLs of product variant detail links.
    """
    product_variant_detail_links = set()
    try:
        for path in tqdm(product_detail_page_paths, desc="Extracting product variant detail links"):
            logging.debug(f"Extracting product variants from {path}")
            dom_tree = load_html_as_dom_tree(path)
            if dom_tree:
                links = extract_product_variant_links(dom_tree)
                product_variant_detail_links.update(links)
        logging.debug(f"Extracted product variant detail links: {product_variant_detail_links}")
    except Exception as e:
        logging.error(f"Error extracting product variant detail links: {e}", exc_info=True)

    return sorted(product_variant_detail_links)

def extract_product_variant_links(dom_tree):
    """
    Extracts product variant URLs from the product detail page DOM tree.

    :param dom_tree: BeautifulSoup object of the product detail page.
    :return: Set of unique and sorted absolute URLs of product variant links.
    """
    try:
        variant_links = set()
        base_url = get_self_link(dom_tree)
        if not base_url:
            logging.debug("Base URL could not be determined.")
            return variant_links

        # Extract variants from the correct div
        variant_elements = dom_tree.find_all('div', class_='product-detail-configurator-group')
        if not variant_elements:
            logging.debug(f"No variants found, returning base URL only. {base_url}")
            variant_links.add(base_url)
            return variant_links

        variant_dict = {}
        for variant_element in variant_elements:
            key_tag = variant_element.find('div', class_='product-detail-buy__group')
            key = key_tag.get_text(strip=True).replace(':', '') if key_tag else ""
            values = []
            # Extract values from both possible locations
            value_elements = variant_element.find_all('li', class_=['tile-select__list-item', 'tile-select__list-item--is-text'])
            for value_element in value_elements:
                container_div = value_element.find('div', class_='tile-select__list-item-container')
                if container_div and container_div.find('div'):
                    # This is the second option
                    preview_span = value_element.find('span', class_='tile-select__preview--is-text')
                    if preview_span:
                        original_value = preview_span.get_text(strip=True)
                        logging.debug(f"Original variant value from span: {original_value}")
                        value = process_variant_value(original_value)
                        values.append(value)
                else:
                    # This is the first option
                    label = value_element.find('label', class_='tile-select__item-label')
                    if label:
                        original_value = label.get_text(strip=True)
                        logging.debug(f"Original variant value: {original_value}")
                        value = process_variant_value(original_value)
                        values.append(value)
            if values:
                variant_dict[key] = values

        # Generate all combinations of variant values
        from itertools import product
        logging.debug(f"Extracting {base_url}")
        for combination in product(*variant_dict.values()):
            variant_suffix = '-'.join(combination)
            variant_url = f"{base_url.rstrip('/')}-{variant_suffix}/"
            variant_links.add(variant_url)
            logging.debug(f"Generated variant URL: {variant_url}")

        return sorted(variant_links)
    except Exception as e:
        logging.error(f"Error extracting product variant links: {e}", exc_info=True)
        return set()

def process_variant_value(value):
    """
    Process the variant value by converting it to lowercase, replacing special characters,
    and removing any invalid characters.

    :param value: Original variant value.
    :return: Processed variant value.
    """
    value = value.lower()
    # Replace special characters with their phonetic equivalents
    value = value.replace('ü', 'ue').replace('ß', 'ss')
    value = value.replace('ä', 'ae').replace('ö', 'oe')
    value = value.replace('č', 'c').replace('š', 's').replace('ž', 'z')
    value = value.replace('á', 'a').replace('é', 'e').replace('í', 'i')
    value = value.replace('ó', 'o').replace('ú', 'u').replace('ý', 'y')
    value = value.replace('ě', 'e').replace('ř', 'r').replace('ť', 't')
    value = value.replace('ň', 'n').replace('ď', 'd')
    value = value.replace(' ', '-').replace('.', '-')
    value = re.sub(r'[-\/\+,]', '-', value)
    while '--' in value:
        value=value.replace("--","-")
    logging.debug(f"Processed variant value: {value}")
    return value