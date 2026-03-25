"""Tests for RedisRateLimiter implementation.

TDD RED phase: These tests will fail initially since RedisRateLimiter doesn't exist yet.
"""
import pytest
import time
from unittest.mock import AsyncMock, MagicMock

from app.rate_limiter import RedisRateLimiter


class TestRedisRateLimiter:

    @pytest.fixture
    def mock_redis(self):
        redis = AsyncMock()
        redis.zadd = AsyncMock()
        redis.zremrangebyscore = AsyncMock()
        redis.zcard = AsyncMock()
        redis.zrange = AsyncMock()
        redis.expire = AsyncMock()
        redis.pipeline = MagicMock(return_value=redis)
        return redis

    @pytest.fixture
    def rate_limiter(self, mock_redis):
        return RedisRateLimiter(
            redis_client=mock_redis,
            limit=3,
            window_seconds=60
        )

    def test_init(self, mock_redis):
        limiter = RedisRateLimiter(
            redis_client=mock_redis,
            limit=3,
            window_seconds=60
        )

        assert limiter.redis == mock_redis
        assert limiter.limit == 3
        assert limiter.window_seconds == 60
        assert limiter.key_prefix == "rate_limit:"

    @pytest.mark.asyncio
    async def test_is_allowed_under_limit(self, rate_limiter, mock_redis):
        mock_redis.zcard.return_value = 1
        mock_redis.zadd.return_value = 1

        is_allowed, metadata = await rate_limiter.is_allowed("192.168.1.1")

        assert is_allowed is True
        assert metadata["remaining"] == 1
        assert metadata["reset_after"] == 60
        mock_redis.zadd.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_allowed_at_limit(self, rate_limiter, mock_redis):
        mock_redis.zcard.return_value = 2
        mock_redis.zadd.return_value = 1

        is_allowed, metadata = await rate_limiter.is_allowed("192.168.1.1")

        assert is_allowed is True
        assert metadata["remaining"] == 0
        mock_redis.zadd.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_allowed_over_limit(self, rate_limiter, mock_redis):
        mock_redis.zcard.return_value = 3
        now = time.time()
        mock_redis.zrange.return_value = [str(now - 30)]

        is_allowed, metadata = await rate_limiter.is_allowed("192.168.1.1")

        assert is_allowed is False
        assert metadata["remaining"] == 0
        assert metadata["reset_after"] <= 30
        assert metadata["reset_after"] > 0

    @pytest.mark.asyncio
    async def test_remaining_count(self, rate_limiter, mock_redis):
        mock_redis.zcard.return_value = 0
        mock_redis.zadd.return_value = 1

        _, metadata = await rate_limiter.is_allowed("192.168.1.1")
        assert metadata["remaining"] == 2

        mock_redis.zcard.return_value = 1
        _, metadata = await rate_limiter.is_allowed("192.168.1.1")
        assert metadata["remaining"] == 1

        mock_redis.zcard.return_value = 2
        _, metadata = await rate_limiter.is_allowed("192.168.1.1")
        assert metadata["remaining"] == 0

    @pytest.mark.asyncio
    async def test_reset_time(self, rate_limiter, mock_redis):
        now = time.time()
        mock_redis.zcard.return_value = 3
        mock_redis.zrange.return_value = [str(now - 45)]

        is_allowed, metadata = await rate_limiter.is_allowed("192.168.1.1")

        assert is_allowed is False
        assert metadata["reset_after"] <= 15
        assert metadata["reset_after"] > 0

    @pytest.mark.asyncio
    async def test_sliding_window(self, rate_limiter, mock_redis):
        mock_redis.zcard.return_value = 1
        mock_redis.zadd.return_value = 1

        await rate_limiter.is_allowed("192.168.1.1")

        mock_redis.zremrangebyscore.assert_called_once()
        call_args = mock_redis.zremrangebyscore.call_args
        assert call_args[0][0] == "rate_limit:192.168.1.1"

    @pytest.mark.asyncio
    async def test_different_ips(self, rate_limiter, mock_redis):
        mock_redis.zadd.return_value = 1

        mock_redis.zcard.return_value = 0
        is_allowed, metadata = await rate_limiter.is_allowed("192.168.1.1")
        assert is_allowed is True
        assert metadata["remaining"] == 2

        mock_redis.zcard.reset_mock()
        mock_redis.zcard.return_value = 0

        is_allowed, metadata = await rate_limiter.is_allowed("192.168.1.2")
        assert is_allowed is True
        assert metadata["remaining"] == 2

        calls = mock_redis.zadd.call_args_list
        assert "rate_limit:192.168.1.1" in str(calls[0])
        assert "rate_limit:192.168.1.2" in str(calls[1])

    @pytest.mark.asyncio
    async def test_reset(self, rate_limiter, mock_redis):
        mock_redis.delete = AsyncMock(return_value=1)

        await rate_limiter.reset("192.168.1.1")

        mock_redis.delete.assert_called_once_with("rate_limit:192.168.1.1")

    @pytest.mark.asyncio
    async def test_key_formatting(self, rate_limiter, mock_redis):
        mock_redis.zcard.return_value = 0
        mock_redis.zadd.return_value = 1

        await rate_limiter.is_allowed("10.0.0.1")

        mock_redis.zcard.assert_called_once_with("rate_limit:10.0.0.1")

    @pytest.mark.asyncio
    async def test_ttl_set_on_key(self, rate_limiter, mock_redis):
        mock_redis.zcard.return_value = 0
        mock_redis.zadd.return_value = 1

        await rate_limiter.is_allowed("192.168.1.1")

        mock_redis.expire.assert_called_once()
        call_args = mock_redis.expire.call_args
        assert call_args[0][0] == "rate_limit:192.168.1.1"
        assert call_args[0][1] == 60

    @pytest.mark.asyncio
    async def test_redis_connection_error_returns_allowed(self, rate_limiter, mock_redis):
        """Fail-open: ConnectionError should allow request with error info."""
        from redis.exceptions import ConnectionError
        mock_redis.zremrangebyscore.side_effect = ConnectionError("Connection refused")

        is_allowed, metadata = await rate_limiter.is_allowed("192.168.1.1")

        assert is_allowed is True
        assert "error" in metadata or metadata.get("remaining") == rate_limiter.limit

    @pytest.mark.asyncio
    async def test_redis_timeout_returns_allowed(self, rate_limiter, mock_redis):
        """Fail-open: TimeoutError should allow request."""
        from redis.exceptions import TimeoutError
        mock_redis.zremrangebyscore.side_effect = TimeoutError("Connection timed out")

        is_allowed, metadata = await rate_limiter.is_allowed("192.168.1.1")

        assert is_allowed is True

    @pytest.mark.asyncio
    async def test_redis_unavailable_logs_warning(self, rate_limiter, mock_redis, caplog):
        """Fail-open: Redis errors should be logged but not raised."""
        from redis.exceptions import ConnectionError
        mock_redis.zremrangebyscore.side_effect = ConnectionError("Redis unavailable")

        with caplog.at_level("WARNING"):
            is_allowed, _ = await rate_limiter.is_allowed("192.168.1.1")

        assert is_allowed is True
        assert "redis" in caplog.text.lower() or "connection" in caplog.text.lower() or "rate_limiter" in caplog.text.lower()
