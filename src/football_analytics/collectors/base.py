"""Base collector class with common patterns.

Provides shared functionality for all data collectors:
- API client initialization
- Rate limiting
- Resume capability
- Logging setup
- File operations

All concrete collectors should inherit from BaseCollector.
"""

import logging
from pathlib import Path
from typing import Optional

from football_analytics.api_client import SportsMonkClient
from football_analytics.utils import RateLimiter, file_exists


class BaseCollector:
    """
    Base class for all data collectors.

    Provides common patterns:
    - API client management
    - Rate limiting
    - Resume capability (skip existing files)
    - Logging
    - Output directory management

    Args:
        output_dir: Directory where collected data will be saved
        rate_limit_seconds: Minimum seconds between API requests
        resume: If True, skip files that already exist
        api_key: Optional API key override (uses env var if not provided)

    Example:
        >>> class MyCollector(BaseCollector):
        ...     def collect(self):
        ...         self.rate_limiter.wait()
        ...         data = self.client.get_leagues()
        ...         return data
    """

    def __init__(
        self,
        output_dir: str = "data/raw",
        rate_limit_seconds: float = 6.0,
        resume: bool = True,
        api_key: Optional[str] = None,
    ):
        """Initialize base collector."""
        # API client
        self.client = SportsMonkClient(api_key=api_key)

        # Output directory
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Rate limiting
        self.rate_limiter = RateLimiter(delay=rate_limit_seconds)

        # Resume capability
        self.resume = resume

        # Logging
        self.logger = logging.getLogger(self.__class__.__name__)

        # Statistics
        self.stats = {"api_calls": 0, "files_created": 0, "files_skipped": 0, "errors": 0}

    def should_skip(self, filepath: Path) -> bool:
        """
        Check if file should be skipped (already exists and resume enabled).

        Args:
            filepath: Path to check

        Returns:
            True if file should be skipped, False otherwise

        Example:
            >>> collector = BaseCollector()
            >>> if collector.should_skip(Path("data/existing.json")):
            ...     print("Skipping")
        """
        if self.resume and file_exists(filepath):
            self.logger.debug(f"Skipping (already exists): {filepath}")
            self.stats["files_skipped"] += 1
            return True
        return False

    def increment_api_calls(self) -> None:
        """Track API call statistics."""
        self.stats["api_calls"] += 1

    def increment_files_created(self) -> None:
        """Track file creation statistics."""
        self.stats["files_created"] += 1

    def increment_errors(self) -> None:
        """Track error statistics."""
        self.stats["errors"] += 1

    def get_stats(self) -> dict:
        """
        Get collection statistics.

        Returns:
            Dictionary with collection stats

        Example:
            >>> collector = BaseCollector()
            >>> # ... collect data ...
            >>> stats = collector.get_stats()
            >>> print(f"Made {stats['api_calls']} API calls")
        """
        return self.stats.copy()

    def reset_stats(self) -> None:
        """Reset collection statistics."""
        self.stats = {"api_calls": 0, "files_created": 0, "files_skipped": 0, "errors": 0}
        self.logger.debug("Statistics reset")
