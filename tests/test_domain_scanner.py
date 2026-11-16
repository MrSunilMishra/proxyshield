"""
Unit tests for ProxyShield Domain Scanner & Reconnaissance Engine
"""

from proxyshield.domain_scanner import (
    clean_target_hostname,
    scan_domain,
    scan_target_ports,
    inspect_ssl_certificate,
    inspect_http_technologies,
)


def test_clean_target_hostname():
    h1, s1, p1 = clean_target_hostname("example.com")
    assert h1 == "example.com"
    assert s1 == "https"
    assert p1 == 443

    h2, s2, p2 = clean_target_hostname("http://test.local:8080/path")
    assert h2 == "test.local"
    assert s2 == "http"
    assert p2 == 8080


def test_scan_domain_structure():
    data = scan_domain("127.0.0.1")
    assert "hostname" in data
    assert "ipv4" in data
    assert "open_ports" in data
    assert "ssl" in data
    assert "technologies" in data
    assert "scan_duration_seconds" in data
