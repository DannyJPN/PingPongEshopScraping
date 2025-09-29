# html_loader.py
import os
import logging
from bs4 import BeautifulSoup

def load_html_as_dom_tree(filepath):
    """
    Loads a file from filepath as an HTML DOM tree.

    :param filepath: Path to the HTML file.
    :return: BeautifulSoup object containing the HTML DOM representation.
    """
    try:
        if not os.path.exists(filepath):
            logging.error(f"File does not exist: {filepath}")
            return None

        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()

        dom_tree = BeautifulSoup(content, 'lxml')
        return dom_tree

    except Exception as e:
        logging.error(f"Error loading HTML file {filepath}: {e}", exc_info=True)
        return None












