from bs4 import BeautifulSoup
import json
import logging
from nittakulib.constants import MAIN_URL
from urllib.parse import urljoin
from shared.html_loader import load_html_as_dom_tree
from tqdm import tqdm

class Product:
    def __init__(self):
        self.name = ""
        self.short_description = ""
        self.description = ""
        self.variants = ""
        self.main_photo_link = ""
        self.main_photo_filepath = ""
        self.photogallery_links = []
        self.photogallery_filepaths = []
        self.url = ""

def get_self_link(dom_tree):
    canonical = dom_tree.find('link', rel='canonical')
    return canonical['href'] if canonical and canonical.get('href') else ""

def extract_product_name(dom_tree):
    """
    Extract product name from the product detail page DOM.

    :param dom_tree: BeautifulSoup object containing the parsed HTML of a product detail page
    :return: Product name as string
    """
    # Find the main product heading (h1)
    h1 = dom_tree.find('h1', class_=lambda c: c and 'product-meta__title' in c)
    if h1:
        product_name = h1.get_text(strip=True)
        logging.debug(f"Found product name in h1.product-meta__title: {product_name}")
        return product_name

    # If not found, try the main heading without class
    h1 = dom_tree.find('h1')
    if h1:
        product_name = h1.get_text(strip=True)
        logging.debug(f"Found product name in h1: {product_name}")
        return product_name

    # If still not found, try meta title
    meta_title = dom_tree.find('meta', property='og:title')
    if meta_title and meta_title.get('content'):
        content = meta_title['content']
        # Remove site name if present
        if ' – ' in content:
            product_name = content.split(' – ')[0].strip()
        elif ' | ' in content:
            product_name = content.split(' | ')[0].strip()
        else:
            product_name = content
        logging.debug(f"Found product name in meta title: {product_name}")
        return product_name

    # Last resort: page title
    title = dom_tree.find('title')
    if title:
        title_text = title.get_text(strip=True)
        if ' – ' in title_text:
            product_name = title_text.split(' – ')[0].strip()
        elif ' | ' in title_text:
            product_name = title_text.split(' | ')[0].strip()
        else:
            product_name = title_text
        logging.debug(f"Found product name in title: {product_name}")
        return product_name

    return ""

def extract_product_short_description(dom_tree):
    """
    Extract short description from the product detail page DOM.

    :param dom_tree: BeautifulSoup object containing the parsed HTML of a product detail page
    :return: Short description as HTML string in a single line with <br> tags
    """
    # Find the first h1 tag in the product description
    desc_div = dom_tree.find('div', class_='rte text--pull')
    if desc_div and desc_div.find('h1'):
        h1_tag = desc_div.find('h1')
        short_desc = str(h1_tag)
        # Replace newlines with <br> tags
        short_desc = short_desc.replace('\n', '<br>').replace('\r', '')
        logging.debug(f"Found short description in h1 tag: {short_desc[:50]}...")
        return short_desc

    # If not found, try the first paragraph in the description
    if desc_div and desc_div.find('p'):
        p_tag = desc_div.find('p')
        short_desc = str(p_tag)
        # Replace newlines with <br> tags
        short_desc = short_desc.replace('\n', '<br>').replace('\r', '')
        logging.debug(f"Found short description in first paragraph: {short_desc[:50]}...")
        return short_desc

    # If still not found, try meta description
    meta_desc = dom_tree.find('meta', property='og:description')
    if meta_desc and meta_desc.get('content'):
        content = meta_desc['content']
        # Replace newlines with <br> tags
        content = content.replace('\n', '<br>').replace('\r', '')
        short_desc = f"<p>{content}</p>"
        logging.debug(f"Found short description in meta description: {short_desc[:50]}...")
        return short_desc

    return ""

