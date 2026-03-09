"""Tests for analytics heartbeat endpoint.

These tests verify the analytics heartbeat functionality and specifically
test the bug where navigator.sendBeacon() sends text/plain content-type
but FastAPI expects application/json, causing 422 errors.
"""

import json
import pytest
from fastapi.testclient import TestClient


class TestAnalyticsHeartbeat:
    """Test suite for analytics heartbeat endpoint."""

    def test_heartbeat_text_plain_content_type(self, client: TestClient):
        """Test that heartbeat accepts text/plain content-type (sendBeacon behavior).
        
        This test reproduces the bug where navigator.sendBeacon() sends data with
        Content-Type: text/plain;charset=UTF-8, but the FastAPI endpoint expects
        application/json, causing 422 Unprocessable Entity errors.
        
        Current behavior (BUG): Returns 422
        Expected behavior (after fix): Returns 200
        
        See: https://developer.mozilla.org/en-US/docs/Web/API/Navigator/sendBeacon
        "The sendBeacon() method returns true if the user agent successfully 
        queued the data for transfer. Otherwise, it returns false."
        
        Note: sendBeacon always sends with Content-Type: text/plain;charset=UTF-8
        """
        payload = '{"session_id": "test-session-123", "path": "/test-page"}'
        
        response = client.post(
            "/analytics/heartbeat",
            content=payload,
            headers={"Content-Type": "text/plain;charset=UTF-8"}
        )
        
        # This assertion will FAIL initially (showing the bug)
        # Current behavior: 422 Unprocessable Entity
        # Expected after fix: 200 OK
        assert response.status_code == 200, (
            f"Expected 200 OK, but got {response.status_code}. "
            f"This reproduces the bug where navigator.sendBeacon() sends "
            f"text/plain content-type but FastAPI expects application/json. "
            f"Response: {response.text}"
        )
        
        data = response.json()
        assert data["status"] == "ok"

    def test_heartbeat_application_json_content_type(self, client: TestClient):
        """Test that heartbeat still works with application/json (backward compatibility).
        
        This ensures the fix doesn't break existing JSON clients.
        """
        payload = {"session_id": "test-session-456", "path": "/another-page"}
        
        response = client.post(
            "/analytics/heartbeat",
            json=payload
        )
        
        # This should pass (existing behavior)
        assert response.status_code == 200, (
            f"Expected 200 OK for JSON content-type, but got {response.status_code}. "
            f"Response: {response.text}"
        )
        
        data = response.json()
        assert data["status"] == "ok"

    def test_heartbeat_beacon_simulation_with_various_paths(self, client: TestClient):
        """Test beacon behavior with various path patterns."""
        test_cases = [
            {"session_id": "sess-001", "path": "/"},
            {"session_id": "sess-002", "path": "/fast-search"},
            {"session_id": "sess-003", "path": "/deep-scan?url=https://example.com"},
            {"session_id": "sess-004", "path": "/analytics/stats"},
        ]
        
        for test_case in test_cases:
            payload = json.dumps(test_case)
            response = client.post(
                "/analytics/heartbeat",
                content=payload,
                headers={"Content-Type": "text/plain;charset=UTF-8"}
            )
            
            assert response.status_code == 200
            assert response.json()["status"] == "ok"

    def test_heartbeat_large_payload(self, client: TestClient):
        """Test beacon with larger payload (edge case)."""
        payload = json.dumps({
            "session_id": "sess-large-001",
            "path": "/" + "x" * 1000  # Long path
        })
        
        response = client.post(
            "/analytics/heartbeat",
            content=payload,
            headers={"Content-Type": "text/plain;charset=UTF-8"}
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_heartbeat_malformed_json_returns_400(self, client: TestClient):
        """Test that malformed JSON returns 400, not 500."""
        response = client.post(
            "/analytics/heartbeat",
            content="not valid json",
            headers={"Content-Type": "text/plain;charset=UTF-8"}
        )
        
        assert response.status_code == 400
        assert "Invalid JSON" in response.json()["detail"]

    def test_heartbeat_empty_payload_returns_400(self, client: TestClient):
        """Test that empty payload returns 400."""
        response = client.post(
            "/analytics/heartbeat",
            content="",
            headers={"Content-Type": "text/plain;charset=UTF-8"}
        )
        
        assert response.status_code == 400

    def test_heartbeat_missing_session_id_returns_400(self, client: TestClient):
        """Test that missing session_id returns 400."""
        payload = json.dumps({"path": "/test-page"})  # No session_id
        
        response = client.post(
            "/analytics/heartbeat",
            content=payload,
            headers={"Content-Type": "text/plain;charset=UTF-8"}
        )
        
        assert response.status_code == 400
        assert "session_id" in response.json()["detail"]
