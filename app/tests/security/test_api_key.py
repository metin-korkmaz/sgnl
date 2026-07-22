"""Unit tests for API key authentication module."""

import os
import pytest
from fastapi import HTTPException, Header
from unittest.mock import patch

from app.security.api_key import require_api_key, get_valid_api_keys


class TestGetValidApiKeys:
    """Tests for get_valid_api_keys function."""
    
    def test_returns_empty_set_when_no_env_var(self):
        """Should return empty set when API_KEYS not set."""
        with patch.dict(os.environ, {}, clear=True):
            keys = get_valid_api_keys()
            assert keys == set()
    
    def test_returns_empty_set_when_empty_env_var(self):
        """Should return empty set when API_KEYS is empty."""
        with patch.dict(os.environ, {"API_KEYS": ""}, clear=True):
            keys = get_valid_api_keys()
            assert keys == set()
    
    def test_returns_single_key(self):
        """Should return set with single key."""
        with patch.dict(os.environ, {"API_KEYS": "test-key-123"}, clear=True):
            keys = get_valid_api_keys()
            assert keys == {"test-key-123"}
    
    def test_returns_multiple_keys(self):
        """Should return set with multiple keys from comma-separated string."""
        with patch.dict(os.environ, {"API_KEYS": "key1,key2,key3"}, clear=True):
            keys = get_valid_api_keys()
            assert keys == {"key1", "key2", "key3"}
    
    def test_trims_whitespace(self):
        """Should trim whitespace around keys."""
        with patch.dict(os.environ, {"API_KEYS": " key1 , key2 , key3 "}, clear=True):
            keys = get_valid_api_keys()
            assert keys == {"key1", "key2", "key3"}
    
    def test_ignores_empty_strings_in_list(self):
        """Should ignore empty strings from consecutive commas."""
        with patch.dict(os.environ, {"API_KEYS": "key1,,key2,,,key3"}, clear=True):
            keys = get_valid_api_keys()
            assert keys == {"key1", "key2", "key3"}


class TestRequireApiKey:
    """Tests for require_api_key dependency function."""
    
    def test_raises_401_when_no_api_key(self):
        """Should raise 401 when X-API-Key header is missing."""
        with patch.dict(os.environ, {"API_KEYS": "valid-key"}, clear=True):
            with pytest.raises(HTTPException) as exc_info:
                require_api_key(None)
            
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "API key required"
            assert exc_info.value.headers == {"WWW-Authenticate": "ApiKey"}
    
    def test_raises_401_when_empty_api_key(self):
        """Should raise 401 when X-API-Key header is empty string."""
        with patch.dict(os.environ, {"API_KEYS": "valid-key"}, clear=True):
            with pytest.raises(HTTPException) as exc_info:
                require_api_key("")
            
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "API key required"
    
    def test_raises_401_when_invalid_api_key(self):
        """Should raise 401 when API key is invalid."""
        with patch.dict(os.environ, {"API_KEYS": "valid-key-123"}, clear=True):
            with pytest.raises(HTTPException) as exc_info:
                require_api_key("invalid-key-456")
            
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Invalid API key"
            assert exc_info.value.headers == {"WWW-Authenticate": "ApiKey"}
    
    def test_returns_key_when_valid(self):
        """Should return API key when valid."""
        with patch.dict(os.environ, {"API_KEYS": "valid-key-123,another-key"}, clear=True):
            result = require_api_key("valid-key-123")
            assert result == "valid-key-123"
    
    def test_returns_key_when_valid_multiple_keys(self):
        """Should return API key when valid among multiple keys."""
        with patch.dict(os.environ, {"API_KEYS": "key1,key2,key3"}, clear=True):
            result = require_api_key("key2")
            assert result == "key2"
    
    def test_validates_exact_match(self):
        """Should validate exact key match (no partial matches)."""
        with patch.dict(os.environ, {"API_KEYS": "valid-key-123"}, clear=True):
            with pytest.raises(HTTPException) as exc_info:
                require_api_key("valid-key")
            
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Invalid API key"


class TestRequireApiKeyLogging:
    """Tests for logging behavior."""
    
    def test_logs_warning_on_missing_key(self, caplog):
        """Should log warning when API key is missing."""
        with patch.dict(os.environ, {"API_KEYS": "valid-key"}, clear=True):
            with pytest.raises(HTTPException):
                require_api_key(None)
        
        assert "Request without API key" in caplog.text
    
    def test_logs_warning_on_invalid_key(self, caplog):
        """Should log warning with truncated key on invalid key."""
        with patch.dict(os.environ, {"API_KEYS": "valid-key"}, clear=True):
            with pytest.raises(HTTPException):
                require_api_key("invalid-key-very-long")
        
        # Should log truncated version for security
        assert "Invalid API key" in caplog.text
        assert "invalid-ke..." in caplog.text
    
    def test_does_not_log_full_key(self, caplog):
        """Should never log full API key (security)."""
        secret_key = "super-secret-api-key-12345"
        with patch.dict(os.environ, {"API_KEYS": "valid-key"}, clear=True):
            with pytest.raises(HTTPException):
                require_api_key(secret_key)
        
        # Full key should not appear in logs
        assert secret_key not in caplog.text


class TestIntegrationWithFastAPI:
    """Integration tests simulating FastAPI dependency usage."""
    
    def test_dependency_injection_pattern(self):
        """Should work correctly as FastAPI dependency."""
        from fastapi import Depends, FastAPI
        from fastapi.testclient import TestClient
        
        app = FastAPI()
        
        @app.get("/protected")
        def protected_endpoint(api_key: str = Depends(require_api_key)):
            return {"message": "success", "key": api_key}
        
        client = TestClient(app)
        
        with patch.dict(os.environ, {"API_KEYS": "test-api-key"}, clear=True):
            # Without header
            response = client.get("/protected")
            assert response.status_code == 401
            assert response.json()["detail"] == "API key required"
            
            # With invalid header
            response = client.get("/protected", headers={"X-API-Key": "wrong-key"})
            assert response.status_code == 401
            assert response.json()["detail"] == "Invalid API key"
            
            # With valid header
            response = client.get("/protected", headers={"X-API-Key": "test-api-key"})
            assert response.status_code == 200
            assert response.json()["message"] == "success"
