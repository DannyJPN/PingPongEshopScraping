import os

# Get the script's directory
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Default values for command line arguments
DEFAULT_LANGUAGE = "CS"
DEFAULT_RESULT_DIR = "H:/Desaka"
DEFAULT_MEMORY_DIR = os.path.join(SCRIPT_DIR, "Memory")
DEFAULT_EXPORT_DIR = "H:/Desaka/Results"
DEFAULT_CONFIRM_AI_RESULTS = True

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

# File names
GEWO_PRICE_LIST = "GewoPriceList.xlsx"
ESHOP_LIST = "EshopList.csv"
BRAND_CODE_LIST = "BrandCodeList.csv"
CATEGORY_CODE_LIST = "CategoryCodeList.csv"
CATEGORY_SUB_CODE_LIST = "CategorySubCodeList.csv"
CATEGORY_LIST = "CategoryList.txt"
CATEGORY_ID_LIST = "CategoryIDList.csv"
DEFAULT_UNIFIED_PRODUCT_VALUES = "DefaultUnifiedProductValues.csv"
SUPPORTED_LANGUAGES_LIST = "SupportedLanguagesList.txt"
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

# Log directory
LOG_DIR = r"H:/Logs"
# Script execution settings
SCRIPT_EXECUTION_TIMEOUT = 300  # 5 minutes timeout for script execution
PROGRESS_BAR_UPDATE_INTERVAL = 0.1  # Update progress bar every 0.1 seconds

