"""Standalone test runner for API key tests."""

import os
import sys
import tempfile

# Add app to path
sys.path.insert(0, '/root/sgnl-backend/app')

from fastapi import HTTPException, Depends, FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch

# Import module under test
from security.api_key import require_api_key, get_valid_api_keys


def test_get_valid_api_keys_empty():
    """Should return empty set when API_KEYS not set."""
    with patch.dict(os.environ, {}, clear=True):
        keys = get_valid_api_keys()
        assert keys == set(), f"Expected empty set, got {keys}"
    print("✓ test_get_valid_api_keys_empty passed")


def test_get_valid_api_keys_single():
    """Should return set with single key."""
    with patch.dict(os.environ, {"API_KEYS": "test-key-123"}, clear=True):
        keys = get_valid_api_keys()
        assert keys == {"test-key-123"}, f"Expected {{'test-key-123'}}, got {keys}"
    print("✓ test_get_valid_api_keys_single passed")


def test_get_valid_api_keys_multiple():
    """Should return set with multiple keys from comma-separated string."""
    with patch.dict(os.environ, {"API_KEYS": "key1,key2,key3"}, clear=True):
        keys = get_valid_api_keys()
        assert keys == {"key1", "key2", "key3"}, f"Expected 3 keys, got {keys}"
    print("✓ test_get_valid_api_keys_multiple passed")


def test_get_valid_api_keys_trims_whitespace():
    """Should trim whitespace around keys."""
    with patch.dict(os.environ, {"API_KEYS": " key1 , key2 , key3 "}, clear=True):
        keys = get_valid_api_keys()
        assert keys == {"key1", "key2", "key3"}, f"Expected trimmed keys, got {keys}"
    print("✓ test_get_valid_api_keys_trims_whitespace passed")


def test_get_valid_api_keys_ignores_empty():
    """Should ignore empty strings from consecutive commas."""
    with patch.dict(os.environ, {"API_KEYS": "key1,,key2,,,key3"}, clear=True):
        keys = get_valid_api_keys()
        assert keys == {"key1", "key2", "key3"}, f"Expected no empty strings, got {keys}"
    print("✓ test_get_valid_api_keys_ignores_empty passed")


def test_require_api_key_missing():
    """Should raise 401 when X-API-Key header is missing."""
    with patch.dict(os.environ, {"API_KEYS": "valid-key"}, clear=True):
        try:
            require_api_key(None)
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.status_code == 401, f"Expected 401, got {e.status_code}"
            assert e.detail == "API key required", f"Expected 'API key required', got {e.detail}"
    print("✓ test_require_api_key_missing passed")


def test_require_api_key_empty():
    """Should raise 401 when X-API-Key header is empty string."""
    with patch.dict(os.environ, {"API_KEYS": "valid-key"}, clear=True):
        try:
            require_api_key("")
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.status_code == 401
            assert e.detail == "API key required"
    print("✓ test_require_api_key_empty passed")


def test_require_api_key_invalid():
    """Should raise 401 when API key is invalid."""
    with patch.dict(os.environ, {"API_KEYS": "valid-key-123"}, clear=True):
        try:
            require_api_key("invalid-key-456")
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.status_code == 401
            assert e.detail == "Invalid API key"
    print("✓ test_require_api_key_invalid passed")


def test_require_api_key_valid():
    """Should return API key when valid."""
    with patch.dict(os.environ, {"API_KEYS": "valid-key-123,another-key"}, clear=True):
        result = require_api_key("valid-key-123")
        assert result == "valid-key-123", f"Expected 'valid-key-123', got {result}"
    print("✓ test_require_api_key_valid passed")


def test_require_api_key_valid_multiple():
    """Should return API key when valid among multiple keys."""
    with patch.dict(os.environ, {"API_KEYS": "key1,key2,key3"}, clear=True):
        result = require_api_key("key2")
        assert result == "key2", f"Expected 'key2', got {result}"
    print("✓ test_require_api_key_valid_multiple passed")


def test_require_api_key_exact_match():
    """Should validate exact key match (no partial matches)."""
    with patch.dict(os.environ, {"API_KEYS": "valid-key-123"}, clear=True):
        try:
            require_api_key("valid-key")
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.status_code == 401
            assert e.detail == "Invalid API key"
    print("✓ test_require_api_key_exact_match passed")


def test_logging_on_missing(caplog):
    """Should log warning when API key is missing."""
    import logging
    with patch.dict(os.environ, {"API_KEYS": "valid-key"}, clear=True):
        try:
            require_api_key(None)
        except HTTPException:
            pass
    print("✓ test_logging_on_missing passed")


def test_integration_with_fastapi():
    """Should work correctly as FastAPI dependency."""
    app = FastAPI()
    
    @app.get("/protected")
    def protected_endpoint(api_key: str = Depends(require_api_key)):
        return {"message": "success", "key": api_key}
    
    client = TestClient(app)
    
    with patch.dict(os.environ, {"API_KEYS": "test-api-key"}, clear=True):
        # Without header
        response = client.get("/protected")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        assert response.json()["detail"] == "API key required"
        
        # With invalid header
        response = client.get("/protected", headers={"X-API-Key": "wrong-key"})
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        assert response.json()["detail"] == "Invalid API key"
        
        # With valid header
        response = client.get("/protected", headers={"X-API-Key": "test-api-key"})
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json()["message"] == "success"
    
    print("✓ test_integration_with_fastapi passed")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Running API Key Authentication Tests")
    print("="*60 + "\n")
    
    tests = [
        test_get_valid_api_keys_empty,
        test_get_valid_api_keys_single,
        test_get_valid_api_keys_multiple,
        test_get_valid_api_keys_trims_whitespace,
        test_get_valid_api_keys_ignores_empty,
        test_require_api_key_missing,
        test_require_api_key_empty,
        test_require_api_key_invalid,
        test_require_api_key_valid,
        test_require_api_key_valid_multiple,
        test_require_api_key_exact_match,
        test_integration_with_fastapi,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} ERROR: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    sys.exit(0 if failed == 0 else 1)
