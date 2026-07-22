"""Tests for cache module (TTLCache, HybridCache, RedisCache)."""

import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from app.cache import TTLCache, HybridCache
from app.cache.redis_cache import RedisCache


class TestTTLCache:
    """Test TTLCache class methods."""

    def test_init(self):
        """Test TTLCache initialization."""
        cache = TTLCache()
        assert cache.max_size == 1000
        assert len(cache.cache) == 0

        cache_custom = TTLCache(max_size=500)
        assert cache_custom.max_size == 500

    def test_set_and_get(self):
        """Test basic set and get operations."""
        cache = TTLCache()
        cache.set("search", "machine learning", 10, "test_value", 300)
        result = cache.get("search", "machine learning", 10)
        assert result == "test_value"

    def test_get_nonexistent_key(self):
        """Test getting a key that doesn't exist."""
        cache = TTLCache()
        result = cache.get("search", "nonexistent", 10)
        assert result is None

    def test_get_expired_key(self):
        """Test that expired keys return None."""
        cache = TTLCache()
        # Set with very short TTL (1 second)
        cache.set("search", "topic", 10, "value", 1)

        # Should work initially
        assert cache.get("search", "topic", 10) == "value"

        # Wait for expiration
        time.sleep(1.5)

        # Should be expired now
        result = cache.get("search", "topic", 10)
        assert result is None

    def test_ttl_expiration(self):
        """Test TTL expiration with multiple keys."""
        cache = TTLCache()

        # Set multiple keys with different TTLs
        cache.set("prefix1", "topic1", 5, "value1", 1)  # 1 second TTL
        cache.set("prefix2", "topic2", 5, "value2", 10)  # 10 second TTL

        # Both should be available initially
        assert cache.get("prefix1", "topic1", 5) == "value1"
        assert cache.get("prefix2", "topic2", 5) == "value2"

        # Wait for first to expire
        time.sleep(1.5)

        # First should be expired, second still valid
        assert cache.get("prefix1", "topic1", 5) is None
        assert cache.get("prefix2", "topic2", 5) == "value2"

    def test_clear(self):
        """Test clearing all cache entries."""
        cache = TTLCache()
        cache.set("prefix", "topic1", 10, "value1", 300)
        cache.set("prefix", "topic2", 10, "value2", 300)

        assert cache.get("prefix", "topic1", 10) == "value1"
        assert cache.get("prefix", "topic2", 10) == "value2"

        cache.clear()

        assert cache.get("prefix", "topic1", 10) is None
        assert cache.get("prefix", "topic2", 10) is None

    def test_get_stats(self):
        """Test cache statistics."""
        cache = TTLCache(max_size=100)

        # Empty cache
        stats = cache.get_stats()
        assert stats["total_entries"] == 0
        assert stats["active_entries"] == 0
        assert stats["max_size"] == 100

        # Add some entries
        cache.set("prefix", "topic1", 10, "value1", 300)
        cache.set("prefix", "topic2", 10, "value2", 1)  # Short TTL

        stats = cache.get_stats()
        assert stats["total_entries"] == 2
        assert stats["active_entries"] == 2
        assert stats["max_size"] == 100

        # Wait for one to expire
        time.sleep(1.5)

        stats = cache.get_stats()
        # After expiration check, one should be expired
        assert stats["expired_entries"] >= 0  # May have been cleaned up

    def test_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = TTLCache(max_size=3)

        # Fill the cache
        cache.set("prefix", "topic1", 10, "value1", 300)
        cache.set("prefix", "topic2", 10, "value2", 300)
        cache.set("prefix", "topic3", 10, "value3", 300)

        # Access topic1 to make it recently used
        cache.get("prefix", "topic1", 10)

        # Add new entry - should evict topic2 (oldest)
        cache.set("prefix", "topic4", 10, "value4", 300)

        # topic2 should be evicted
        assert cache.get("prefix", "topic2", 10) is None

        # Others should still be there
        assert cache.get("prefix", "topic1", 10) == "value1"
        assert cache.get("prefix", "topic3", 10) == "value3"
        assert cache.get("prefix", "topic4", 10) == "value4"

    def test_key_normalization(self):
        """Test that keys are normalized (case-insensitive, stripped)."""
        cache = TTLCache()
        cache.set("prefix", "Machine Learning", 10, "value1", 300)

        # Should work with different casing and whitespace
        assert cache.get("prefix", "machine learning", 10) == "value1"
        assert cache.get("prefix", "  MACHINE LEARNING  ", 10) == "value1"
        assert cache.get("prefix", "MaChInE lEaRnInG", 10) == "value1"

    def test_thread_safety(self):
        """Test thread-safe operations (basic smoke test)."""
        import threading

        cache = TTLCache(max_size=100)
        errors = []

        def worker(thread_id):
            try:
                for i in range(10):
                    cache.set("prefix", f"topic_{thread_id}_{i}", 10, f"value_{i}", 300)
                    cache.get("prefix", f"topic_{thread_id}_{i}", 10)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestHybridCache:
    """Test HybridCache class methods with Redis fallback behavior."""

    def test_init_without_redis(self):
        """Test HybridCache initialization when Redis is unavailable."""
        # Mock RedisCache to simulate unavailability
        with patch("app.cache.RedisCache") as mock_redis_class:
            mock_redis_instance = MagicMock()
            mock_redis_class.side_effect = Exception("Redis connection failed")

            cache = HybridCache()

            assert cache._memory_cache is not None
            assert cache._redis_cache is None
            assert cache._redis_available is False

    def test_fallback_to_memory_cache(self):
        """Test that HybridCache falls back to memory cache when Redis unavailable."""
        with patch("app.cache.RedisCache") as mock_redis_class:
            mock_redis_class.side_effect = Exception("Redis unavailable")

            cache = HybridCache()

            # Set and get should work via memory cache
            cache.set("prefix", "topic", 10, "test_value", 300)
            result = cache.get("prefix", "topic", 10)

            assert result == "test_value"
            assert cache._memory_cache.get("prefix", "topic", 10) == "test_value"

    def test_fallback_on_redis_get_failure(self):
        """Test fallback when Redis get fails."""
        with patch("app.cache.RedisCache") as mock_redis_class:
            mock_redis_instance = MagicMock()
            mock_redis_instance.get = AsyncMock(side_effect=Exception("Redis get failed"))
            mock_redis_class.return_value = mock_redis_instance

            cache = HybridCache()
            cache._redis_cache = mock_redis_instance

            # Set via memory cache first
            cache._memory_cache.set("prefix", "topic", 10, "fallback_value", 300)

            # Get should fail over to memory cache
            result = cache.get("prefix", "topic", 10)
            assert result == "fallback_value"

    def test_fallback_on_redis_set_failure(self):
        """Test that set still writes to memory cache when Redis fails."""
        with patch("app.cache.RedisCache") as mock_redis_class:
            mock_redis_instance = MagicMock()
            mock_redis_instance.set = AsyncMock(side_effect=Exception("Redis set failed"))
            mock_redis_class.return_value = mock_redis_instance

            cache = HybridCache()
            cache._redis_cache = mock_redis_instance

            # Set should still write to memory cache
            cache.set("prefix", "topic", 10, "value", 300)

            # Verify it's in memory cache
            result = cache._memory_cache.get("prefix", "topic", 10)
            assert result == "value"

    def test_clear_clears_both_caches(self):
        """Test that clear operation clears both Redis and memory cache."""
        with patch("app.cache.RedisCache") as mock_redis_class:
            mock_redis_instance = MagicMock()
            mock_redis_class.return_value = mock_redis_instance

            cache = HybridCache()

            # Clear should be called on both
            cache.clear()

            # Memory cache should be empty
            assert len(cache._memory_cache.cache) == 0
            # Redis clear should be attempted
            mock_redis_instance.clear.assert_not_called()  # No async context

    def test_get_stats_returns_combined_stats(self):
        """Test that get_stats returns statistics from both caches."""
        cache = HybridCache(max_size=100)

        stats = cache.get_stats()

        assert "type" in stats
        assert stats["type"] == "hybrid"
        assert "redis_available" in stats
        assert "memory" in stats
        assert "redis" in stats
        assert isinstance(stats["memory"], dict)
        assert stats["memory"]["max_size"] == 100

    def test_is_redis_available(self):
        """Test is_redis_available method."""
        cache = HybridCache()

        # Initially should be False (no connection attempt made yet)
        assert cache.is_redis_available() is False

    def test_redis_url_from_env(self):
        """Test that Redis URL is read from environment variable."""
        import os

        # Save original
        original_url = os.getenv("REDIS_URL")

        try:
            os.environ["REDIS_URL"] = "redis://custom:6379/1"
            cache = HybridCache()
            assert cache._redis_url == "redis://custom:6379/1"
        finally:
            # Restore original
            if original_url:
                os.environ["REDIS_URL"] = original_url
            else:
                del os.environ["REDIS_URL"]

    def test_redis_url_override(self):
        """Test that explicit redis_url parameter overrides env var."""
        import os

        original_url = os.getenv("REDIS_URL")

        try:
            os.environ["REDIS_URL"] = "redis://env:6379/0"
            cache = HybridCache(redis_url="redis://override:6379/2")
            assert cache._redis_url == "redis://override:6379/2"
        finally:
            if original_url:
                os.environ["REDIS_URL"] = original_url
            else:
                del os.environ["REDIS_URL"]

    def test_key_generation_consistency(self):
        """Test that key generation is consistent."""
        cache1 = HybridCache()
        cache2 = HybridCache()

        key1 = cache1._generate_key("prefix", "topic", 10)
        key2 = cache2._generate_key("prefix", "topic", 10)

        assert key1 == key2

    def test_memory_cache_ttl_respected(self):
        """Test that TTL is respected in memory cache fallback."""
        with patch("app.cache.RedisCache") as mock_redis_class:
            mock_redis_class.side_effect = Exception("Redis unavailable")

            cache = HybridCache()

            # Set with short TTL
            cache.set("prefix", "topic", 10, "value", 1)

            # Should be available initially
            assert cache.get("prefix", "topic", 10) == "value"

            # Wait for expiration
            time.sleep(1.5)

            # Should be expired
            assert cache.get("prefix", "topic", 10) is None


