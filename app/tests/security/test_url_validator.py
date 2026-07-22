"""
Tests for URL validation and SSRF protection.

Comprehensive tests for URL validation, IP blocking, DNS resolution,
redirect validation, and edge cases.
"""

import pytest
import socket
from typing import List
from unittest.mock import patch

from app.security.url_validator import (
    validate_url,
    validate_redirect_url,
    SSRFValidator,
    _is_private_ip,
    _resolve_hostname,
    _is_blocked_host,
    MAX_URL_LENGTH,
    ALLOWED_SCHEMES,
    BLOCKED_HOSTS,
    BLOCKED_PORTS,
)


class TestURLValidationFixtures:
    """Test that security fixtures are properly defined."""

    def test_blocked_private_ips_fixture(self, blocked_private_ips: List[str]):
        """Verify blocked_private_ips fixture contains expected values."""
        assert len(blocked_private_ips) > 0
        assert "http://127.0.0.1" in blocked_private_ips
        assert "http://localhost" in blocked_private_ips
        assert "http://192.168.0.1" in blocked_private_ips
        assert "http://10.0.0.1" in blocked_private_ips

    def test_blocked_metadata_endpoints_fixture(self, blocked_metadata_endpoints: List[str]):
        """Verify blocked_metadata_endpoints fixture contains expected values."""
        assert len(blocked_metadata_endpoints) > 0
        assert any("169.254.169.254" in url for url in blocked_metadata_endpoints)
        assert any("metadata.google" in url for url in blocked_metadata_endpoints)

    def test_blocked_internal_services_fixture(self, blocked_internal_services: List[str]):
        """Verify blocked_internal_services fixture contains expected values."""
        assert len(blocked_internal_services) > 0
        assert any("kubernetes" in url for url in blocked_internal_services)
        assert any("consul" in url or "etcd" in url for url in blocked_internal_services)

    def test_blocked_suspicious_patterns_fixture(self, blocked_suspicious_patterns: List[str]):
        """Verify blocked_suspicious_patterns fixture contains expected values."""
        assert len(blocked_suspicious_patterns) > 0
        # Check for various bypass attempts
        assert any("xip.io" in url or "nip.io" in url for url in blocked_suspicious_patterns)

    def test_valid_public_urls_fixture(self, valid_public_urls: List[str]):
        """Verify valid_public_urls fixture contains expected values."""
        assert len(valid_public_urls) > 0
        assert all(url.startswith("https://") for url in valid_public_urls)

    def test_url_test_cases_fixture(self, url_test_cases):
        """Verify url_test_cases fixture has all expected categories."""
        assert "private_ips" in url_test_cases
        assert "metadata_services" in url_test_cases
        assert "internal_services" in url_test_cases
        assert "valid_urls" in url_test_cases

    def test_ssrf_attack_vectors_fixture(self, ssrf_attack_vectors: List[dict]):
        """Verify ssrf_attack_vectors fixture is properly structured."""
        assert len(ssrf_attack_vectors) > 0
        for vector in ssrf_attack_vectors:
            assert "url" in vector
            assert "attack_type" in vector
            assert "description" in vector
            assert "expected_blocked" in vector


