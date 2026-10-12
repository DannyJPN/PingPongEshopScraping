"""Image download cache and hashing (uses the pincesobchod downloader HTTP mechanism)."""
import hashlib
import logging
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit

from cssklib.loader import DOWNLOADER_DIR


def default_fetch(url):
    """Download bytes with the downloader's retry logic (shared.http_downloader)."""
    if DOWNLOADER_DIR not in sys.path:
        sys.path.insert(0, DOWNLOADER_DIR)
    from shared.http_downloader import download_with_retry
    response = download_with_retry(url)
    return None if response is None else response.content


def sorted_images(product):
    return sorted(product.get("images") or [], key=lambda i: (i.get("position") or 0, i.get("id") or 0))


class ImageStore:
    """Downloads images into a cache folder (one file per URL) and computes SHA-256 hashes."""

    def __init__(self, cache_dir, fetch=None, workers=8):
        self.cache_dir = cache_dir
        self.fetch = fetch or default_fetch
        self.workers = max(1, workers)
        self._hashes = {}
        self._lock = threading.Lock()

    def cache_path(self, url):
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
        ext = os.path.splitext(urlsplit(url).path)[1].lower()
        if not ext or len(ext) > 5:
            ext = ".img"
        host = urlsplit(url).hostname or "unknown"
        return os.path.join(self.cache_dir, host, digest[:2], digest + ext)

    def get_bytes(self, url):
        """Image content (from cache or downloaded); None when it cannot be downloaded."""
        path = self.cache_path(url)
        if os.path.isfile(path):
            with open(path, "rb") as handle:
                return handle.read()
        try:
            content = self.fetch(url)
        except Exception as exc:  # network errors are reported as missing hash
            logging.warning(f"Stažení obrázku selhalo: {url}: {exc}")
            content = None
        if content is None:
            return None
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = f"{path}.part{threading.get_ident()}"
        with open(tmp, "wb") as handle:
            handle.write(content)
        os.replace(tmp, path)
        return content

    def get_hash(self, url):
        with self._lock:
            if url in self._hashes:
                return self._hashes[url]
        content = self.get_bytes(url)
        digest = hashlib.sha256(content).hexdigest() if content is not None else None
        with self._lock:
            self._hashes[url] = digest
        return digest

    def hash_many(self, urls, progress=None):
        """Hash all URLs in parallel; returns {url: sha256 or None}."""
        unique = sorted({u for u in urls if u})
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            for url, _ in zip(unique, pool.map(self.get_hash, unique)):
                if progress:
                    progress(url)
        return {url: self._hashes.get(url) for url in unique}
