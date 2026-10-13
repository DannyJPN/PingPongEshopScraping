"""
Category mappings of the project (desaka_unifier/Memory/CategoryMapping<Platform>_<LANG>.csv).

KEY   = e-shop category path, e.g. "Potahy>Softy>Softy OFF"
VALUE = category of the comparison platform (Glami, Google, Heureka, Zboží)
"""
import csv
import os

from cssklib.loader import DOWNLOADER_DIR
from cssklib.values import normalize_text

DEFAULT_MEMORY_DIR = os.path.join(os.path.dirname(DOWNLOADER_DIR), "desaka_unifier", "Memory")

# feed key in the Pincesobchod JSON -> platform name used in the mapping file name
FEED_PLATFORMS = {"glami": "Glami", "google": "Google", "heurekacs": "Heureka", "zbozi": "Zbozi"}
MAPPING_FILE_PATTERN = "CategoryMapping{platform}_{lang}.csv"
FALLBACK_LANG = "CS"


def _read_mapping(path):
    if not os.path.isfile(path):
        return {}
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "KEY" not in reader.fieldnames:
            return {}
        return {normalize_text(row["KEY"]): normalize_text(row.get("VALUE"))
                for row in reader if normalize_text(row.get("KEY"))}


def load_mapping(memory_dir, platform, lang):
    """
    Return (mapping, file_name). Falls back to the CS file when the language file is missing
    or empty (the SK mapping files of the project are currently empty; the SK shop uses the same
    Czech category names).
    """
    name = MAPPING_FILE_PATTERN.format(platform=platform, lang=lang.upper())
    mapping = _read_mapping(os.path.join(memory_dir, name))
    if not mapping and lang.upper() != FALLBACK_LANG:
        fallback = MAPPING_FILE_PATTERN.format(platform=platform, lang=FALLBACK_LANG)
        mapping = _read_mapping(os.path.join(memory_dir, fallback))
        if mapping:
            return mapping, f"{fallback} (záloha, {name} je prázdný)"
    return mapping, name


class CategoryMappings:
    """Lazy cache of mappings per (platform, language)."""

    def __init__(self, memory_dir=DEFAULT_MEMORY_DIR):
        self.memory_dir = memory_dir
        self._cache = {}

    def get(self, platform, lang):
        key = (platform, lang.upper())
        if key not in self._cache:
            self._cache[key] = load_mapping(self.memory_dir, platform, lang)
        return self._cache[key]
