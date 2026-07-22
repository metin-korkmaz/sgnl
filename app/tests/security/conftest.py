"""
Security test fixtures and utilities.

Provides reusable fixtures for SSRF testing, API key testing,
and other security-related test scenarios.
"""

import pytest
from typing import List, Dict, Any, Tuple


# =============================================================================
# URL Validation Fixtures (SSRF Protection)
# =============================================================================

@pytest.fixture
def blocked_private_ips() -> List[str]:
    """
    Fixture providing private/internal IP addresses that should be blocked.
    These are SSRF attack vectors.
    """
    return [
        # IPv4 private ranges
        "http://127.0.0.1",
        "http://127.0.0.1:8080",
        "https://127.0.0.1/path",
        "http://10.0.0.1",
        "http://10.255.255.255",
        "http://172.16.0.1",
        "http://172.31.255.255",
        "http://192.168.0.1",
        "http://192.168.255.255",
        "http://0.0.0.0",
        "http://localhost",
        "http://localhost:3000",
        "https://localhost/path/to/resource",
        "http://[::1]",  # IPv6 localhost
        "http://[::1]:8080",
        "http://169.254.169.254",  # Link-local
        # With credentials
        "http://user:pass@127.0.0.1",
        "http://user:pass@localhost",
    ]


@pytest.fixture
def blocked_metadata_endpoints() -> List[str]:
    """
    Fixture providing cloud metadata service endpoints that should be blocked.
    These are common SSRF targets for credential theft.
    """
    return [
        # AWS
        "http://169.254.169.254/latest/meta-data/",
        "http://169.254.169.254/latest/user-data/",
        "http://169.254.169.254/latest/dynamic/instance-identity/",
        "http://169.254.169.254/1.0/meta-data/",
        # GCP
        "http://169.254.169.254/computeMetadata/v1/",
        "http://metadata.google.internal/",
        "http://metadata.google.internal/computeMetadata/v1/",
        # Azure
        "http://169.254.169.254/metadata/instance/",
        # Alibaba Cloud
        "http://100.100.100.200/latest/meta-data/",
        # Oracle Cloud
        "http://169.254.169.254/opc/v1/",
        # OpenStack
        "http://169.254.169.254/openstack/",
    ]


@pytest.fixture
def blocked_internal_services() -> List[str]:
    """
    Fixture providing internal service URLs that should be blocked.
    These could expose internal infrastructure.
    """
    return [
        # Kubernetes/Docker internal
        "http://kubernetes.default",
        "http://kubernetes.default.svc",
        "http://kubernetes.default.svc.cluster.local",
        "http://kube-dns.kube-system.svc.cluster.local",
        "http://docker.socket",
        "http://containerd.sock",
        # Common internal services
        "http://consul:8500",
        "http://etcd:2379",
        "http://redis:6379",
        "http://postgres:5432",
        "http://mysql:3306",
        "http://mongodb:27017",
        "http://elasticsearch:9200",
        "http://kibana:5601",
        "http://grafana:3000",
        "http://prometheus:9090",
    ]


@pytest.fixture
def blocked_suspicious_patterns() -> List[str]:
    """
    Fixture providing URLs with suspicious patterns that should be blocked.
    These may indicate attempted bypasses or attacks.
    """
    return [
        # IP bypass attempts
        "http://0177.0.0.1",  # Octal encoding
        "http://0x7f.0.0.1",  # Hex encoding
        "http://2130706433",  # Decimal encoding
        "http://0x7f000001",  # Hex single value
        "http://127.0.0.1.xip.io",  # DNS rebinding
        "http://127.0.0.1.nip.io",
        "http://make-127-0-0-1-rr.1d.tl",
        # Path traversal
        "http://example.com/../etc/passwd",
        "http://example.com/..%2f..%2fetc%2fpasswd",
        "http://example.com/../../../etc/passwd",
        # Null byte injection
        "http://example.com%00.evil.com",
        # Protocol smuggling
        "http://example.com@127.0.0.1",
        "http://example.com:80@127.0.0.1:8080",
        # File protocol
        "file:///etc/passwd",
        "file://localhost/etc/passwd",
        # Gopher protocol
        "gopher://127.0.0.1:6379/_*1%0d%0a$8%0d%0aflushall%0d%0a",
    ]


