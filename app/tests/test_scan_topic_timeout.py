import httpx

import extractor
import app.main as main_module
from unittest.mock import patch


class MockTimeoutClient:
    async def post(self, *args, **kwargs):
        raise httpx.TimeoutException("timed out")


class TestScanTopicTimeout:
    def test_scan_topic_timeout_returns_partial_response(self, client, monkeypatch):
        original_url = main_module.N8N_WEBHOOK_URL

        main_module.N8N_WEBHOOK_URL = "https://example.com/webhook"
        monkeypatch.setattr(extractor, "get_http_client", lambda: MockTimeoutClient())

        # Mock get_env to return 120.0 for SCAN_TOPIC_TIMEOUT_SECONDS
        original_get_env = main_module.get_env

        def mock_get_env(key, default=None):
            if key == "SCAN_TOPIC_TIMEOUT_SECONDS":
                return 120.0
            return original_get_env(key, default)

        monkeypatch.setattr(main_module, "get_env", mock_get_env)

        try:
            response = client.post("/scan-topic", json={"topic": "test topic", "max_results": 5})
        finally:
            main_module.N8N_WEBHOOK_URL = original_url

        assert response.status_code == 200

        data = response.json()
        assert data["timed_out"] is True
        assert data["verdict"] == "PARTIAL"
        assert "Deep search took longer than expected" in data["summary"]
        assert any("120.0 seconds" in finding for finding in data["key_findings"])
