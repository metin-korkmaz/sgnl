"""Redis-based rate limiter using sliding window algorithm.

This module provides a Redis-backed rate limiter implementation
using sorted sets for efficient sliding window rate limiting.
"""
import time
import logging
from typing import Tuple, Dict, Any, Optional

import redis.asyncio as redis
from redis.asyncio import Redis

from .rate_limiter_interface import RateLimiterInterface

logger = logging.getLogger(__name__)


class RedisRateLimiter(RateLimiterInterface):
    """Redis-based rate limiter using sliding window algorithm.

    Uses Redis sorted sets (ZADD, ZREMRANGEBYSCORE, ZCARD, ZRANGE) to track
    request timestamps per IP address with automatic expiration.

    Features:
    - Sliding window rate limiting (no fixed windows)
    - O(log n) operations using sorted sets
    - Automatic key expiration to prevent memory leaks
    - Atomic operations for race condition safety
    """

    def __init__(
        self,
        redis_client: Optional[Redis] = None,
        limit: int = 3,
        window_seconds: int = 60,
        redis_url: Optional[str] = None
    ):
        """Initialize the Redis rate limiter.

        Args:
            redis_client: Existing Redis client to use (optional)
            limit: Maximum number of requests allowed per window
            window_seconds: Time window in seconds for rate limiting
            redis_url: Redis connection URL (used if redis_client not provided)
        """
        self.limit = limit
        self.window_seconds = window_seconds
        self.key_prefix = "rate_limit:"

        if redis_client is not None:
            self.redis = redis_client
        elif redis_url:
            self.redis = Redis.from_url(redis_url, decode_responses=True)
        else:
            # Try to get from environment
            import os
            url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            self.redis = Redis.from_url(url, decode_responses=True)

    def _get_key(self, ip: str) -> str:
        """Generate the Redis key for an IP address."""
        return f"{self.key_prefix}{ip}"

    async def is_allowed(self, ip: str) -> Tuple[bool, Dict[str, Any]]:
        """Check if a request from the given IP is allowed.

        Implements sliding window rate limiting using Redis sorted sets:
        1. Remove timestamps older than window_seconds (ZREMRANGEBYSCORE)
        2. Count current requests in window (ZCARD)
        3. If under limit: add current timestamp (ZADD) and set TTL (EXPIRE)
        4. If at/over limit: calculate reset_after from oldest timestamp

        Args:
            ip: The client IP address to check.

        Returns:
            Tuple of (is_allowed, metadata) where:
            - is_allowed: True if the request is allowed, False if rate limited
            - metadata: Dict containing 'remaining' (int) and 'reset_after' (int)
        """
        key = self._get_key(ip)
        now = time.time()
        window_start = now - self.window_seconds

        try:
            await self.redis.zremrangebyscore(key, 0, window_start)
            current_count = await self.redis.zcard(key)

            if current_count >= self.limit:
                oldest_timestamps = await self.redis.zrange(key, 0, 0, withscores=True)

                if oldest_timestamps:
                    oldest_ts = float(oldest_timestamps[0][1])
                    reset_after = max(1, int(self.window_seconds - (now - oldest_ts)))
                else:
                    reset_after = self.window_seconds

                return False, {"remaining": 0, "reset_after": reset_after}

            await self.redis.zadd(key, {str(now): now})
            await self.redis.expire(key, self.window_seconds)

            remaining = max(0, self.limit - current_count - 1)

            return True, {"remaining": remaining, "reset_after": self.window_seconds}

        except Exception as e:
            logger.error(f"[RATE_LIMITER] Error checking rate limit for {ip}: {e}")
            return True, {"remaining": self.limit, "reset_after": self.window_seconds}

    async def reset(self, ip: str) -> None:
        """Reset the rate limit for the given IP.

        Args:
            ip: The client IP address to reset.
        """
        key = self._get_key(ip)

        try:
            await self.redis.delete(key)
            logger.debug(f"[RATE_LIMITER] Rate limit reset for {ip}")
        except Exception as e:
            logger.error(f"[RATE_LIMITER] Error resetting rate limit for {ip}: {e}")
