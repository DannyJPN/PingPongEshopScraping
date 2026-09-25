import json
import os
import unicodedata


def load_latest_json(base_dir, lang_code):
    folders = [
        os.path.join(base_dir, d)
        for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d)) and d.startswith('Full_')
    ]
    if not folders:
        raise FileNotFoundError(f"No Full_* folders in {base_dir}")
    latest = max(folders, key=lambda p: os.stat(p).st_mtime)
    json_path = os.path.join(latest, f"Pincesobchod_{lang_code}.json")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('data', []), latest, json_path


def match_by_catalog_number(cs_products, sk_products):
    cs_map = {p['catalogNumber']: p for p in cs_products if p.get('catalogNumber')}
    sk_map = {p['catalogNumber']: p for p in sk_products if p.get('catalogNumber')}
    shared_keys = sorted(set(cs_map) & set(sk_map))
    cs_only_keys = sorted(set(cs_map) - set(sk_map))
    sk_only_keys = sorted(set(sk_map) - set(cs_map))
    return (
        [cs_map[k] for k in shared_keys],
        [sk_map[k] for k in shared_keys],
        [cs_map[k] for k in cs_only_keys],
        [sk_map[k] for k in sk_only_keys],
    )


def get_name(product):
    return (product.get('translations') or {}).get('cs', {}).get('name') or ''


def normalize_name(name):
    name = name.lower().strip()
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    return ' '.join(name.split())


def normalize_image_url(url):
    if not url:
        return ''
    for domain in [
        'https://www.pincesobchod.cz', 'https://www.pincesobchod.sk',
        'http://www.pincesobchod.cz',  'http://www.pincesobchod.sk',
    ]:
        if url.startswith(domain):
            return url[len(domain):]
    return url


def is_active(product):
    return bool(product.get('visibility')) and not bool(product.get('archive'))