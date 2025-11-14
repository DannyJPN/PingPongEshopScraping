"""
HTTP download constants for retry logic and error handling.
"""

# Retry configuration
MAX_RETRY_ATTEMPTS = 100        # Maximum retry attempts
BASE_RETRY_DELAY = 0.01         # Base delay in seconds (multiplied by 1 + failure rate)

# HTTP status codes that should be retried
RETRY_STATUS_CODES = [
    # 4xx - Client errors that might be temporary
    403,  # Forbidden (possible rate limiting/IP ban)
    408,  # Request Timeout
    421,  # Misdirected Request
    423,  # Locked
    425,  # Too Early
    429,  # Too Many Requests (rate limiting)

    # 5xx - Server errors (usually temporary)
    500,  # Internal Server Error
    502,  # Bad Gateway
    503,  # Service Unavailable
    504,  # Gateway Timeout
]

# HTTP status codes that should be skipped without retry
SKIP_STATUS_CODES = [
    # 4xx - Client errors (permanent)
    400,  # Bad Request
    401,  # Unauthorized
    402,  # Payment Required
    405,  # Method Not Allowed
    406,  # Not Acceptable
    407,  # Proxy Authentication Required
    409,  # Conflict
    410,  # Gone (permanently deleted)
    411,  # Length Required
    412,  # Precondition Failed
    413,  # Payload Too Large
    414,  # URI Too Long
    415,  # Unsupported Media Type
    416,  # Range Not Satisfiable
    417,  # Expectation Failed
    418,  # I'm a teapot
    422,  # Unprocessable Entity
    424,  # Failed Dependency
    426,  # Upgrade Required
    428,  # Precondition Required
    431,  # Request Header Fields Too Large
    451,  # Unavailable For Legal Reasons

    # 5xx - Server errors (permanent)
    501,  # Not Implemented
    505,  # HTTP Version Not Supported
    506,  # Variant Also Negotiates
    507,  # Insufficient Storage
    508,  # Loop Detected
    510,  # Not Extended
    511,  # Network Authentication Required
]

# Default request timeout in seconds
DEFAULT_TIMEOUT = 30
