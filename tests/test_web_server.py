"""
Unit tests for ProxyShield Local Web Server & Dashboard
"""

import urllib.request
import json
import pytest
from proxyshield.web_server import (
    find_available_port,
    generate_dashboard_html,
    start_report_server,
)


def test_find_available_port():
    port = find_available_port(start_port=18080)
    assert isinstance(port, int)
    assert port >= 18080


def test_generate_dashboard_html_structure():
    mock_reports = [
        {
            "name": "audit_report.html",
            "format": "HTML",
            "size_kb": 24.5,
            "modified": "2026-11-16 19:00:00"
        }
    ]
    html = generate_dashboard_html(mock_reports, port=8080)
    assert "ProxyShield" in html
    assert "Quarkova" in html
    assert "proxyshield.test:8080" in html
    assert "audit_report.html" in html
    assert "Direct-IP Guard Policy" in html


def test_start_report_server_background():
    # Start server on dynamic port without opening browser
    local_url, port = start_report_server(port=18888, open_browser=False, background=True)
    assert "http://127.0.0.1:" in local_url

    # Query dashboard
    req = urllib.request.Request(local_url)
    with urllib.request.urlopen(req, timeout=3) as resp:
        assert resp.status == 200
        content = resp.read().decode("utf-8")
        assert "ProxyShield" in content
        assert "Quarkova" in content

    # Query api status
    api_url = f"{local_url}/api/status"
    req_api = urllib.request.Request(api_url)
    with urllib.request.urlopen(req_api, timeout=3) as resp_api:
        assert resp_api.status == 200
        data = json.loads(resp_api.read().decode("utf-8"))
        assert data["tool"] == "ProxyShield"
        assert data["author"] == "Quarkova"


def test_safe_open_browser_and_dns_check():
    from proxyshield.web_server import safe_open_browser, check_local_dns_status
    # Checking DNS structure
    dns = check_local_dns_status()
    assert "hosts_path" in dns
    assert "configured" in dns
    assert isinstance(dns["configured"], bool)

    # safe_open_browser should run without raising uncaught exceptions
    res = safe_open_browser("http://127.0.0.1:8080")
    assert isinstance(res, bool)
