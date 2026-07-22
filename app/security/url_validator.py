"""
SSRF URL Validator Module

Prevents Server-Side Request Forgery (SSRF) attacks by validating URLs
before they are fetched. Blocks private IP ranges, metadata endpoints,
and validates DNS resolution to prevent DNS rebinding attacks.
"""

import ipaddress
import logging
import re
import socket
from typing import Tuple, Optional, Set
from urllib.parse import urlparse, urlsplit

logger = logging.getLogger(__name__)

# Maximum URL length (Chrome/Edge standard)
MAX_URL_LENGTH = 2048

# Allowed schemes
ALLOWED_SCHEMES = {'http', 'https'}

# Private IPv4 ranges (RFC 1918 + loopback + link-local + carrier-grade NAT)
PRIVATE_IPV4_NETWORKS = [
    ipaddress.ip_network('10.0.0.0/8'),      # RFC 1918 - Private
    ipaddress.ip_network('172.16.0.0/12'),   # RFC 1918 - Private
    ipaddress.ip_network('192.168.0.0/16'),  # RFC 1918 - Private
    ipaddress.ip_network('127.0.0.0/8'),     # Loopback
    ipaddress.ip_network('169.254.0.0/16'),  # Link-local (includes metadata)
    ipaddress.ip_network('100.64.0.0/10'),   # Carrier-grade NAT
]

# Private IPv6 ranges
PRIVATE_IPV6_NETWORKS = [
    ipaddress.ip_network('::1/128'),         # Loopback
    ipaddress.ip_network('fc00::/7'),        # Unique local (ULA)
    ipaddress.ip_network('fe80::/10'),       # Link-local
]

# Cloud metadata endpoints that should be blocked
BLOCKED_HOSTS: Set[str] = {
    '169.254.169.254',       # AWS, GCP, Azure metadata
    '169.254.170.2',         # AWS ECS task metadata
    '169.254.170.1',         # AWS ECS credentials
    '100.100.100.200',       # Alibaba Cloud metadata
    'metadata.google.internal',  # GCP metadata
    'metadata',              # Short hostname often used
    'metadata.internal',     # Internal metadata
}

# Additional sensitive ports to block
BLOCKED_PORTS = {22, 23, 25, 53, 110, 143, 3389, 3306, 5432, 6379, 27017}


def _is_private_ip(ip_str: str) -> bool:
    """
    Check if an IP address is in a private/special range.

    Args:
        ip_str: IP address string (IPv4 or IPv6)

    Returns:
        True if IP is private/special, False otherwise
    """
    try:
        ip = ipaddress.ip_address(ip_str)

        # Check IPv4 private networks
        if isinstance(ip, ipaddress.IPv4Address):
            for network in PRIVATE_IPV4_NETWORKS:
                if ip in network:
                    return True

        # Check IPv6 private networks
        if isinstance(ip, ipaddress.IPv6Address):
            for network in PRIVATE_IPV6_NETWORKS:
                if ip in network:
                    return True

        return False
    except ValueError:
        return False


