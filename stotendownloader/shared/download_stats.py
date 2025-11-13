"""
Download statistics tracker for adaptive retry delays.
Tracks success/failure rates per domain.
"""

import logging
from urllib.parse import urlparse
from threading import Lock
from typing import Dict, Tuple


class DownloadStats:
    """
    Tracks download statistics per domain for adaptive retry logic.
    Thread-safe implementation.
    """

    def __init__(self):
        """Initialize statistics tracker."""
        self._stats: Dict[str, Dict[str, int]] = {}
        self._lock = Lock()

    def _get_domain(self, url: str) -> str:
        """
        Extract domain from URL.

        Args:
            url: Full URL

        Returns:
            Domain name (e.g., 'example.com')
        """
        parsed = urlparse(url)
        return parsed.netloc.lower()

    def record_success(self, url: str) -> None:
        """
        Record successful request.

        Args:
            url: URL that was successfully downloaded
        """
        domain = self._get_domain(url)

        with self._lock:
            if domain not in self._stats:
                self._stats[domain] = {'total': 0, 'failed': 0}

            self._stats[domain]['total'] += 1

    def record_failure(self, url: str) -> None:
        """
        Record failed request (that needed retry).

        Args:
            url: URL that failed and needed retry
        """
        domain = self._get_domain(url)

        with self._lock:
            if domain not in self._stats:
                self._stats[domain] = {'total': 0, 'failed': 0}

            self._stats[domain]['total'] += 1
            self._stats[domain]['failed'] += 1

    def get_failure_rate(self, url: str) -> float:
        """
        Get failure rate for domain as decimal (0.0 - 1.0).

        Args:
            url: URL to check domain for

        Returns:
            Failure rate (0.0 if no requests yet)

        Example:
            2 failed out of 16 total = 0.125
        """
        domain = self._get_domain(url)

        with self._lock:
            if domain not in self._stats:
                return 0.0

            stats = self._stats[domain]
            total = stats['total']

            if total == 0:
                return 0.0

            return stats['failed'] / total

    def get_stats(self, url: str) -> Tuple[int, int]:
        """
        Get statistics for domain.

        Args:
            url: URL to check domain for

        Returns:
            Tuple of (total_requests, failed_requests)
        """
        domain = self._get_domain(url)

        with self._lock:
            if domain not in self._stats:
                return (0, 0)

            stats = self._stats[domain]
            return (stats['total'], stats['failed'])

    def get_all_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Get all statistics for all domains.

        Returns:
            Dictionary mapping domain to stats dict
        """
        with self._lock:
            return dict(self._stats)

    def log_summary(self) -> None:
        """Log summary of all domain statistics."""
        with self._lock:
            if not self._stats:
                logging.info("No download statistics recorded")
                return

            logging.info("=== Download Statistics Summary ===")
            for domain, stats in sorted(self._stats.items()):
                total = stats['total']
                failed = stats['failed']
                rate = (failed / total * 100) if total > 0 else 0

                logging.info(
                    f"  {domain}: {total} requests, {failed} failed ({rate:.1f}%)"
                )
