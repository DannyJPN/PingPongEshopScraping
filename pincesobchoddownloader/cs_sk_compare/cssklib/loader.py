"""Locating, downloading (--pullnewest) and loading Pincesobchod JSON exports."""
import json
import logging
import os
import sys
from datetime import datetime

from cssklib.constants import (
    FULL_FOLDER_PREFIX, FULL_FOLDER_DATE_FORMAT, SIDE_COUNTRY, SIDE_LANG,
)

DOWNLOADER_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def json_filename(lang_code):
    return f"Pincesobchod_{lang_code.upper()}.json"


def _folder_date(name):
    try:
        return datetime.strptime(name[len(FULL_FOLDER_PREFIX):], FULL_FOLDER_DATE_FORMAT)
    except ValueError:
        return None


def find_latest_json(base_dir, lang_code):
    """
    Newest Pincesobchod_<LANG>.json in <base_dir>/Full_<dd.mm.yyyy>/.

    Folders are ordered by the date in their name (modification time breaks ties
    and orders folders with an unparsable name).
    """
    if not os.path.isdir(base_dir):
        raise FileNotFoundError(f"Složka neexistuje: {base_dir}")
    candidates = []
    for name in os.listdir(base_dir):
        folder = os.path.join(base_dir, name)
        path = os.path.join(folder, json_filename(lang_code))
        if name.startswith(FULL_FOLDER_PREFIX) and os.path.isfile(path):
            date = _folder_date(name) or datetime.min
            candidates.append((date, os.stat(folder).st_mtime, path))
    if not candidates:
        raise FileNotFoundError(f"V {base_dir} není žádná složka Full_* s {json_filename(lang_code)}")
    return max(candidates)[2]


def _import_downloader():
    """Import the pincesobchod downloader modules (shared/, pincesobchodlib/)."""
    if DOWNLOADER_DIR not in sys.path:
        sys.path.insert(0, DOWNLOADER_DIR)
    from pincesobchodlib.constants import API_URL_PATTERN
    from shared.json_downloader import download_json_file
    from shared.utils import get_full_day_folder
    return API_URL_PATTERN, download_json_file, get_full_day_folder


def pull_newest_json(base_dir, side, downloader=None):
    """
    Download today's JSON using the pincesobchod downloader mechanism
    (API_URL_PATTERN + JZ_BEARER_TOKEN_<LANG>) into <base_dir>/Full_<today>/.
    """
    api_url_pattern, download_json_file, get_full_day_folder = downloader or _import_downloader()
    lang = SIDE_LANG[side]
    url = api_url_pattern.format(COUNTRY_CODE=SIDE_COUNTRY[side])
    path = os.path.join(get_full_day_folder(base_dir), json_filename(lang))
    logging.info(f"Stahuji nejnovější JSON {lang}: {url} -> {path}")
    download_json_file(url, path, lang, overwrite=True)
    return path


def load_products(path):
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    products = data.get("data", []) if isinstance(data, dict) else data
    if not isinstance(products, list):
        raise ValueError(f"Neočekávaný formát JSON: {path}")
    return products


def resolve_source(side, base_dir, explicit_json=None, pull_newest=False, downloader=None):
    """Return (json_path, products) for one side."""
    if explicit_json:
        path = explicit_json
    elif pull_newest:
        path = pull_newest_json(base_dir, side, downloader=downloader)
    else:
        path = find_latest_json(base_dir, SIDE_LANG[side])
    return path, load_products(path)