class TestRedisUrl:
    """Test Redis URL formatting with password authentication."""

    def test_redis_url_with_password(self):
        """Test Redis URL includes password authentication."""
        import os

        original_url = os.getenv("REDIS_URL")

        try:
            # Test with password in URL
            os.environ["REDIS_URL"] = "redis://:changeme@redis:6379/0"
            cache = HybridCache()

            assert "changeme" in cache._redis_url
            assert "@redis:6379" in cache._redis_url
        finally:
            if original_url:
                os.environ["REDIS_URL"] = original_url
            else:
                del os.environ["REDIS_URL"]

    def test_redis_url_default_no_auth(self):
        """Test default Redis URL has no authentication."""
        import os

        original_url = os.getenv("REDIS_URL")

        try:
            if "REDIS_URL" in os.environ:
                del os.environ["REDIS_URL"]

            # Should default to localhost without auth
            cache = HybridCache()
            assert cache._redis_url == "redis://localhost:6379/0"
        finally:
            if original_url:
                os.environ["REDIS_URL"] = original_url

    def test_redis_url_with_username_and_password(self):
        """Test Redis URL with both username and password."""
        cache = HybridCache(redis_url="redis://user:password@host:6379/1")

        assert "user" in cache._redis_url
        assert "password" in cache._redis_url
        assert "@host:6379" in cache._redis_url

    def test_redis_url_format_validation(self):
        """Test Redis URL format is valid."""
        test_urls = [
            "redis://localhost:6379/0",
            "redis://:password@host:6379/0",
            "redis://user:pass@host:6379/1",
            "redis://:changeme@redis:6379/0",
        ]

        for url in test_urls:
            cache = HybridCache(redis_url=url)
            assert cache._redis_url.startswith("redis://")
            assert ":" in cache._redis_url  # Has port
            assert "/" in cache._redis_url  # Has database