def extract_product_description(dom_tree):
    """
    Extract full description from the product detail page DOM.

    :param dom_tree: BeautifulSoup object containing the parsed HTML of a product detail page
    :return: Full description as HTML string in a single line with <br> tags
    """
    # Find the product description in the rte text--pull div
    desc_div = dom_tree.find('div', class_='rte text--pull')
    if desc_div:
        desc_html = str(desc_div)
        # Replace newlines with <br> tags and ensure it's a single line
        desc_html = desc_html.replace('\n', '<br>').replace('\r', '')
        logging.debug(f"Found description in div.rte.text--pull, length: {len(desc_html)}")
        return desc_html

    # If not found, try product-description div
    desc = dom_tree.find('div', class_='product-description')
    if desc:
        desc_html = str(desc)
        # Replace newlines with <br> tags and ensure it's a single line
        desc_html = desc_html.replace('\n', '<br>').replace('\r', '')
        logging.debug(f"Found description in div.product-description, length: {len(desc_html)}")
        return desc_html

    # If still not found, try description div
    desc = dom_tree.find('div', class_='description')
    if desc:
        desc_html = str(desc)
        # Replace newlines with <br> tags and ensure it's a single line
        desc_html = desc_html.replace('\n', '<br>').replace('\r', '')
        logging.debug(f"Found description in div.description, length: {len(desc_html)}")
        return desc_html

    return ""

def extract_product_variants(dom_tree):
    """
    Extract product variants from the product detail page DOM.

    :param dom_tree: BeautifulSoup object containing the parsed HTML of a product detail page
    :return: Dictionary with variant information
    """
    try:
        # Initialize result dictionary
        variants_data = {
            "key_value_pairs": [],
            "current_price": "",
            "basic_price": "",
            "stock_status": ""
        }

        # Find all variant selectors (color, size, etc.)
        variant_selectors = dom_tree.find_all('div', class_='product-form__option')

        # Extract all variant options
        for selector in variant_selectors:
            option_name = selector.find('span', class_='product-form__option-name')
            if option_name:
                option_name = option_name.get_text(strip=True).replace(':', '')

                # Find all options for this selector
                # First try radio inputs
                options = selector.find_all('input', {'type': 'radio'})
                if options:
                    for option in options:
                        if option.get('value'):
                            variants_data["key_value_pairs"].append([option_name, option.get('value')])
                else:
                    # Try select options
                    select = selector.find('select')
                    if select:
                        for option in select.find_all('option'):
                            if option.get('value') and not option.get('value').startswith('Default'):
                                variants_data["key_value_pairs"].append([option_name, option.get_text(strip=True)])

        # Get price information
        price = dom_tree.find('span', class_='product-meta__price')
        if price:
            variants_data["current_price"] = price.get_text(strip=True)

        # Get stock status
        stock = dom_tree.find('span', class_='product-form__inventory')
        if stock:
            variants_data["stock_status"] = stock.get_text(strip=True)

        return variants_data
    except Exception as e:
        logging.error(f"Error extracting variants: {e}")
        return {"key_value_pairs": [], "current_price": "", "basic_price": "", "stock_status": ""}

def extract_product_main_photo_link(dom_tree):
    """
    Extract main product image URL from the product detail page DOM.

    :param dom_tree: BeautifulSoup object containing the parsed HTML of a product detail page
    :return: URL of the main product image
    """
    try:
        # Find meta og:image tag (usually the main product image)
        meta_img = dom_tree.find('meta', property='og:image')
        if meta_img and meta_img.get('content'):
            img_url = meta_img['content']

            # Make sure it's a full URL
            if img_url.startswith('//'):  # Protocol-relative URL
                img_url = 'https:' + img_url
            elif not img_url.startswith(('http://', 'https://')):  # Relative URL
                img_url = urljoin(MAIN_URL, img_url)

            # Replace size indicators with highest quality version
            for size in ['_800x', '_600x', '_500x', '_400x', '_300x', '_200x', '_130x', '_100x', '_60x']:
                if size in img_url:
                    img_url = img_url.replace(size, '_1600x')
                    break

            # Note: We keep the original URL format (webp) for downloading
            # The conversion from webp to jpg will happen in the image_downloader

            logging.debug(f"Found main photo in meta og:image: {img_url}")
            return img_url

        # If no meta tag, try to find the first product image
        product_images = dom_tree.find_all('img')
        for img in product_images:
            if img.get('src') and not ('icon' in img.get('src').lower() or 'logo' in img.get('src').lower()):
                img_url = img['src']

                # Make sure it's a full URL
                if img_url.startswith('//'):  # Protocol-relative URL
                    img_url = 'https:' + img_url
                elif not img_url.startswith(('http://', 'https://')):  # Relative URL
                    img_url = urljoin(MAIN_URL, img_url)

                # Replace size indicators with highest quality version
                for size in ['_800x', '_600x', '_500x', '_400x', '_300x', '_200x', '_130x', '_100x', '_60x']:
                    if size in img_url:
                        img_url = img_url.replace(size, '_1600x')
                        break

                # Note: We keep the original URL format (webp) for downloading
                # The conversion from webp to jpg will happen in the image_downloader

                logging.debug(f"Found main photo in product images: {img_url}")
                return img_url

        return ""
    except Exception as e:
        logging.error(f"Error extracting main photo: {e}")
        return ""