@pytest.fixture
def valid_public_urls() -> List[str]:
    """
    Fixture providing valid public URLs that should be allowed.
    These are legitimate external URLs.
    """
    return [
        "https://example.com",
        "https://www.example.com",
        "https://example.com/path/to/resource",
        "https://example.com:443/page",
        "https://subdomain.example.com",
        "https://api.github.com/repos/example/repo",
        "https://raw.githubusercontent.com/user/repo/main/file.md",
        "https://arxiv.org/abs/1234.56789",
        "https://www.nature.com/articles/example",
        "https://huggingface.co/datasets/example",
        "https://deepmind.google/research/publications",
        "https://distill.pub/2021/example",
    ]


@pytest.fixture
def url_test_cases() -> Dict[str, List[Tuple[str, bool, str]]]:
    """
    Fixture providing comprehensive URL test cases with expected results.
    Format: [(url, should_be_allowed, reason), ...]
    """
    return {
        "private_ips": [
            ("http://127.0.0.1", False, "localhost IPv4"),
            ("http://10.0.0.1", False, "private 10.x.x.x"),
            ("http://172.16.0.1", False, "private 172.16.x.x"),
            ("http://192.168.0.1", False, "private 192.168.x.x"),
            ("http://0.0.0.0", False, "broadcast address"),
            ("http://localhost", False, "localhost hostname"),
            ("http://[::1]", False, "IPv6 localhost"),
        ],
        "metadata_services": [
            ("http://169.254.169.254/latest/meta-data/", False, "AWS metadata"),
            ("http://metadata.google.internal/", False, "GCP metadata"),
        ],
        "internal_services": [
            ("http://kubernetes.default", False, "K8s internal"),
            ("http://consul:8500", False, "Consul service"),
        ],
        "valid_urls": [
            ("https://example.com", True, "public domain"),
            ("https://github.com/user/repo", True, "public GitHub"),
        ],
    }


# =============================================================================
# API Key Fixtures
# =============================================================================

@pytest.fixture
def valid_api_key() -> str:
    """
    Fixture providing a valid API key format.
    """
    return "sgnl_live_abcdefghijklmnopqrstuvwxyz123456"


@pytest.fixture
def valid_api_keys() -> List[str]:
    """
    Fixture providing multiple valid API key formats.
    """
    return [
        "sgnl_live_abcdefghijklmnopqrstuvwxyz123456",
        "sgnl_test_abcdefghijklmnopqrstuvwxyz123456",
        "sgnl_live_1234567890abcdefghijklmnopqr",
        "sgnl_live_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456",
    ]


@pytest.fixture
def invalid_api_keys() -> List[Tuple[str, str]]:
    """
    Fixture providing invalid API keys with reasons.
    Format: [(key, reason), ...]
    """
    return [
        ("", "empty string"),
        ("invalid", "too short"),
        ("sgnl_live_", "missing key part"),
        ("sgnl_live_123", "too short key"),
        ("SGNL_LIVE_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456", "wrong prefix case"),
        ("wrong_live_abcdefghijklmnopqrstuvwxyz123456", "wrong prefix"),
        ("sgnl_invalid_abcdefghijklmnopqrstuvwxyz123456", "wrong environment"),
        ("sgnl_live_abcdefghijklmnopqrstuvwxyz123456\n", "newline in key"),
        ("sgnl_live_abcdefghijklmnopqrstuvwxyz 123456", "space in key"),
        ("sgnl_live_abcdefghijklmnopqrstuvwxyz\t123456", "tab in key"),
        ("sgnl_live_abc!@#$%^&*()_+-=[]{}|;':\",./<>?", "special chars"),
    ]


@pytest.fixture
def api_key_headers() -> Dict[str, str]:
    """
    Fixture providing valid API key headers.
    """
    return {
        "Authorization": "Bearer sgnl_live_abcdefghijklmnopqrstuvwxyz123456",
        "X-API-Key": "sgnl_live_abcdefghijklmnopqrstuvwxyz123456",
    }