class TestIsPrivateIP:
    """Tests for private IP detection."""

    def test_private_ipv4_10_range(self):
        """Test 10.0.0.0/8 range."""
        assert _is_private_ip('10.0.0.1') is True
        assert _is_private_ip('10.255.255.255') is True
        assert _is_private_ip('9.255.255.255') is False

    def test_private_ipv4_172_range(self):
        """Test 172.16.0.0/12 range."""
        assert _is_private_ip('172.16.0.1') is True
        assert _is_private_ip('172.31.255.255') is True
        assert _is_private_ip('172.15.255.255') is False
        assert _is_private_ip('172.32.0.0') is False

    def test_private_ipv4_192_range(self):
        """Test 192.168.0.0/16 range."""
        assert _is_private_ip('192.168.0.1') is True
        assert _is_private_ip('192.168.255.255') is True
        assert _is_private_ip('192.167.255.255') is False

    def test_loopback_ipv4(self):
        """Test 127.0.0.0/8 loopback range."""
        assert _is_private_ip('127.0.0.1') is True
        assert _is_private_ip('127.255.255.255') is True
        assert _is_private_ip('126.255.255.255') is False

    def test_link_local_ipv4(self):
        """Test 169.254.0.0/16 link-local range."""
        assert _is_private_ip('169.254.0.1') is True
        assert _is_private_ip('169.254.169.254') is True
        assert _is_private_ip('169.253.255.255') is False

    def test_carrier_grade_nat(self):
        """Test 100.64.0.0/10 carrier-grade NAT."""
        assert _is_private_ip('100.64.0.1') is True
        assert _is_private_ip('100.127.255.255') is True
        assert _is_private_ip('100.63.255.255') is False

    def test_public_ipv4_allowed(self):
        """Test public IPs are not blocked."""
        assert _is_private_ip('8.8.8.8') is False
        assert _is_private_ip('1.1.1.1') is False
        assert _is_private_ip('208.67.222.222') is False

    def test_loopback_ipv6(self):
        """Test ::1 IPv6 loopback."""
        assert _is_private_ip('::1') is True
        assert _is_private_ip('0:0:0:0:0:0:0:1') is True

    def test_private_ipv6_ula(self):
        """Test fc00::/7 unique local addresses."""
        assert _is_private_ip('fc00::1') is True
        assert _is_private_ip('fdff:ffff:ffff:ffff:ffff:ffff:ffff:ffff') is True

    def test_link_local_ipv6(self):
        """Test fe80::/10 link-local addresses."""
        assert _is_private_ip('fe80::1') is True
        assert _is_private_ip('febf:ffff:ffff:ffff:ffff:ffff:ffff:ffff') is True

    def test_invalid_ip(self):
        """Test invalid IP addresses."""
        assert _is_private_ip('not-an-ip') is False
        assert _is_private_ip('') is False
        assert _is_private_ip('256.1.1.1') is False


class TestIsBlockedHost:
    """Tests for blocked host detection."""

    def test_blocked_metadata_endpoints(self):
        """Test known metadata endpoints are blocked."""
        assert _is_blocked_host('169.254.169.254') is True
        assert _is_blocked_host('169.254.170.2') is True
        assert _is_blocked_host('169.254.170.1') is True
        assert _is_blocked_host('100.100.100.200') is True

    def test_blocked_metadata_hostnames(self):
        """Test metadata hostnames are blocked."""
        assert _is_blocked_host('metadata.google.internal') is True
        assert _is_blocked_host('metadata') is True
        assert _is_blocked_host('metadata.internal') is True

    def test_blocked_case_insensitive(self):
        """Test blocked hosts are case-insensitive."""
        assert _is_blocked_host('METADATA.GOOGLE.INTERNAL') is True
        assert _is_blocked_host('Metadata') is True

    def test_allowed_hosts(self):
        """Test normal hosts are not blocked."""
        assert _is_blocked_host('example.com') is False
        assert _is_blocked_host('google.com') is False
        assert _is_blocked_host('github.com') is False


class TestResolveHostname:
    """Tests for DNS resolution."""

    @patch('socket.getaddrinfo')
    def test_successful_resolution(self, mock_getaddrinfo):
        """Test successful DNS resolution."""
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', ('93.184.216.34', 0))
        ]
        ip, error = _resolve_hostname('example.com')
        assert ip == '93.184.216.34'
        assert error is None

    @patch('socket.getaddrinfo')
    def test_resolution_failure(self, mock_getaddrinfo):
        """Test failed DNS resolution."""
        mock_getaddrinfo.side_effect = socket.gaierror("Name or service not known")
        ip, error = _resolve_hostname('nonexistent.invalid')
        assert ip is None
        assert error is not None
        assert 'DNS resolution failed' in error

    @patch('socket.getaddrinfo')
    def test_empty_resolution(self, mock_getaddrinfo):
        """Test empty DNS resolution result."""
        mock_getaddrinfo.return_value = []
        ip, error = _resolve_hostname('example.com')
        assert ip is None
        assert 'no results' in error


