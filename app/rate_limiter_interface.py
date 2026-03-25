"""Rate limiter interface and implementations for decoupled storage.

This module provides an abstract base class for rate limiting storage
and an in-memory implementation using dict storage.
"""

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Tuple, Dict, Any
import time


class RateLimiterInterface(ABC):
    """Abstract base class for rate limiter storage implementations.

    Implementations must provide async-compatible methods for checking
    rate limits and resetting state.
    """

    @abstractmethod
    async def is_allowed(self, ip: str) -> Tuple[bool, Dict[str, Any]]:
        """Check if a request from the given IP is allowed.

        Args:
            ip: The client IP address to check.

        Returns:
            Tuple of (is_allowed, metadata) where:
            - is_allowed: True if the request is allowed, False if rate limited
            - metadata: Dict containing 'remaining' (int) and 'reset_after' (int)
        """
        pass

    @abstractmethod
    async def reset(self, ip: str) -> None:
        """Reset the rate limit for the given IP.

        Args:
            ip: The client IP address to reset.
        """
        pass


class InMemoryRateLimiter(RateLimiterInterface):
    """In-memory rate limiter using dict storage.

    Tracks request timestamps per IP address and enforces rate limits
    based on a configurable time window.
    """

    def __init__(self, limit: int = 3, window_seconds: int = 60):
        """Initialize the in-memory rate limiter.

        Args:
            limit: Maximum number of requests allowed per window.
            window_seconds: Time window in seconds for rate limiting.
        """
        self.limit = limit
        self.window_seconds = window_seconds
        self._request_counts: Dict[str, list] = defaultdict(list)

    def _clean_old_requests(self, ip: str) -> None:
        """Remove timestamps older than the window for a specific IP."""
        now = time.time()
        self._request_counts[ip] = [
            ts for ts in self._request_counts[ip]
            if now - ts < self.window_seconds
        ]

    async def is_allowed(self, ip: str) -> Tuple[bool, Dict[str, Any]]:
        """Check if a request from the given IP is allowed.

        Args:
            ip: The client IP address to check.

        Returns:
            Tuple of (is_allowed, metadata) where:
            - is_allowed: True if the request is allowed, False if rate limited
            - metadata: Dict containing 'remaining' (int) and 'reset_after' (int)
        """
        self._clean_old_requests(ip)

        current_count = len(self._request_counts[ip])
        remaining = max(0, self.limit - current_count)

        if current_count >= self.limit:
            oldest_request = min(self._request_counts[ip])
            reset_after = int(self.window_seconds - (time.time() - oldest_request))

            return False, {"remaining": 0, "reset_after": reset_after}

        self._request_counts[ip].append(time.time())
        remaining = max(0, self.limit - len(self._request_counts[ip]))

        return True, {"remaining": remaining, "reset_after": self.window_seconds}

    async def reset(self, ip: str) -> None:
        """Reset the rate limit for the given IP.

        Args:
            ip: The client IP address to reset.
        """
        if ip in self._request_counts:
            del self._request_counts[ip]
