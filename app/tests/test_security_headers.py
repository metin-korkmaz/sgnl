"""Tests for security headers."""

import pytest
from fastapi.testclient import TestClient


class TestSecurityHeaders:
    """Test suite for security headers middleware."""

    def test_x_frame_options_header(self, client: TestClient):
        """Test X-Frame-Options header is present and set to DENY."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.headers.get("X-Frame-Options") == "DENY"

    def test_x_content_type_options_header(self, client: TestClient):
        """Test X-Content-Type-Options header is present and set to nosniff."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_hsts_header(self, client: TestClient):
        """Test Strict-Transport-Security (HSTS) header is present."""
        response = client.get("/health")
        
        assert response.status_code == 200
        hsts = response.headers.get("Strict-Transport-Security")
        assert hsts is not None
        assert "max-age=31536000" in hsts
        assert "includeSubDomains" in hsts

    def test_referrer_policy_header(self, client: TestClient):
        """Test Referrer-Policy header is present."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_permissions_policy_header(self, client: TestClient):
        """Test Permissions-Policy header is present."""
        response = client.get("/health")
        
        assert response.status_code == 200
        permissions = response.headers.get("Permissions-Policy")
        assert permissions is not None
        assert "geolocation=()" in permissions
        assert "microphone=()" in permissions
        assert "camera=()" in permissions

    def test_csp_header(self, client: TestClient):
        """Test Content-Security-Policy header is present and properly configured."""
        response = client.get("/health")
        
        assert response.status_code == 200
        csp = response.headers.get("Content-Security-Policy")
        assert csp is not None
        
        # Check CSP directives
        assert "default-src 'self'" in csp
        assert "script-src 'self' https://cdnjs.cloudflare.com" in csp
        # 'unsafe-inline' should NOT be in script-src
        assert "'unsafe-inline'" not in csp.split("script-src")[1].split("style-src")[0] if "style-src" in csp else "'unsafe-inline'" not in csp.split("script-src")[1]
        assert "style-src 'self' https://fonts.googleapis.com" in csp
        assert "font-src 'self' https://fonts.gstatic.com" in csp
        assert "img-src 'self' data: https:" in csp
        assert "connect-src 'self'" in csp

    def test_csp_no_unsafe_inline_in_scripts(self, client: TestClient):
        """Test CSP does not allow unsafe-inline for scripts (XSS prevention)."""
        response = client.get("/health")
        
        assert response.status_code == 200
        csp = response.headers.get("Content-Security-Policy", "")
        
        # Extract script-src directive
        script_src_part = csp.split("script-src ")[1] if "script-src " in csp else ""
        if "style-src" in script_src_part:
            script_src_part = script_src_part.split("style-src")[0]
        
        # Should NOT contain 'unsafe-inline' (which would allow inline scripts)
        assert "'unsafe-inline'" not in script_src_part, "CSP should not allow 'unsafe-inline' for scripts"
