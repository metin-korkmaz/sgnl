"""
Thread-safe in-memory cache with TTL support for SGNL backend.

Optimizes search response times by caching Tavily results and LLM analysis.
"""
import time
import threading
import hashlib
import logging
import os
from typing import Any, Optional
from collections import OrderedDict

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

    Usage:
        cache = TTLCache(max_size=1000)

        # Set value with 1 hour TTL
        cache.set("search", "topic", 10, results, ttl_seconds=3600)

        # Get value (returns None if expired or not found)
        results = cache.get("search", "topic", 10)
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
                "usage_percent": round((len(self.cache) / self.max_size) * 100, 2)
            }


_cache_instance: Optional[TTLCache] = None
_cache_lock = threading.Lock()


def get_cache() -> TTLCache:
    """Get or create global cache instance."""
    global _cache_instance

    if _cache_instance is None:
        with _cache_lock:
            if _cache_instance is None:
                max_size = int(os.getenv('CACHE_MAX_SIZE', '1000'))
                _cache_instance = TTLCache(max_size=max_size)
                logger.info(f"[CACHE] Initialized with max_size={max_size}")

    return _cache_instance