def extract_product_photogallery_links(dom_tree):
    """
    Extract product gallery image URLs from the product detail page DOM.

    :param dom_tree: BeautifulSoup object containing the parsed HTML of a product detail page
    :return: List of URLs of product gallery images
    """
    links = []
    try:
        # Find all product images in the gallery
        all_images = dom_tree.find_all('img')
        main_img_url = extract_product_main_photo_link(dom_tree)

        # Process each image
        for img in all_images:
            if img.get('src'):
                img_url = img['src']

                # Skip icons, logos, and other non-product images
                if any(x in img_url.lower() for x in ['icon', 'logo', 'payment', 'social']):
                    continue

                # Make sure it's a full URL
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif not img_url.startswith(('http://', 'https://')):
                    img_url = urljoin(MAIN_URL, img_url)

                # Replace size indicators with highest quality version
                for size in ['_800x', '_600x', '_500x', '_400x', '_300x', '_200x', '_130x', '_100x', '_60x']:
                    if size in img_url:
                        img_url = img_url.replace(size, '_1600x')
                        break

                # Note: We keep the original URL format (webp) for downloading
                # The conversion from webp to jpg will happen in the image_downloader

                # Add to links if not already there and not the main image
                if img_url != main_img_url and img_url not in links:
                    links.append(img_url)
                    logging.debug(f"Found gallery image: {img_url}")

        logging.debug(f"Extracted {len(links)} gallery images")
        return links
    except Exception as e:
        logging.error(f"Error extracting gallery photos: {e}")
        return []

def extract_product(filepath):
    try:
        soup = load_html_as_dom_tree(filepath)
        if soup is None:
            logging.error(f"Failed to parse HTML from {filepath}")
            return None

        # Check if the page is a verification page or error page
        title = soup.find('title')
        if title:
            title_text = title.get_text().lower()
            if any(phrase in title_text for phrase in ["connection needs to be verified", "error", "not found", "404", "403", "500"]):
                logging.warning(f"Skipping error/verification page: {filepath} with title: {title_text}")
                return None

        # Check if the page has minimal required content
        if not soup.find_all(['h1', 'h2', 'div', 'span', 'p']):
            logging.warning(f"Skipping page with insufficient content: {filepath}")
            return None

        product = Product()
        product.name = extract_product_name(soup)

        # Skip if we couldn't extract a product name
        if not product.name:
            logging.warning(f"Skipping page with no product name: {filepath}")
            return None

        product.short_description = extract_product_short_description(soup)
        product.description = extract_product_description(soup)
        product.variants = extract_product_variants(soup)
        product.main_photo_link = extract_product_main_photo_link(soup)
        product.photogallery_links = extract_product_photogallery_links(soup)
        product.url = get_self_link(soup)

        return product
    except Exception as e:
        logging.error(f"Error extracting product from {filepath}: {e}", exc_info=True)
        return None

def extract_products(product_detail_page_paths):
    products = []
    with tqdm(total=len(product_detail_page_paths), desc="Extracting products") as pbar:
        for path in product_detail_page_paths:
            product = extract_product(path)
            if product:
                products.append(product)
            pbar.update(1)
    return products
