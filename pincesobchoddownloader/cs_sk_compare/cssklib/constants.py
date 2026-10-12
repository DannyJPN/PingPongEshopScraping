"""Constants for the Pincesobchod CS vs SK comparison scripts."""

# Default folders (same layout as pincesobchod_downloader: <result_dir>_<LANG>/Full_<dd.mm.yyyy>/)
DEFAULT_CS_DIR = "H:/Desaka/Pincesobchod_CS"
DEFAULT_SK_DIR = "H:/Desaka/Pincesobchod_SK"
DEFAULT_REPORT_DIR = "H:/Desaka/Reports/Pincesobchod/CsSk"
DEFAULT_IMAGE_CACHE_DIR = "H:/Desaka/Pincesobchod_ImageCache"

FULL_FOLDER_PREFIX = "Full_"
FULL_FOLDER_DATE_FORMAT = "%d.%m.%Y"

# Side definitions: side id -> country code used by the downloader / language code of the JSON file
SIDES = ("cs", "sk")
SIDE_COUNTRY = {"cs": "cz", "sk": "sk"}
SIDE_LANG = {"cs": "CS", "sk": "SK"}
SIDE_LABEL = {"cs": "CZ", "sk": "SK"}

# Prices
VAT_RATES = {"cs": 21.0, "sk": 23.0}
CZK_PER_EUR = 25.0
PRICE_TOLERANCE = 0.1

# CZ -> SK price conversion rules: brand -> (root categories or None for all, discount)
# Root category names are compared without diacritics and case-insensitively.
BRAND_PRICE_RULES = {
    "butterfly": (None, 0.05),
    "andro": (("potahy", "dreva"), 0.05),
    "stiga": (("potahy",), 0.05),
    "tibhar": (None, 0.05),
    "victas": (("potahy", "dreva"), 0.10),
}

# Shop domains stripped from URLs so CZ and SK paths are comparable
SHOP_DOMAINS = (
    "https://www.pincesobchod.cz", "https://www.pincesobchod.sk",
    "http://www.pincesobchod.cz", "http://www.pincesobchod.sk",
    "https://pincesobchod.cz", "https://pincesobchod.sk",
)

# Report
REPORT_SCHEMA = "pincesobchod-cs-sk-report/1"
SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"
SEVERITY_INFO = "info"

# OpenAI vision
DEFAULT_VISION_MODEL = "gpt-4o"
VISION_MODEL_ENV = "PINCESOBCHOD_VISION_MODEL"
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