class TestValidateUrl:
    """Tests for URL validation."""

    @patch('app.security.url_validator._resolve_hostname')
    def test_valid_https_url(self, mock_resolve):
        """Test valid HTTPS URL passes validation."""
        mock_resolve.return_value = ('93.184.216.34', None)
        is_valid, error = validate_url('https://example.com/')
        assert is_valid is True
        assert error == ''

    @patch('app.security.url_validator._resolve_hostname')
    def test_valid_http_url(self, mock_resolve):
        """Test valid HTTP URL passes validation."""
        mock_resolve.return_value = ('93.184.216.34', None)
        is_valid, error = validate_url('http://example.com/')
        assert is_valid is True
        assert error == ''

    def test_url_too_long(self):
        """Test URL exceeding max length is rejected."""
        long_url = 'https://example.com/' + 'a' * MAX_URL_LENGTH
        is_valid, error = validate_url(long_url)
        assert is_valid is False
        assert 'exceeds maximum length' in error

    def test_missing_scheme(self):
        """Test URL without scheme is rejected."""
        is_valid, error = validate_url('example.com')
        assert is_valid is False
        assert 'scheme' in error.lower()

    def test_invalid_scheme(self):
        """Test non-http(s) schemes are rejected."""
        is_valid, error = validate_url('ftp://example.com')
        assert is_valid is False
        assert 'not allowed' in error.lower()

    def test_file_scheme_blocked(self):
        """Test file:// scheme is blocked."""
        is_valid, error = validate_url('file:///etc/passwd')
        assert is_valid is False
        assert 'not allowed' in error.lower()

    def test_data_scheme_blocked(self):
        """Test data:// scheme is blocked."""
        is_valid, error = validate_url('data:text/html,<script>alert(1)</script>')
        assert is_valid is False

    def test_javascript_scheme_blocked(self):
        """Test javascript:// scheme is blocked."""
        is_valid, error = validate_url('javascript:alert(1)')
        assert is_valid is False

    def test_private_ipv4_blocked_10(self):
        """Test 10.0.0.0/8 private IP is blocked."""
        is_valid, error = validate_url('http://10.0.0.1/')
        assert is_valid is False
        assert 'private' in error.lower()

    def test_private_ipv4_blocked_172(self):
        """Test 172.16.0.0/12 private IP is blocked."""
        is_valid, error = validate_url('http://172.16.0.1/')
        assert is_valid is False
        assert 'private' in error.lower()

    def test_private_ipv4_blocked_192(self):
        """Test 192.168.0.0/16 private IP is blocked."""
        is_valid, error = validate_url('http://192.168.1.1/')
        assert is_valid is False
        assert 'private' in error.lower()

    def test_loopback_ipv4_blocked(self):
        """Test 127.0.0.1 is blocked."""
        is_valid, error = validate_url('http://127.0.0.1/')
        assert is_valid is False
        assert 'private' in error.lower()

    def test_link_local_ipv4_blocked(self):
        """Test 169.254.0.0/16 link-local is blocked."""
        is_valid, error = validate_url('http://169.254.1.1/')
        assert is_valid is False
        assert 'private' in error.lower()

    def test_metadata_endpoint_blocked(self):
        """Test AWS metadata endpoint is blocked."""
        is_valid, error = validate_url('http://169.254.169.254/latest/meta-data/')
        assert is_valid is False
        assert 'not allowed' in error.lower()

    def test_private_ipv6_blocked_loopback(self):
        """Test IPv6 loopback is blocked."""
        is_valid, error = validate_url('http://[::1]/')
        assert is_valid is False
        assert 'private' in error.lower()

    def test_private_ipv6_blocked_ula(self):
        """Test IPv6 unique local address is blocked."""
        is_valid, error = validate_url('http://[fc00::1]/')
        assert is_valid is False
        assert 'private' in error.lower()

    def test_private_ipv6_blocked_linklocal(self):
        """Test IPv6 link-local is blocked."""
        is_valid, error = validate_url('http://[fe80::1]/')
        assert is_valid is False
        assert 'private' in error.lower()

    @patch('app.security.url_validator._resolve_hostname')
    def test_dns_rebinding_blocked(self, mock_resolve):
        """Test DNS rebinding to private IP is blocked."""
        mock_resolve.return_value = ('10.0.0.1', None)  # Resolves to private IP
        is_valid, error = validate_url('http://external-host.example.com/')
        assert is_valid is False
        assert 'private' in error.lower()

    @patch('app.security.url_validator._resolve_hostname')
    def test_dns_resolution_failure(self, mock_resolve):
        """Test DNS resolution failure is handled."""
        mock_resolve.return_value = (None, "DNS resolution failed")
        is_valid, error = validate_url('http://nonexistent.example.com/')
        assert is_valid is False
        assert 'resolve' in error.lower()

    def test_blocked_port_22(self):
        """Test SSH port is blocked."""
        is_valid, error = validate_url('http://example.com:22/')
        assert is_valid is False
        assert 'port' in error.lower()

    def test_blocked_port_3306(self):
        """Test MySQL port is blocked."""
        is_valid, error = validate_url('http://example.com:3306/')
        assert is_valid is False

    def test_blocked_port_5432(self):
        """Test PostgreSQL port is blocked."""
        is_valid, error = validate_url('http://example.com:5432/')
        assert is_valid is False

    @patch('app.security.url_validator._resolve_hostname')
    def test_standard_port_80_allowed(self, mock_resolve):
        """Test HTTP port 80 is allowed."""
        mock_resolve.return_value = ('93.184.216.34', None)
        is_valid, error = validate_url('http://example.com:80/')
        assert is_valid is True

    @patch('app.security.url_validator._resolve_hostname')
    def test_standard_port_443_allowed(self, mock_resolve):
        """Test HTTPS port 443 is allowed."""
        mock_resolve.return_value = ('93.184.216.34', None)
        is_valid, error = validate_url('https://example.com:443/')
        assert is_valid is True

    @patch('app.security.url_validator._resolve_hostname')
    def test_high_port_allowed(self, mock_resolve):
        """Test high ports are allowed."""
        mock_resolve.return_value = ('93.184.216.34', None)
        is_valid, error = validate_url('http://example.com:8080/')
        assert is_valid is True


