import pytest
from unittest.mock import AsyncMock, MagicMock
from app.main import RateLimitMiddleware
import time
from starlette.requests import Request
from starlette.responses import Response


class TestRateLimitMiddleware:
    """Test RateLimitMiddleware functionality."""

    def test_init(self):
        """Test middleware initialization."""
        from fastapi import FastAPI
        app = FastAPI()
        middleware = RateLimitMiddleware(app)

        assert middleware.request_counts == {}
        assert middleware.RATE_LIMIT == 3  # default
        assert middleware.WINDOW_SECONDS == 60  # default
        assert "/fast-search" in middleware.PROTECTED_PATHS

    def test_clean_old_requests_no_old_requests(self):
        """Test cleaning when no old requests exist."""
        from fastapi import FastAPI
        app = FastAPI()
        middleware = RateLimitMiddleware(app)

        middleware.request_counts = {"ip1": [time.time()]}
        middleware._clean_old_requests("ip1")

        assert "ip1" in middleware.request_counts
        assert len(middleware.request_counts["ip1"]) == 1

    def test_clean_old_requests_with_old_requests(self):
        """Test cleaning old requests."""
        from fastapi import FastAPI
        app = FastAPI()
        middleware = RateLimitMiddleware(app)

        old_time = time.time() - 70  # 70 seconds ago
        recent_time = time.time() - 30  # 30 seconds ago

        middleware.request_counts = {
            "ip1": [old_time, recent_time, time.time()]
        }
        middleware._clean_old_requests("ip1")

        assert len(middleware.request_counts["ip1"]) == 2  # old one removed

    def test_clean_old_requests_empty_dict(self):
        """Test cleaning with empty request counts."""
        from fastapi import FastAPI
        app = FastAPI()
        middleware = RateLimitMiddleware(app)

        middleware._clean_old_requests("nonexistent_ip")
        # Should not raise error

    def test_get_client_ip_with_x_forwarded_for(self):
        """Test IP extraction with X-Forwarded-For header."""
        from fastapi import FastAPI
        app = FastAPI()
        middleware = RateLimitMiddleware(app)

        mock_request = MagicMock()
        mock_request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}
        mock_request.client = None

        ip = middleware._get_client_ip(mock_request)
        assert ip == "192.168.1.1"

    def test_get_client_ip_without_x_forwarded_for(self):
        """Test IP extraction without X-Forwarded-For header."""
        from fastapi import FastAPI
        app = FastAPI()
        middleware = RateLimitMiddleware(app)

        mock_request = MagicMock()
        mock_request.headers = {}
        mock_request.client.host = "192.168.1.100"

        ip = middleware._get_client_ip(mock_request)
        assert ip == "192.168.1.100"

    def test_get_client_ip_unknown(self):
        """Test IP extraction when no IP available."""
        from fastapi import FastAPI
        app = FastAPI()
        middleware = RateLimitMiddleware(app)

        mock_request = MagicMock()
        mock_request.headers = {}
        mock_request.client = None

        ip = middleware._get_client_ip(mock_request)
        assert ip == "unknown"

    @pytest.mark.asyncio
    async def test_dispatch_unprotected_path(self):
        """Test dispatch for unprotected paths (no rate limiting)."""
        from fastapi import FastAPI
        app = FastAPI()
        middleware = RateLimitMiddleware(app)

        mock_request = MagicMock()
        mock_request.url.path = "/health"
        mock_call_next = AsyncMock(return_value=Response("OK"))

        response = await middleware.dispatch(mock_request, mock_call_next)

        mock_call_next.assert_called_once()
        assert response == mock_call_next.return_value

    @pytest.mark.asyncio
    async def test_dispatch_under_limit(self):
        """Test dispatch when under rate limit."""
        from fastapi import FastAPI
        app = FastAPI()
        middleware = RateLimitMiddleware(app)

        mock_request = MagicMock()
        mock_request.url.path = "/fast-search"
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"

        mock_call_next = AsyncMock(return_value=Response("OK"))

        response = await middleware.dispatch(mock_request, mock_call_next)

        mock_call_next.assert_called_once()
        assert response == mock_call_next.return_value
        assert "127.0.0.1" in middleware.request_counts
        assert len(middleware.request_counts["127.0.0.1"]) == 1

    @pytest.mark.asyncio
    async def test_dispatch_at_limit(self):
        """Test dispatch when at rate limit."""
        from fastapi import FastAPI
        app = FastAPI()
        middleware = RateLimitMiddleware(app)

        # Set rate limit to 2 for testing
        middleware.RATE_LIMIT = 2

        mock_request = MagicMock()
        mock_request.url.path = "/fast-search"
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"

        mock_call_next = AsyncMock(return_value=Response("OK"))

        # First request
        await middleware.dispatch(mock_request, mock_call_next)
        # Second request
        response = await middleware.dispatch(mock_request, mock_call_next)

        mock_call_next.assert_called()  # Should be called twice
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_dispatch_over_limit(self):
        """Test dispatch when over rate limit."""
        from fastapi import FastAPI
        app = FastAPI()
        middleware = RateLimitMiddleware(app)

        # Set rate limit to 1 for testing
        middleware.RATE_LIMIT = 1

        mock_request = MagicMock()
        mock_request.url.path = "/fast-search"
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"

        mock_call_next = AsyncMock(return_value=Response("OK"))

        # First request (allowed)
        await middleware.dispatch(mock_request, mock_call_next)

        # Second request (should be rate limited)
        response = await middleware.dispatch(mock_request, mock_call_next)

        # Should return 429 status
        assert response.status_code == 429
        assert "RATE_LIMIT_EXCEEDED" in response.body.decode()
        assert "Retry-After" in response.headers

    @pytest.mark.asyncio
    async def test_dispatch_with_old_requests_cleaned(self):
        """Test that old requests are cleaned up during dispatch."""
        from fastapi import FastAPI
        app = FastAPI()
        middleware = RateLimitMiddleware(app)

        middleware.RATE_LIMIT = 2
        middleware.WINDOW_SECONDS = 1  # Short window for testing

        mock_request = MagicMock()
        mock_request.url.path = "/fast-search"
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"

        mock_call_next = AsyncMock(return_value=Response("OK"))

        # Add an old timestamp
        old_time = time.time() - 2  # 2 seconds ago, beyond window
        middleware.request_counts["127.0.0.1"] = [old_time]

        # Make a new request
        response = await middleware.dispatch(mock_request, mock_call_next)

        # Old request should be cleaned, new one added
        assert len(middleware.request_counts["127.0.0.1"]) == 1
        assert response.status_code == 200

    def test_environment_variable_rate_limit(self):
        """Test that environment variables affect rate limiting."""
        import os
        from fastapi import FastAPI

        # Set environment variables
        original_rate = os.environ.get('RATE_LIMIT')
        original_window = os.environ.get('RATE_WINDOW_SECONDS')

        try:
            os.environ['RATE_LIMIT'] = '5'
            os.environ['RATE_WINDOW_SECONDS'] = '30'

            app = FastAPI()
            middleware = RateLimitMiddleware(app)

            assert middleware.RATE_LIMIT == 5
            assert middleware.WINDOW_SECONDS == 30

        finally:
            # Restore original values
            if original_rate:
                os.environ['RATE_LIMIT'] = original_rate
            else:
                os.environ.pop('RATE_LIMIT', None)

            if original_window:
                os.environ['RATE_WINDOW_SECONDS'] = original_window
            else:
                os.environ.pop('RATE_WINDOW_SECONDS', None)</content>
<parameter name="filePath">app/tests/test_main.py