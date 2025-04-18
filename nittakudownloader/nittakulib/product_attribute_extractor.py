from bs4 import BeautifulSoup
import json
from nittakulib.constants import MAIN_URL
from urllib.parse import urljoin

def get_self_link(dom_tree):
    canonical = dom_tree.find('link', rel='canonical')
    return canonical['href'] if canonical and canonical.get('href') else ""

def extract_product_name(dom_tree):
    h1 = dom_tree.find('h1')
    return h1.get_text(strip=True) if h1 else ""

def extract_product_short_description(dom_tree):
    p = dom_tree.find('p')
    return p.get_text(strip=True) if p else ""

def extract_product_description(dom_tree):
    desc = dom_tree.find('div', class_='description')
    return str(desc) if desc else ""

def extract_product_variants(dom_tree):
    return []

def extract_product_prices(dom_tree):
    prices = []
    for tag in dom_tree.find_all(['span', 'div']):
        text = tag.get_text()
        if any(c in text for c in ['â‚¬', '$']):
            prices.append(text.strip())
    return prices

def extract_availability_tag(dom_tree):
    text = dom_tree.get_text().lower()
    if 'in stock' in text:
        return 'In stock'
    elif 'out of stock' in text:
        return 'Out of stock'
    return 'Unknown'

def extract_product_main_photo_link(dom_tree):
    img = dom_tree.find('img')
    return urljoin(MAIN_URL, img['src']) if img and img.get('src') else ""

def extract_product_photogallery_links(dom_tree):
    links = []
    for img in dom_tree.find_all('img'):
        if img.get('src'):
            links.append(urljoin(MAIN_URL, img['src']))
    return links

def extract_product(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')
    return {
        'name': extract_product_name(soup),
        'short_description': extract_product_short_description(soup),
        'description': extract_product_description(soup),
        'variants': extract_product_variants(soup),
        'prices': extract_product_prices(soup),
        'availability': extract_availability_tag(soup),
        'main_photo': extract_product_main_photo_link(soup),
        'photogallery': extract_product_photogallery_links(soup),
        'url': get_self_link(soup),
    }

def extract_products(product_detail_page_paths):
    products = []
    for path in product_detail_page_paths:
        products.append(extract_product(path))
    return products