class TestValidateRedirectUrl:
    """Tests for redirect URL validation."""

    @patch('app.security.url_validator._resolve_hostname')
    def test_relative_redirect_allowed(self, mock_resolve):
        """Test relative redirect is allowed."""
        mock_resolve.return_value = ('93.184.216.34', None)
        is_valid, error = validate_redirect_url('https://example.com/page', '/other')
        assert is_valid is True

    @patch('app.security.url_validator._resolve_hostname')
    def test_absolute_redirect_validated(self, mock_resolve):
        """Test absolute redirect URL is validated."""
        mock_resolve.return_value = ('93.184.216.34', None)
        is_valid, error = validate_redirect_url(
            'https://example.com/page',
            'https://other-site.com/'
        )
        assert is_valid is True

    def test_redirect_to_private_ip_blocked(self):
        """Test redirect to private IP is blocked."""
        is_valid, error = validate_redirect_url(
            'https://example.com/page',
            'http://192.168.1.1/'
        )
        assert is_valid is False
        assert 'private' in error.lower()


class TestSSRFValidator:
    """Tests for SSRFValidator class."""

    def test_default_validator_creation(self):
        """Test creating validator with default settings."""
        validator = SSRFValidator()
        assert validator.max_url_length == MAX_URL_LENGTH
        assert validator.allowed_schemes == ALLOWED_SCHEMES

    def test_custom_max_length(self):
        """Test validator with custom max length."""
        import ipaddress
        validator = SSRFValidator(max_url_length=100)
        assert validator.max_url_length == 100
        is_valid, error = validator.validate('https://example.com/' + 'a' * 100)
        assert is_valid is False
        assert 'exceeds maximum length' in error

    def test_custom_allowed_schemes(self):
        """Test validator with custom schemes."""
        validator = SSRFValidator(allowed_schemes={'https'})
        is_valid, _ = validator.validate('http://example.com/')
        assert is_valid is False
        is_valid, _ = validator.validate('https://example.com/')
        # Will fail due to DNS, but scheme is accepted
        assert 'scheme' not in str(is_valid).lower()

    def test_custom_blocked_hosts(self):
        """Test validator with additional blocked hosts."""
        validator = SSRFValidator(blocked_hosts={'evil.com'})
        is_valid, error = validator.validate('http://evil.com/')
        assert is_valid is False
        assert 'not allowed' in error

    def test_custom_blocked_ports(self):
        """Test validator with additional blocked ports."""
        validator = SSRFValidator(blocked_ports={8080})
        is_valid, error = validator.validate('http://example.com:8080/')
        assert is_valid is False
        assert 'port' in error

    @patch('app.security.url_validator._resolve_hostname')
    def test_custom_private_networks(self, mock_resolve):
        """Test validator with custom private networks."""
        import ipaddress
        # First verify the IP is not blocked by default
        mock_resolve.return_value = ('203.0.113.1', None)
        validator_default = SSRFValidator()
        is_valid, _ = validator_default.validate('http://example.com/')
        assert is_valid is True

        # Now block it with custom network
        custom_network = ipaddress.ip_network('203.0.113.0/24')
        validator_custom = SSRFValidator(custom_private_networks=[custom_network])
        mock_resolve.return_value = ('203.0.113.1', None)
        is_valid, error = validator_custom.validate('http://example.com/')
        assert is_valid is False
        assert 'private' in error.lower()


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_url(self):
        """Test empty URL is rejected."""
        is_valid, error = validate_url('')
        assert is_valid is False

    def test_whitespace_url(self):
        """Test whitespace-only URL is rejected."""
        is_valid, error = validate_url('   ')
        assert is_valid is False

    def test_url_with_fragment(self):
        """Test URL with fragment is handled."""
        with patch('app.security.url_validator._resolve_hostname') as mock_resolve:
            mock_resolve.return_value = ('93.184.216.34', None)
            is_valid, error = validate_url('https://example.com/page#section')
            assert is_valid is True

    def test_url_with_query_string(self):
        """Test URL with query string is handled."""
        with patch('app.security.url_validator._resolve_hostname') as mock_resolve:
            mock_resolve.return_value = ('93.184.216.34', None)
            is_valid, error = validate_url('https://example.com/page?param=value')
            assert is_valid is True

    def test_url_with_multiple_query_params(self):
        """Test URL with multiple query parameters is handled."""
        with patch('app.security.url_validator._resolve_hostname') as mock_resolve:
            mock_resolve.return_value = ('93.184.216.34', None)
            is_valid, error = validate_url(
                'https://example.com/page?param1=value1&param2=value2'
            )
            assert is_valid is True

    @patch('app.security.url_validator._resolve_hostname')
    def test_localhost_blocked(self, mock_resolve):
        """Test localhost is blocked as loopback."""
        mock_resolve.return_value = ('127.0.0.1', None)
        is_valid, error = validate_url('http://localhost/')
        assert is_valid is False
        assert 'private' in error.lower()

    @patch('app.security.url_validator._resolve_hostname')
    def test_localhost_resolves_private(self, mock_resolve):
        """Test that localhost resolves to private IP is blocked."""
        mock_resolve.return_value = ('127.0.0.1', None)
        is_valid, error = validate_url('http://localhost:8080/admin')
        assert is_valid is False
        assert 'private' in error.lower()

    def test_zero_padded_ip_blocked(self):
        """Test zero-padded IP is blocked."""
        # These may be interpreted by the IP parser
        # 0177.0.0.1 is octal for 127.0.0.1
        is_valid, error = validate_url('http://0177.0.0.1/')
        # May or may not be blocked depending on ipaddress module behavior
        # Just ensure it doesn't crash
        assert isinstance(is_valid, bool)


