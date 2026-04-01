"""Constants for batch memory checker."""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BASE_DIR)

DEFAULT_LANGUAGE = "CS"
DEFAULT_MEMORY_DIR = os.path.join(ROOT_DIR, "desaka_unifier", "Memory")
DEFAULT_RESULTS_DIR = "H:/Desaka"
DEFAULT_LOG_DIR = "H:/Logs"

DEFAULT_BATCH_MAX_RECORDS = 5000
DEFAULT_BATCH_MAX_MB = 100
DEFAULT_BATCH_POLL_INTERVAL = 600
DEFAULT_MAX_POLL_ITERATIONS = 1000
DEFAULT_BATCH_WAIT_TIMEOUT = 0
DEFAULT_REGISTRY_WRITE_EVERY = 200
DEFAULT_STATE_WRITE_EVERY = 200

BATCH_STATE_DIR = os.path.join(BASE_DIR, "batch_state")
BATCH_REGISTRY_FILE = os.path.join(BATCH_STATE_DIR, "batch_registry.json")
BATCH_LOCK_FILE = os.path.join(BATCH_STATE_DIR, "batch.lock")
BATCH_COST_LOG = os.path.join(BATCH_STATE_DIR, "cost_log.json")
REPORTS_DIR = os.path.join(BATCH_STATE_DIR, "reports")

STATUS_COLLECTING = "collecting"
STATUS_READY = "ready"
STATUS_SENT = "sent"
STATUS_COMPLETED = "completed"
STATUS_ERROR = "error"

MEMORY_SUFFIX = "_CS.csv"

VARIANT_NAME_PREFIX = "VariantNameMemory"
VARIANT_VALUE_PREFIX = "VariantValueMemory"

RESULT_DATE_PREFIX = "Full_"
RESULT_DATE_FORMAT = "%d.%m.%Y"

DEFAULT_MODEL_KEY = "openai/gpt-5-mini"

OUTPUT_JSON_FIELDS = [
    "is_correct",
    "correct_value",
    "reason",
    "source"
]
