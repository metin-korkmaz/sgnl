"""Cache module for SGNL backend.

Provides hybrid caching with Redis primary and in-memory fallback.
"""

import time
import threading
import hashlib
import logging
import asyncio
import os
from typing import Any, Optional
from collections import OrderedDict

from config import config
from .redis_cache import RedisCache

logger = logging.getLogger(__name__)


class CacheEntry:
    def __init__(self, value: Any, ttl_seconds: int):
        self.value = value
        self.expiry = time.time() + ttl_seconds

    def is_expired(self) -> bool:
        return time.time() > self.expiry


class TTLCache:
    """
    Thread-safe LRU cache with TTL support.

    Features:
    - Thread-safe operations (Lock-based)
    - TTL (Time-To-Live) per entry
    - Automatic cleanup of expired entries
    - LRU eviction when full
    - O(1) operations
    """

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = threading.RLock()
        self.last_cleanup = time.time()
        self.CLEANUP_INTERVAL = 300

    def _generate_key(self, prefix: str, topic: str, max_results: int) -> str:
        normalized_topic = topic.lower().strip()
        topic_hash = hashlib.md5(normalized_topic.encode()).hexdigest()
        return f"{prefix}:{topic_hash}:{max_results}"

    def _cleanup_expired(self):
        now = time.time()

        if now - self.last_cleanup < self.CLEANUP_INTERVAL:
            return

        with self.lock:
            expired_keys = []

            for key, entry in self.cache.items():
                if entry.is_expired():
                    expired_keys.append(key)

            for key in expired_keys:
                del self.cache[key]

            if expired_keys:
                self.last_cleanup = now
                logger.info(f"[CACHE] Cleaned up {len(expired_keys)} expired entries")

    def set(self, prefix: str, topic: str, max_results: int, value: Any, ttl_seconds: int):
        key = self._generate_key(prefix, topic, max_results)
        entry = CacheEntry(value, ttl_seconds)

        with self.lock:
            self._cleanup_expired()

            if len(self.cache) >= self.max_size and key not in self.cache:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]

            self.cache[key] = entry
            self.cache.move_to_end(key)

    def get(self, prefix: str, topic: str, max_results: int) -> Optional[Any]:
        """Get value from cache or None if expired/not found."""
        key = self._generate_key(prefix, topic, max_results)

        with self.lock:
            self._cleanup_expired()

            entry = self.cache.get(key)

            if entry is None:
                return None

            if entry.is_expired():
                del self.cache[key]
                return None

            self.cache.move_to_end(key)
            return entry.value

    def clear(self):
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
            logger.info("[CACHE] Cache cleared")

    def get_stats(self) -> dict:
        """Get cache statistics."""
        with self.lock:
            now = time.time()
            active_count = sum(1 for entry in self.cache.values() if not entry.is_expired())
            expired_count = sum(1 for entry in self.cache.values() if entry.is_expired())

            return {
                "total_entries": len(self.cache),
                "active_entries": active_count,
                "expired_entries": expired_count,
                "max_size": self.max_size,
                "usage_percent": round((len(self.cache) / self.max_size) * 100, 2),
            }


