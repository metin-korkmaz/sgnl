"""
Redis cache implementation for SGNL backend.

Provides distributed caching with connection pooling and retry logic.
Maintains same interface as TTLCache for drop-in replacement.
"""
import os
import json
import logging
import asyncio
from typing import Any, Optional, Union
from functools import wraps

import redis.asyncio as redis
from redis.asyncio import Redis
from redis.connection import ConnectionPool

logger = logging.getLogger(__name__)


def retry_on_error(max_retries: int = 3, delay: float = 0.1):
    """Decorator to retry Redis operations on connection errors."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except redis.ConnectionError as e:
                    if attempt == max_retries - 1:
                        logger.error(f"[REDIS] Connection failed after {max_retries} attempts: {e}")
                        raise
                    logger.warning(f"[REDIS] Connection error (attempt {attempt + 1}/{max_retries}): {e}")
                    await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
                except Exception as e:
                    logger.error(f"[REDIS] Unexpected error: {e}")
                    raise
            return None
        return wrapper
    return decorator


class RedisCache:
    """
    Redis-based cache with connection pooling and TTL support.

    Features:
    - Connection pooling for efficient resource usage
    - Automatic retry with exponential backoff
    - JSON serialization for complex objects
    - Same interface as TTLCache for compatibility
    - Distributed caching across multiple workers

    Usage:
        cache = RedisCache()

        # Set value with 1 hour TTL
        await cache.set("search:topic:10", results, ttl=3600)

        # Get value (returns None if expired or not found)
        results = await cache.get("search:topic:10")

        # Delete value
        await cache.delete("search:topic:10")
    """

    def __init__(self, redis_url: Optional[str] = None, max_connections: int = 10):
        """
        Initialize Redis cache with connection pooling.

        Args:
            redis_url: Redis connection URL (default: from REDIS_URL env var)
            max_connections: Maximum connections in pool (default: 10)
        """
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.max_connections = max_connections
        self._pool: Optional[ConnectionPool] = None
        self._redis: Optional[Redis] = None

    async def _get_redis(self) -> Redis:
        """Get or create Redis connection with pooling."""
        if self._redis is None:
            self._pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                decode_responses=True
            )
            self._redis = Redis(connection_pool=self._pool)
            logger.info(f"[REDIS] Connected to {self.redis_url}")
        return self._redis

    async def close(self):
        """Close Redis connection pool."""
        if self._redis:
            await self._redis.close()
            self._redis = None
        if self._pool:
            await self._pool.disconnect()
            self._pool = None
        logger.info("[REDIS] Connection closed")

    @retry_on_error(max_retries=3)
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from Redis cache.

        Args:
            key: Cache key

        Returns:
            Deserialized value or None if not found/expired
        """
        try:
            r = await self._get_redis()
            data = await r.get(key)

            if data is None:
                return None

            # Deserialize JSON
            return json.loads(data)
        except json.JSONDecodeError as e:
            logger.error(f"[REDIS] Failed to decode value for key {key}: {e}")
            return None
        except Exception as e:
            logger.error(f"[REDIS] Get error for key {key}: {e}")
            raise

    @retry_on_error(max_retries=3)
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in Redis cache with optional TTL.

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time-to-live in seconds (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            r = await self._get_redis()
            serialized = json.dumps(value, default=str)

            if ttl:
                await r.setex(key, ttl, serialized)
            else:
                await r.set(key, serialized)

            return True
        except (TypeError, ValueError) as e:
            logger.error(f"[REDIS] Failed to serialize value for key {key}: {e}")
            return False
        except Exception as e:
            logger.error(f"[REDIS] Set error for key {key}: {e}")
            raise

    @retry_on_error(max_retries=3)
    async def delete(self, key: str) -> bool:
        """
        Delete value from Redis cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if key didn't exist
        """
        try:
            r = await self._get_redis()
            result = await r.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"[REDIS] Delete error for key {key}: {e}")
            raise

    @retry_on_error(max_retries=3)
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        try:
            r = await self._get_redis()
            return await r.exists(key) > 0
        except Exception as e:
            logger.error(f"[REDIS] Exists error for key {key}: {e}")
            raise

    @retry_on_error(max_retries=3)
    async def clear(self) -> bool:
        """
        Clear all cache entries (use with caution).

        Returns:
            True if successful
        """
        try:
            r = await self._get_redis()
            await r.flushdb()
            logger.info("[REDIS] Cache cleared")
            return True
        except Exception as e:
            logger.error(f"[REDIS] Clear error: {e}")
            raise

    @retry_on_error(max_retries=3)
    async def get_stats(self) -> dict:
        """
        Get Redis cache statistics.

        Returns:
            Dictionary with cache stats
        """
        try:
            r = await self._get_redis()
            info = await r.info()

            return {
                "total_entries": info.get('db0', {}).get('keys', 0) if 'db0' in info else 0,
                "used_memory": info.get('used_memory_human', 'N/A'),
                "max_memory": info.get('maxmemory_human', 'N/A'),
                "connected_clients": info.get('connected_clients', 0),
                "hit_rate": info.get('keyspace_hits', 0) / (info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1)) if info.get('keyspace_hits', 0) > 0 else 0,
                "uptime_seconds": info.get('uptime_in_seconds', 0)
            }
        except Exception as e:
            logger.error(f"[REDIS] Stats error: {e}")
            return {
                "total_entries": 0,
                "error": str(e)
            }

    @retry_on_error(max_retries=3)
    async def ping(self) -> bool:
        """
        Test Redis connection.

        Returns:
            True if Redis is reachable
        """
        try:
            r = await self._get_redis()
            return await r.ping()
        except Exception:
            return False


# Convenience function for sync-style usage (for compatibility)
def get_redis_cache(redis_url: Optional[str] = None) -> RedisCache:
    """Get or create Redis cache instance."""
    return RedisCache(redis_url=redis_url)