# =============================================================================
# SSRF Attack Vectors
# =============================================================================

@pytest.fixture
def ssrf_attack_vectors() -> List[Dict[str, Any]]:
    """
    Fixture providing SSRF attack vectors with expected behaviors.
    Each entry contains: url, attack_type, description, expected_blocked
    """
    return [
        {
            "url": "http://169.254.169.254/latest/meta-data/",
            "attack_type": "metadata_service",
            "description": "AWS metadata service access",
            "expected_blocked": True,
        },
        {
            "url": "http://127.0.0.1/admin",
            "attack_type": "local_service",
            "description": "Access to localhost admin panel",
            "expected_blocked": True,
        },
        {
            "url": "http://0x7f.0.0.1",
            "attack_type": "ip_encoding",
            "description": "Hex-encoded localhost",
            "expected_blocked": True,
        },
        {
            "url": "http://2130706433",
            "attack_type": "ip_encoding",
            "description": "Decimal-encoded localhost",
            "expected_blocked": True,
        },
        {
            "url": "http://127.0.0.1.nip.io",
            "attack_type": "dns_rebinding",
            "description": "DNS rebinding to localhost",
            "expected_blocked": True,
        },
        {
            "url": "file:///etc/passwd",
            "attack_type": "file_inclusion",
            "description": "Local file inclusion",
            "expected_blocked": True,
        },
        {
            "url": "https://example.com",
            "attack_type": "none",
            "description": "Valid public URL",
            "expected_blocked": False,
        },
    ]


# =============================================================================
# Test Helper Functions
# =============================================================================

@pytest.fixture
def security_test_helpers():
    """
    Fixture providing helper functions for security testing.
    """
    def is_private_ip(ip: str) -> bool:
        """Check if IP is in private ranges."""
        try:
            import ipaddress
            addr = ipaddress.ip_address(ip)
            return addr.is_private or addr.is_loopback or addr.is_link_local
        except ValueError:
            return False

    def is_internal_hostname(hostname: str) -> bool:
        """Check if hostname is internal."""
        internal_suffixes = [
            ".local",
            ".internal",
            ".svc.cluster.local",
            ".default.svc.cluster.local",
            ".kube-system.svc.cluster.local",
        ]
        return any(hostname.endswith(suffix) for suffix in internal_suffixes)

    def is_metadata_endpoint(url: str) -> bool:
        """Check if URL is a metadata service endpoint."""
        metadata_patterns = [
            "169.254.169.254",
            "metadata.google.internal",
            "100.100.100.200",
        ]
        return any(pattern in url for pattern in metadata_patterns)

    return {
        "is_private_ip": is_private_ip,
        "is_internal_hostname": is_internal_hostname,
        "is_metadata_endpoint": is_metadata_endpoint,
    }


# =============================================================================
# Rate Limiting Fixtures
# =============================================================================

@pytest.fixture
def rate_limit_test_cases() -> List[Dict[str, Any]]:
    """
    Fixture providing rate limiting test scenarios.
    """
    return [
        {
            "name": "single_request",
            "requests": 1,
            "window_seconds": 60,
            "expected_allowed": True,
        },
        {
            "name": "at_limit",
            "requests": 3,
            "window_seconds": 60,
            "expected_allowed": True,
        },
        {
            "name": "over_limit",
            "requests": 4,
            "window_seconds": 60,
            "expected_allowed": False,
        },
    ]


# =============================================================================
# Environment Fixtures
# =============================================================================

@pytest.fixture
def secure_test_env(monkeypatch):
    """
    Fixture providing a secure test environment.
    Sets secure defaults for environment variables.
    """
    # Set secure defaults
    monkeypatch.setenv("RATE_LIMIT", "3")
    monkeypatch.setenv("RATE_WINDOW_SECONDS", "60")
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://example.com")
    monkeypatch.setenv("DENSITY_THRESHOLD", "0.45")
    monkeypatch.setenv("LLM_MAX_CHARS", "12000")

    yield

    # Cleanup is handled automatically by monkeypatch