class HybridCache:
    """
    Hybrid cache that uses Redis as primary and TTLCache as fallback.

    Maintains the same synchronous interface as TTLCache while using
    async Redis operations internally. Falls back to in-memory cache
    if Redis is unavailable.
    """

    def __init__(self, max_size: int = 1000, redis_url: Optional[str] = None):
        """
        Initialize hybrid cache with Redis and in-memory fallback.

        Args:
            max_size: Maximum size of in-memory fallback cache
            redis_url: Redis connection URL (default: from REDIS_URL env var)
        """
        self._memory_cache = TTLCache(max_size=max_size)
        self._redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._redis_available = False
        self._redis_cache = None
        self._lock = threading.Lock()
        self._loop = None

        # Try to initialize Redis
        self._init_redis()

    def _init_redis(self):
        """Initialize Redis client (lazy - no blocking connection test)."""
        try:
            self._redis_cache = RedisCache(redis_url=self._redis_url)
            # Don't ping here - defer to first operation
            logger.info(f"[CACHE] Redis client created (connection deferred): {self._redis_url}")
        except ImportError as e:
            logger.warning(f"[CACHE] Redis package not available: {e}")
        except Exception as e:
            logger.warning(f"[CACHE] Redis initialization failed: {e}")

    async def _ensure_connected(self) -> bool:
        """Ensure Redis is connected (lazy connection on first use)."""
        if self._redis_cache is None:
            return False
        if self._redis_available:
            return True
        try:
            if await self._redis_cache.ping():
                self._redis_available = True
                logger.info(f"[CACHE] Redis connected: {self._redis_url}")
                return True
        except Exception as e:
            logger.warning(f"[CACHE] Redis ping failed: {e}")
        self._redis_available = False
        return False

    def _generate_key(self, prefix: str, topic: str, max_results: int) -> str:
        """Generate cache key matching TTLCache format."""
        normalized_topic = topic.lower().strip()
        topic_hash = hashlib.md5(normalized_topic.encode()).hexdigest()
        return f"{prefix}:{topic_hash}:{max_results}"

    def get(self, prefix: str, topic: str, max_results: int) -> Optional[Any]:
        """Get from memory cache (Redis async bridge limited in event loop thread)."""
        return self._memory_cache.get(prefix, topic, max_results)

    def set(self, prefix: str, topic: str, max_results: int, value: Any, ttl_seconds: int):
        """Set in memory cache, fire-and-forget to Redis."""
        key = self._generate_key(prefix, topic, max_results)

        if self._redis_cache:
            async def _bg_set():
                try:
                    if await self._ensure_connected():
                        await self._redis_cache.set(key, value, ttl=ttl_seconds)
                        logger.debug(f"[CACHE] Redis set: {key}")
                except Exception as e2:
                    logger.debug(f"[CACHE] Redis bg set skipped: {e2}")
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    asyncio.ensure_future(_bg_set())
            except RuntimeError:
                pass

        self._memory_cache.set(prefix, topic, max_results, value, ttl_seconds)

    def clear(self):
        """Clear all cache entries (Redis and memory)."""
        if self._redis_cache:
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    future = asyncio.run_coroutine_threadsafe(self._ensure_connected(), loop)
                    try:
                        connected = future.result(timeout=2.0)
                    except Exception:
                        connected = False
                    if connected:
                        clear_future = asyncio.run_coroutine_threadsafe(
                            self._redis_cache.clear(), loop
                        )
                        clear_future.result(timeout=2.0)
                        logger.info("[CACHE] Redis cache cleared")
            except RuntimeError:
                # No running loop - not in async context, skip Redis
                pass
            except Exception as e:
                logger.warning(f"[CACHE] Redis clear failed: {e}")

        self._memory_cache.clear()

    def get_stats(self) -> dict:
        """Get combined cache statistics."""
        memory_stats = self._memory_cache.get_stats()

        redis_stats = {}
        if self._redis_cache:
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    future = asyncio.run_coroutine_threadsafe(self._ensure_connected(), loop)
                    try:
                        connected = future.result(timeout=2.0)
                    except Exception:
                        connected = False
                    if connected:
                        stats_future = asyncio.run_coroutine_threadsafe(
                            self._redis_cache.get_stats(), loop
                        )
                        redis_stats = stats_future.result(timeout=2.0)
            except RuntimeError:
                # No running loop - not in async context, skip Redis
                pass
            except Exception as e:
                logger.warning(f"[CACHE] Redis stats failed: {e}")

        return {
            "type": "hybrid",
            "redis_available": self._redis_available,
            "memory": memory_stats,
            "redis": redis_stats,
        }

    def is_redis_available(self) -> bool:
        """Check if Redis is currently available."""
        return self._redis_available

    async def close(self):
        """Close Redis connection gracefully."""
        if self._redis_cache:
            try:
                await self._redis_cache.close()
                logger.info("[CACHE] Redis connection closed")
            except Exception as e:
                logger.warning(f"[CACHE] Error closing Redis: {e}")


_cache_instance: Optional[HybridCache] = None
_cache_lock = threading.Lock()


def get_cache() -> HybridCache:
    """Get or create global hybrid cache instance (Redis + in-memory fallback)."""
    global _cache_instance

    if _cache_instance is None:
        with _cache_lock:
            if _cache_instance is None:
                _cache_instance = HybridCache(
                    max_size=config.CACHE_MAX_SIZE,
                    redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                )
                logger.info(f"[CACHE] Hybrid cache initialized (max_size={config.CACHE_MAX_SIZE})")

    return _cache_instance


def get_redis_cache(redis_url: Optional[str] = None) -> RedisCache:
    """Get or create Redis cache instance (for direct Redis access)."""
    return RedisCache(redis_url=redis_url)


__all__ = ["RedisCache", "get_redis_cache", "get_cache", "HybridCache", "TTLCache"]