def _resolve_hostname(hostname: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Resolve a hostname to its IP address.

    Args:
        hostname: The hostname to resolve

    Returns:
        Tuple of (ip_address, error_message). ip_address is None if resolution fails.
    """
    try:
        # Getaddrinfo supports both IPv4 and IPv6
        result = socket.getaddrinfo(hostname, None)
        if result:
            # Get the first resolved IP
            ip = result[0][4][0]
            return ip, None
        return None, "DNS resolution returned no results"
    except socket.gaierror as e:
        return None, f"DNS resolution failed: {str(e)}"
    except Exception as e:
        return None, f"DNS resolution error: {str(e)}"


def _is_blocked_host(hostname: str) -> bool:
    """
    Check if hostname is in the blocked hosts list.

    Args:
        hostname: Hostname to check

    Returns:
        True if blocked, False otherwise
    """
    hostname_lower = hostname.lower()

    # Direct match against known metadata endpoints
    if hostname_lower in BLOCKED_HOSTS:
        return True

    return False


def validate_url(url: str) -> Tuple[bool, str]:
    """
    Validate a URL for SSRF protection.

    Performs comprehensive validation including:
    - URL format and length validation
    - Scheme validation (only http/https)
    - IP address validation (blocks private ranges)
    - DNS resolution and re-validation (prevents DNS rebinding)
    - Blocked host validation (metadata endpoints)
    - Port validation

    Args:
        url: The URL to validate

    Returns:
        Tuple of (is_valid, error_message). is_valid is True if URL is safe to fetch.
    """
    # Check URL length
    if len(url) > MAX_URL_LENGTH:
        logger.warning(f"[SECURITY] URL exceeds maximum length: {len(url)} chars")
        return False, f"URL exceeds maximum length of {MAX_URL_LENGTH} characters"

    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        logger.warning(f"[SECURITY] Failed to parse URL: {e}")
        return False, f"Invalid URL format: {str(e)}"

    # Validate scheme
    scheme = parsed.scheme.lower()
    if not scheme:
        logger.warning("[SECURITY] URL missing scheme")
        return False, "URL must include a scheme (http:// or https://)"

    if scheme not in ALLOWED_SCHEMES:
        logger.warning(f"[SECURITY] Disallowed scheme: {scheme}")
        return False, f"Scheme '{scheme}' is not allowed. Only http:// and https:// are permitted"

    # Validate hostname
    hostname = parsed.hostname
    if not hostname:
        logger.warning("[SECURITY] URL missing hostname")
        return False, "URL must include a hostname"

    # Check for blocked hosts before resolution
    if _is_blocked_host(hostname):
        logger.warning(f"[SECURITY] Blocked host detected: {hostname}")
        return False, f"Access to host '{hostname}' is not allowed"

    # Check if hostname is an IP address
    try:
        ip = ipaddress.ip_address(hostname)
        # Direct IP access - validate immediately
        if _is_private_ip(hostname):
            logger.warning(f"[SECURITY] Private IP access blocked: {hostname}")
            return False, f"Access to private IP addresses is not allowed"
    except ValueError:
        # Not an IP, it's a hostname - need DNS resolution
        pass

    # Check port
    port = parsed.port
    if port is not None and port in BLOCKED_PORTS:
        logger.warning(f"[SECURITY] Blocked port detected: {port}")
        return False, f"Access to port {port} is not allowed"

    # Resolve hostname to IP (DNS validation)
    resolved_ip, error = _resolve_hostname(hostname)
    if error:
        logger.warning(f"[SECURITY] DNS resolution failed for {hostname}: {error}")
        return False, f"Could not resolve hostname: {error}"

    # Re-validate resolved IP address
    if _is_private_ip(resolved_ip):
        logger.warning(f"[SECURITY] Resolved IP is private: {hostname} -> {resolved_ip}")
        return False, f"Access to private IP addresses is not allowed (resolved from {hostname})"

    logger.debug(f"[SECURITY] URL validated successfully: {url} -> {resolved_ip}")
    return True, ""


def validate_redirect_url(base_url: str, redirect_url: str) -> Tuple[bool, str]:
    """
    Validate a redirect URL against the original base URL.

    Prevents open redirects and SSRF through redirect chains.
    Validates that the redirect destination is not to a private IP or blocked host.

    Args:
        base_url: The original request URL
        redirect_url: The URL being redirected to

    Returns:
        Tuple of (is_valid, error_message)
    """
    # If redirect URL is relative, it's generally safer but still validate
    if redirect_url.startswith('/') or not bool(urlparse(redirect_url).netloc):
        # Relative redirect - combine with base
        parsed_base = urlparse(base_url)
        redirect_url = f"{parsed_base.scheme}://{parsed_base.netloc}{redirect_url}"

    # Validate the redirect URL
    return validate_url(redirect_url)


class SSRFValidator:
    """
    SSRF Validator class for managing URL validation state and configuration.

    Provides a configurable interface for SSRF protection that can be
    customized with different blocked hosts, networks, and validation rules.
    """

    def __init__(
        self,
        max_url_length: int = MAX_URL_LENGTH,
        allowed_schemes: Optional[Set[str]] = None,
        blocked_hosts: Optional[Set[str]] = None,
        blocked_ports: Optional[Set[int]] = None,
        custom_private_networks: Optional[list] = None
    ):
        """
        Initialize SSRF validator with custom configuration.

        Args:
            max_url_length: Maximum allowed URL length
            allowed_schemes: Set of allowed URL schemes (default: http, https)
            blocked_hosts: Additional hosts to block
            blocked_ports: Additional ports to block
            custom_private_networks: Additional IP networks to treat as private
        """
        self.max_url_length = max_url_length
        self.allowed_schemes = allowed_schemes or ALLOWED_SCHEMES.copy()
        self.blocked_hosts = blocked_hosts or set()
        self.blocked_ports = blocked_ports or set()

        # Combine default and custom blocked hosts
        self._blocked_hosts_all = BLOCKED_HOSTS | self.blocked_hosts

        # Combine default and custom blocked ports
        self._blocked_ports_all = BLOCKED_PORTS | self.blocked_ports

        # Combine default and custom private networks
        self._private_ipv4 = PRIVATE_IPV4_NETWORKS.copy()
        self._private_ipv6 = PRIVATE_IPV6_NETWORKS.copy()
        if custom_private_networks:
            for network in custom_private_networks:
                if isinstance(network, ipaddress.IPv4Network):
                    self._private_ipv4.append(network)
                elif isinstance(network, ipaddress.IPv6Network):
                    self._private_ipv6.append(network)

    def validate(self, url: str) -> Tuple[bool, str]:
        """
        Validate a URL using this validator's configuration.

        Args:
            url: The URL to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check URL length
        if len(url) > self.max_url_length:
            logger.warning(f"[SECURITY] URL exceeds maximum length: {len(url)} chars")
            return False, f"URL exceeds maximum length of {self.max_url_length} characters"

        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception as e:
            logger.warning(f"[SECURITY] Failed to parse URL: {e}")
            return False, f"Invalid URL format: {str(e)}"

        # Validate scheme
        scheme = parsed.scheme.lower()
        if not scheme:
            return False, "URL must include a scheme (http:// or https://)"

        if scheme not in self.allowed_schemes:
            logger.warning(f"[SECURITY] Disallowed scheme: {scheme}")
            return False, f"Scheme '{scheme}' is not allowed"

        # Validate hostname
        hostname = parsed.hostname
        if not hostname:
            return False, "URL must include a hostname"

        # Check blocked hosts
        hostname_lower = hostname.lower()
        if hostname_lower in self._blocked_hosts_all:
            logger.warning(f"[SECURITY] Blocked host detected: {hostname}")
            return False, f"Access to host '{hostname}' is not allowed"

        # Validate IP if hostname is an IP address
        try:
            ip = ipaddress.ip_address(hostname)
            if self._is_ip_blocked(hostname):
                return False, f"Access to private IP addresses is not allowed"
        except ValueError:
            pass

        # Check port
        port = parsed.port
        if port is not None and port in self._blocked_ports_all:
            logger.warning(f"[SECURITY] Blocked port detected: {port}")
            return False, f"Access to port {port} is not allowed"

        # DNS resolution and validation
        resolved_ip, error = _resolve_hostname(hostname)
        if error:
            logger.warning(f"[SECURITY] DNS resolution failed for {hostname}: {error}")
            return False, f"Could not resolve hostname: {error}"

        # Check if resolved IP is blocked
        if self._is_ip_blocked(resolved_ip):
            logger.warning(f"[SECURITY] Resolved IP is private: {hostname} -> {resolved_ip}")
            return False, f"Access to private IP addresses is not allowed"

        return True, ""

    def _is_ip_blocked(self, ip_str: str) -> bool:
        """Check if IP is in blocked networks."""
        try:
            ip = ipaddress.ip_address(ip_str)

            if isinstance(ip, ipaddress.IPv4Address):
                for network in self._private_ipv4:
                    if ip in network:
                        return True

            if isinstance(ip, ipaddress.IPv6Address):
                for network in self._private_ipv6:
                    if ip in network:
                        return True

            return False
        except ValueError:
            return False

    def validate_redirect(self, base_url: str, redirect_url: str) -> Tuple[bool, str]:
        """Validate a redirect URL."""
        if redirect_url.startswith('/') or not bool(urlparse(redirect_url).netloc):
            parsed_base = urlparse(base_url)
            redirect_url = f"{parsed_base.scheme}://{parsed_base.netloc}{redirect_url}"
        return self.validate(redirect_url)
