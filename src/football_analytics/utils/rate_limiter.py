"""Rate limiting utilities for API requests.

Simple rate limiter to avoid overwhelming the SportsMonk API.

TODO (Framework Evolution):
    - Token bucket algorithm for burst handling
    - Adaptive rate limiting based on API response headers
    - Retry logic with exponential backoff
    - Rate limit per endpoint (different limits for different endpoints)
"""

import logging
import time
from typing import Optional


class RateLimiter:
    """
    Simple rate limiter with fixed delay between requests.

    Ensures minimum time between consecutive API calls to respect
    rate limits and avoid 429 (Too Many Requests) errors.

    Example:
        >>> limiter = RateLimiter(delay=2.0)
        >>> limiter.wait()  # Waits if needed
        >>> # Make API call
        >>> limiter.wait()  # Waits again before next call
    """

    def __init__(self, delay: float = 6.0):
        """
        Initialize rate limiter.

        Args:
            delay: Minimum seconds between requests (default: 6.0)
        """
        self.delay = delay
        self.last_request_time: Optional[float] = None
        self.logger = logging.getLogger(__name__)
        self.request_count = 0

    def wait(self) -> float:
        """
        Wait if necessary to maintain rate limit.

        Returns:
            Actual time waited in seconds

        Example:
            >>> limiter = RateLimiter(delay=2.0)
            >>> time.sleep(1.5)
            >>> wait_time = limiter.wait()
            >>> wait_time >= 0.5  # Waited at least 0.5s more
            True
        """
        if self.last_request_time is None:
            # First request, no need to wait
            self.last_request_time = time.time()
            self.request_count += 1
            return 0.0

        elapsed = time.time() - self.last_request_time

        if elapsed < self.delay:
            sleep_time = self.delay - elapsed
            self.logger.debug(
                f"Rate limiting: waiting {sleep_time:.2f}s " f"(request #{self.request_count + 1})"
            )
            time.sleep(sleep_time)
            self.last_request_time = time.time()
            self.request_count += 1
            return sleep_time

        # Enough time has passed, no wait needed
        self.last_request_time = time.time()
        self.request_count += 1
        return 0.0

    def reset(self) -> None:
        """
        Reset the rate limiter.

        Useful when starting a new batch of requests or after an error.

        Example:
            >>> limiter = RateLimiter()
            >>> limiter.wait()
            >>> limiter.reset()
            >>> limiter.request_count
            0
        """
        self.last_request_time = None
        self.request_count = 0
        self.logger.debug("Rate limiter reset")

    def get_stats(self) -> dict:
        """
        Get rate limiter statistics.

        Returns:
            Dictionary with request_count, delay, and last_request_time

        Example:
            >>> limiter = RateLimiter(delay=2.0)
            >>> limiter.wait()
            >>> stats = limiter.get_stats()
            >>> stats['request_count']
            1
        """
        return {
            "request_count": self.request_count,
            "delay": self.delay,
            "last_request_time": self.last_request_time,
        }
