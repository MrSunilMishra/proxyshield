"""
Unit tests for ProxyShield Security Shield, Direct-IP Protection, Risk Engine, and Multi-Format Reporting
"""

import tempfile
import os
import pytest

from proxyshield.security_shield import (
    StrictProxyShield,
    DirectIPExposureError,
    ProxyConnectivityError,
    LEGAL_PRIVACY_NOTICE,
)
from proxyshield.proxy_verifier import calculate_risk_score
from proxyshield.reporter import export_multi_format_reports
from proxyshield.db import init_db, get_session, ProxyRecord, AuditSession


def test_strict_proxy_shield_blocks_direct_ip():
    operator_ip = "198.51.100.42"
    shield = StrictProxyShield(operator_direct_ip=operator_ip)

    # When exit IP is different, it is safe
    ok, msg = shield.verify_exit_ip("203.0.113.19")
    assert ok is True

    # When exit IP matches operator direct IP, it must raise DirectIPExposureError
    with pytest.raises(DirectIPExposureError):
        shield.verify_exit_ip(operator_ip)


def test_strict_proxy_shield_zero_direct_fallback():
    shield = StrictProxyShield(operator_direct_ip="198.51.100.42")
    assert shield.direct_fallback_enabled is False

    # Calling execute_strictly_via_proxy with invalid proxy must raise ProxyConnectivityError, never fallback to direct
    with pytest.raises(ProxyConnectivityError):
        shield.execute_strictly_via_proxy("http://127.0.0.1:9999", "http://example.com", timeout=1)


def test_risk_score_calculation():
    # Dead proxy should be Unavailable with risk 100
    score, label, warnings = calculate_risk_score(
        protocol="http",
        is_alive=False,
        https_supported=False,
        leaks_direct_ip=False,
        ip_mismatch=False,
        latency_ms=0,
        unexpected_headers=[]
    )
    assert label == "Unavailable"
    assert score == 100

    # Live proxy with direct IP leak must be High Risk
    score_leak, label_leak, warnings_leak = calculate_risk_score(
        protocol="http",
        is_alive=True,
        https_supported=True,
        leaks_direct_ip=True,
        ip_mismatch=False,
        latency_ms=250,
        unexpected_headers=["X-Forwarded-For: 198.51.100.42"]
    )
    assert label_leak == "High Risk"
    assert any("exposes client IP" in w for w in warnings_leak)


def test_multi_format_reporting():
    audit_data = {
        "target_url": "http://authorized-test.local",
        "total_requests": 2,
        "direct_exposure_prevented": 0,
        "results": [
            {
                "endpoint": "http://1.2.3.4:80",
                "exit_ip": "1.2.3.4",
                "status_code": 200,
                "category": "SUCCESS",
                "evidence": "HTTP 200 OK",
                "latency_ms": 150
            },
            {
                "endpoint": "socks5://5.6.7.8:1080",
                "exit_ip": "5.6.7.8",
                "status_code": 403,
                "category": "HTTP_403",
                "evidence": "WAF Block",
                "latency_ms": 220
            }
        ]
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = os.path.join(tmpdir, "test_report")
        out_files = export_multi_format_reports(audit_data, base_path)

        assert "json" in out_files and os.path.exists(out_files["json"])
        assert "csv" in out_files and os.path.exists(out_files["csv"])
        assert "html" in out_files and os.path.exists(out_files["html"])

        # Verify legal notice is in HTML
        with open(out_files["html"], "r", encoding="utf-8") as f:
            content = f.read()
            assert "Legal & Privacy Transparency Notice" in content
            assert "Quarkova" in content


def test_sqlite_db_init_and_records():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        engine = init_db(db_path)
        session = get_session(engine)

        proxy = ProxyRecord(
            ip="192.0.2.1",
            port=8080,
            protocol="http",
            proxy_url="http://192.0.2.1:8080",
            source_name="UnitTest",
            country_code="US"
        )
        session.add(proxy)
        session.commit()

        retrieved = session.query(ProxyRecord).filter_by(ip="192.0.2.1").first()
        assert retrieved is not None
        assert retrieved.port == 8080
        assert retrieved.source_name == "UnitTest"

        # Explicitly close session and dispose engine so Windows releases file lock
        session.close()
        engine.dispose()


def test_collect_target_intelligence():
    from proxyshield.auditor import collect_target_intelligence
    intel = collect_target_intelligence("https://example.com")
    assert intel["hostname"] == "example.com"
    assert intel["port"] == 443
    assert intel["scheme"] == "https"
    assert "resolved_ip" in intel
    assert "server" in intel
    assert "cdn_waf" in intel
    assert "security_headers" in intel