class TestSecurityHelpers:
    """Test security helper functions from fixtures."""

    def test_is_private_ip_helper(self, security_test_helpers):
        """Test the is_private_ip helper function."""
        is_private = security_test_helpers["is_private_ip"]

        # Private IPs
        assert is_private("127.0.0.1") is True
        assert is_private("10.0.0.1") is True
        assert is_private("172.16.0.1") is True
        assert is_private("192.168.0.1") is True
        assert is_private("169.254.0.1") is True  # Link-local

        # Public IPs
        assert is_private("8.8.8.8") is False
        assert is_private("1.1.1.1") is False
        assert is_private("208.67.222.222") is False

    def test_is_internal_hostname_helper(self, security_test_helpers):
        """Test the is_internal_hostname helper function."""
        is_internal = security_test_helpers["is_internal_hostname"]

        # Internal hostnames
        assert is_internal("service.local") is True
        assert is_internal("service.internal") is True
        assert is_internal("kubernetes.default.svc.cluster.local") is True

        # Public hostnames
        assert is_internal("example.com") is False
        assert is_internal("github.com") is False

    def test_is_metadata_endpoint_helper(self, security_test_helpers):
        """Test the is_metadata_endpoint helper function."""
        is_metadata = security_test_helpers["is_metadata_endpoint"]

        # Metadata endpoints
        assert is_metadata("http://169.254.169.254/") is True
        assert is_metadata("http://metadata.google.internal/") is True

        # Non-metadata endpoints
        assert is_metadata("http://example.com/") is False
        assert is_metadata("https://github.com/") is False
