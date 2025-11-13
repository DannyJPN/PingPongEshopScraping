import os

# Get the script's directory
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Default values for command line arguments
DEFAULT_LANGUAGE = "CS"
DEFAULT_RESULT_DIR = "H:/Desaka"
DEFAULT_MEMORY_DIR = os.path.join(SCRIPT_DIR, "Memory")
DEFAULT_EXPORT_DIR = "H:/Desaka/Results"
DEFAULT_LOG_DIR = r"H:/Logs"
DEFAULT_CONFIRM_AI_RESULTS = False
DEFAULT_ENABLE_FINE_TUNING = False
DEFAULT_USE_FINE_TUNED_MODELS = False
DEFAULT_MAX_TOKENS = 4000

# Memory checker constants
MAX_ITERATIONS = 10  # Maximální počet iterací pro řešení překrývajících se hodnot

# Fine-tuning constants
FINE_TUNED_MODELS_FILE = "fine_tuned_models.json"

# Memory file prefixes
NAME_MEMORY_PREFIX = "NameMemory"
DESC_MEMORY_PREFIX = "DescMemory"
SHORT_DESC_MEMORY_PREFIX = "ShortDescMemory"
VARIANT_NAME_MEMORY_PREFIX = "VariantNameMemory"
VARIANT_VALUE_MEMORY_PREFIX = "VariantValueMemory"
PRODUCT_MODEL_MEMORY_PREFIX = "ProductModelMemory"
PRODUCT_BRAND_MEMORY_PREFIX = "ProductBrandMemory"
PRODUCT_TYPE_MEMORY_PREFIX = "ProductTypeMemory"
CATEGORY_MEMORY_PREFIX = "CategoryMemory"
CATEGORY_NAME_MEMORY_PREFIX = "CategoryNameMemory"
STOCK_STATUS_MEMORY_PREFIX = "StockStatusMemory"

# File names
GEWO_PRICE_LIST = "GewoPriceList.xlsx"
ESHOP_LIST = "EshopList.csv"
BRAND_CODE_LIST = "BrandCodeList.csv"
CATEGORY_CODE_LIST = "CategoryCodeList.csv"
CATEGORY_SUB_CODE_LIST = "CategorySubCodeList.csv"
CATEGORY_LIST = "CategoryList.txt"
CATEGORY_ID_LIST = "CategoryIDList.csv"
DEFAULT_EXPORT_PRODUCT_VALUES = "DefaultExportProductValues.csv"
SUPPORTED_LANGUAGES_FILE = "SupportedLanguages.csv"
ITEM_FILTER = "ItemFilter.csv"

# Category mapping files
CATEGORY_MAPPING_HEUREKA_PREFIX = "CategoryMappingHeureka"
CATEGORY_MAPPING_ZBOZI_PREFIX = "CategoryMappingZbozi"
CATEGORY_MAPPING_GLAMI_PREFIX = "CategoryMappingGlami"
CATEGORY_MAPPING_GOOGLE_PREFIX = "CategoryMappingGoogle"

# Keywords files
KEYWORDS_GOOGLE_PREFIX = "KeywordsGoogle"
KEYWORDS_ZBOZI_PREFIX = "KeywordsZbozi"

# Other constants
WRONGS_FILE = "Wrongs.txt"

# Export and report directories
RESULTS_SUBDIR = "Výsledky"
REPORTS_SUBDIR_PREFIX = "Reporty"
DETAIL_REPORTS_SUBDIR = "Detail_reporty"

# Memory file keys (language-independent)
MEMORY_KEY_BRAND_CODE_LIST = "BrandCodeList"
MEMORY_KEY_CATEGORY_CODE_LIST = "CategoryCodeList"
MEMORY_KEY_CATEGORY_ID_LIST = "CategoryIDList"
MEMORY_KEY_CATEGORY_LIST = "CategoryList"
MEMORY_KEY_CATEGORY_SUB_CODE_LIST = "CategorySubCodeList"
MEMORY_KEY_DEFAULT_EXPORT_PRODUCT_VALUES = "DefaultExportProductValues"
MEMORY_KEY_ESHOP_LIST = "EshopList"
MEMORY_KEY_ITEM_FILTER = "ItemFilter"
MEMORY_KEY_WRONGS = "Wrongs"

# Memory file key templates (language-dependent)
MEMORY_KEY_CATEGORY_MAPPING_GLAMI = "CategoryMappingGlami_{language}"
MEMORY_KEY_CATEGORY_MAPPING_GOOGLE = "CategoryMappingGoogle_{language}"
MEMORY_KEY_CATEGORY_MAPPING_HEUREKA = "CategoryMappingHeureka_{language}"
MEMORY_KEY_CATEGORY_MAPPING_ZBOZI = "CategoryMappingZbozi_{language}"
MEMORY_KEY_CATEGORY_MEMORY = "CategoryMemory_{language}"
MEMORY_KEY_CATEGORY_NAME_MEMORY = "CategoryNameMemory_{language}"
MEMORY_KEY_DESC_MEMORY = "DescMemory_{language}"
MEMORY_KEY_KEYWORDS_GOOGLE = "KeywordsGoogle_{language}"
MEMORY_KEY_KEYWORDS_ZBOZI = "KeywordsZbozi_{language}"
MEMORY_KEY_NAME_MEMORY = "NameMemory_{language}"
MEMORY_KEY_PRODUCT_BRAND_MEMORY = "ProductBrandMemory_{language}"
MEMORY_KEY_PRODUCT_MODEL_MEMORY = "ProductModelMemory_{language}"
MEMORY_KEY_PRODUCT_TYPE_MEMORY = "ProductTypeMemory_{language}"
MEMORY_KEY_SHORT_DESC_MEMORY = "ShortDescMemory_{language}"
MEMORY_KEY_VARIANT_NAME_MEMORY = "VariantNameMemory_{language}"
MEMORY_KEY_VARIANT_VALUE_MEMORY = "VariantValueMemory_{language}"
MEMORY_KEY_STOCK_STATUS_MEMORY = "StockStatusMemory_{language}"

# Log directory (deprecated - use DEFAULT_LOG_DIR)
LOG_DIR = DEFAULT_LOG_DIR
# Script execution settings
PROGRESS_BAR_UPDATE_INTERVAL = 0.1  # Update progress bar every 0.1 seconds
