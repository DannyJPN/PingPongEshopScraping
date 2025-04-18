from bs4 import BeautifulSoup
from urllib.parse import urljoin

from shared.html_loader import load_html_as_dom_tree
def extract_category_links(main_page_html):
    soup = load_html_as_dom_tree(main_page_html)
    links = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if any(keyword in href.lower() for keyword in ['rubber', 'blade', 'shoe', 'accessory', 'bat']):
            links.add(urljoin("https://example.com", href))
    return links











