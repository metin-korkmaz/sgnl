import httpx

import extractor
import app.main as main_module


class MockTimeoutClient:
    async def post(self, *args, **kwargs):
        raise httpx.TimeoutException("timed out")


class TestScanTopicTimeout:
    def test_scan_topic_timeout_returns_partial_response(self, client, monkeypatch):
        original_url = main_module.N8N_WEBHOOK_URL
        original_timeout = main_module._CACHED_ENV.get("SCAN_TOPIC_TIMEOUT_SECONDS")

        main_module.N8N_WEBHOOK_URL = "https://example.com/webhook"
        main_module._CACHED_ENV["SCAN_TOPIC_TIMEOUT_SECONDS"] = 120.0
        monkeypatch.setattr(extractor, "get_http_client", lambda: MockTimeoutClient())

        try:
            response = client.post("/scan-topic", json={"topic": "test topic", "max_results": 5})
        finally:
            main_module.N8N_WEBHOOK_URL = original_url
            if original_timeout is None:
                main_module._CACHED_ENV.pop("SCAN_TOPIC_TIMEOUT_SECONDS", None)
            else:
                main_module._CACHED_ENV["SCAN_TOPIC_TIMEOUT_SECONDS"] = original_timeout

        assert response.status_code == 200

        data = response.json()
        assert data["timed_out"] is True
        assert data["verdict"] == "PARTIAL"
        assert "Deep search took longer than expected" in data["summary"]
        assert any("120.0 seconds" in finding for finding in data["key_findings"])