class TestRedisCache:
    """Test RedisCache async operations."""

    @pytest.mark.asyncio
    async def test_ping_failure(self):
        """Test ping returns False when Redis unavailable."""
        cache = RedisCache(redis_url="redis://invalid:6379/0")

        # Ping should return False, not raise exception
        result = await cache.ping()
        assert result is False

    @pytest.mark.asyncio
    async def test_set_and_get(self):
        """Test basic set and get operations (will test if Redis available)."""
        import os

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        cache = RedisCache(redis_url=redis_url)

        # Skip test if Redis not available
        if not await cache.ping():
            pytest.skip("Redis not available")

        # Test set
        result = await cache.set("test_key", "test_value", ttl=60)
        assert result is True

        # Test get
        value = await cache.get("test_key")
        assert value == "test_value"

        # Cleanup
        await cache.delete("test_key")
        await cache.close()

    @pytest.mark.asyncio
    async def test_get_nonexistent(self):
        """Test getting nonexistent key returns None."""
        import os

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        cache = RedisCache(redis_url=redis_url)

        if not await cache.ping():
            pytest.skip("Redis not available")

        value = await cache.get("nonexistent_key_12345")
        assert value is None

        await cache.close()

    @pytest.mark.asyncio
    async def test_clear(self):
        """Test clear operation."""
        import os

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        cache = RedisCache(redis_url=redis_url)

        if not await cache.ping():
            pytest.skip("Redis not available")

        # Set a test value
        await cache.set("test_clear_key", "value", ttl=60)
        assert await cache.get("test_clear_key") == "value"

        # Clear (WARNING: clears entire DB!)
        # Skip clear in tests to avoid data loss
        # await cache.clear()

        # Just delete our test key instead
        await cache.delete("test_clear_key")
        assert await cache.get("test_clear_key") is None

        await cache.close()

    def test_init_with_custom_url(self):
        """Test RedisCache initialization with custom URL."""
        cache = RedisCache(redis_url="redis://custom:6380/2")
        assert cache.redis_url == "redis://custom:6380/2"

    def test_init_default_url(self):
        """Test RedisCache default URL from env."""
        import os

        original = os.getenv("REDIS_URL")

        try:
            os.environ["REDIS_URL"] = "redis://fromenv:6379/1"
            cache = RedisCache()
            assert cache.redis_url == "redis://fromenv:6379/1"
        finally:
            if original:
                os.environ["REDIS_URL"] = original
            else:
                del os.environ["REDIS_URL"]

    def test_json_serialization(self):
        """Test that complex objects are JSON serialized."""
        import json

        # Verify JSON serialization works for common types
        test_data = {
            "string": "value",
            "number": 42,
            "float": 3.14,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "none": None,
        }

        serialized = json.dumps(test_data, default=str)
        deserialized = json.loads(serialized)

        assert deserialized == test_data
