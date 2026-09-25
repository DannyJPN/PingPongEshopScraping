"""
Core HTTP download functionality with adaptive retry logic.
Handles all HTTP requests with automatic retry on transient errors.
"""

import logging
import time
import requests
from typing import Optional

from .download_constants import (
    MAX_RETRY_ATTEMPTS,
    BASE_RETRY_DELAY,
    RETRY_STATUS_CODES,
    SKIP_STATUS_CODES,
    DEFAULT_TIMEOUT
)
from .download_stats import DownloadStats


def download_with_retry(
    url: str,
    stats: Optional[DownloadStats] = None,
    headers: Optional[dict] = None,
    timeout: int = DEFAULT_TIMEOUT
) -> Optional[requests.Response]:
    """
    Download URL with adaptive retry logic.

    Args:
        url: URL to download
        stats: DownloadStats instance for tracking (if None, creates temporary instance)
        headers: Optional HTTP headers
        timeout: Request timeout in seconds

    Returns:
        Response object if successful, None if failed
    """
    # Create temporary stats if not provided (for backward compatibility)
    if stats is None:
        stats = DownloadStats()

    for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
        try:
            # Make request
            response = requests.get(url, headers=headers, timeout=timeout)

            # Check for HTTP errors
            if response.status_code == 404:
                # 404 is special - log as DEBUG and skip
                logging.debug(f"404 Not Found for URL: {url}")
                stats.record_success(url)  # Count as "handled" not failed
                return None

            elif response.status_code in SKIP_STATUS_CODES:
                # Permanent error - log and skip
                logging.error(
                    f"HTTP {response.status_code} error for URL: {url} - "
                    f"Response: {response.text[:200]}"
                )
                stats.record_success(url)  # Count as "handled" not failed
                return None

            elif response.status_code in RETRY_STATUS_CODES:
                # Temporary error - retry
                if attempt < MAX_RETRY_ATTEMPTS:
                    # Calculate adaptive delay
                    failure_rate = stats.get_failure_rate(url)
                    delay = BASE_RETRY_DELAY * (1 + failure_rate)

                    logging.warning(
                        f"HTTP {response.status_code} error for URL: {url} - "
                        f"Attempt {attempt}/{MAX_RETRY_ATTEMPTS} - "
                        f"Response: {response.text[:100]} - "
                        f"Retrying in {delay:.3f}s..."
                    )

                    stats.record_failure(url)
                    time.sleep(delay)
                    continue
                else:
                    # Max retries exceeded
                    logging.error(
                        f"HTTP {response.status_code} error for URL: {url} - "
                        f"Max retries ({MAX_RETRY_ATTEMPTS}) exceeded - "
                        f"Response: {response.text[:200]}"
                    )
                    stats.record_failure(url)
                    return None

            elif response.status_code >= 400:
                # Unknown error code - treat as skip
                logging.error(
                    f"HTTP {response.status_code} error (unknown) for URL: {url} - "
                    f"Response: {response.text[:200]}"
                )
                stats.record_success(url)
                return None

            # Success (2xx, 3xx)
            stats.record_success(url)
            return response

        except requests.exceptions.Timeout:
            if attempt < MAX_RETRY_ATTEMPTS:
                failure_rate = stats.get_failure_rate(url)
                delay = BASE_RETRY_DELAY * (1 + failure_rate)

                logging.warning(
                    f"Timeout for URL: {url} - "
                    f"Attempt {attempt}/{MAX_RETRY_ATTEMPTS} - "
                    f"Retrying in {delay:.3f}s..."
                )

                stats.record_failure(url)
                time.sleep(delay)
                continue
            else:
                logging.error(
                    f"Timeout for URL: {url} - "
                    f"Max retries ({MAX_RETRY_ATTEMPTS}) exceeded"
                )
                stats.record_failure(url)
                return None

        except requests.exceptions.ConnectionError as e:
            if attempt < MAX_RETRY_ATTEMPTS:
                failure_rate = stats.get_failure_rate(url)
                delay = BASE_RETRY_DELAY * (1 + failure_rate)

                logging.warning(
                    f"Connection error for URL: {url} - "
                    f"Attempt {attempt}/{MAX_RETRY_ATTEMPTS} - "
                    f"Error: {e} - "
                    f"Retrying in {delay:.3f}s..."
                )

                stats.record_failure(url)
                time.sleep(delay)
                continue
            else:
                logging.error(
                    f"Connection error for URL: {url} - "
                    f"Max retries ({MAX_RETRY_ATTEMPTS}) exceeded - "
                    f"Error: {e}"
                )
                stats.record_failure(url)
                return None

        except Exception as e:
            # Unexpected error
            logging.error(
                f"Unexpected error downloading {url}: {e}",
                exc_info=True
            )
            stats.record_success(url)  # Don't count unexpected errors in failure rate
            return None

    return None
