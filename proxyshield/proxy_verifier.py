"""
ProxyShield Proxy Verification & Risk Analysis Engine
Performs protocol verification, exit IP discovery, header leak detection,
HTTPS CONNECT testing, and risk assessment scoring.

Author: Quarkova
Website: https://quarkova.com
"""

import time
import json
import datetime
from typing import Dict, Any, Tuple, List, Optional
import httpx

from proxyshield.security_shield import StrictProxyShield, DirectIPExposureError


def calculate_risk_score(
    protocol: str,
    is_alive: bool,
    https_supported: bool,
    leaks_direct_ip: bool,
    ip_mismatch: bool,
    latency_ms: int,
    unexpected_headers: List[str]
) -> Tuple[int, str, List[str]]:
    """
    Computes a risk score (0 to 100) and risk label:
      - Unavailable
      - High Risk
      - Verified Connectivity
      - Unverified
    Note: A public proxy is never labeled 'Secure' because third-party public proxies are untrusted.
    """
    warnings = []
    if not is_alive:
        return 100, "Unavailable", ["Proxy endpoint failed connectivity tests."]

    score = 25  # Base score for any public third-party proxy

    if leaks_direct_ip:
        score += 50
        warnings.append("CRITICAL: Proxy exposes client IP in headers (X-Forwarded-For / Via).")

    if not https_supported:
        score += 20
        warnings.append("Plaintext HTTP proxy without verified HTTPS CONNECT support.")

    if protocol in ("http", "socks4"):
        score += 15
        warnings.append(f"Legacy {protocol.upper()} protocol lacks modern transport guarantees.")

    if ip_mismatch:
        score += 10
        warnings.append("Observed exit IP differs from proxy host IP (routed / exit node cluster).")

    if unexpected_headers:
        score += 10
        warnings.append(f"Proxy injects non-standard HTTP headers: {', '.join(unexpected_headers)}")

    if latency_ms > 2000:
        score += 5
        warnings.append(f"High latency ({latency_ms} ms) indicates unstable relay.")

    score = min(100, max(0, score))

    if leaks_direct_ip or score >= 70:
        label = "High Risk"
    else:
        label = "Verified Connectivity"

    return score, label, warnings


class ProxyVerifier:
    """Verifies proxy integrity, exit IP, and leak detection."""

    def __init__(self, shield: Optional[StrictProxyShield] = None):
        self.shield = shield or StrictProxyShield()

    def verify_single_proxy(
        self,
        proxy_url: str,
        timeout: int = 5
    ) -> Dict[str, Any]:
        """
        Executes complete verification pipeline:
        1. Tests connectivity
        2. Discovers observed exit IP
        3. Tests HTTPS CONNECT
        4. Detects direct IP header leaks
        5. Computes risk score
        """
        start = time.perf_counter()
        observed_exit_ip = None
        https_supported = False
        leaks_direct_ip = False
        unexpected_headers = []
        is_alive = False
        ip_mismatch = False

        # Extract proxy host IP for mismatch check
        host_ip = proxy_url.split("://")[-1].split(":")[0] if "://" in proxy_url else proxy_url.split(":")[0]

        # 1. Test HTTP & Header leak inspection
        try:
            with httpx.Client(proxy=proxy_url, timeout=timeout) as client:
                # Query httpbin for header and IP inspection
                resp = client.get("http://httpbin.org/get")
                if resp.status_code == 200:
                    is_alive = True
                    data = resp.json()
                    observed_exit_ip = data.get("origin", "").split(",")[0].strip()

                    # Check headers for operator direct IP leak
                    headers = data.get("headers", {})
                    for h in ["X-Forwarded-For", "Via", "X-Real-Ip", "Client-Ip"]:
                        if h in headers:
                            val = headers[h]
                            unexpected_headers.append(f"{h}: {val}")
                            if self.shield.operator_direct_ip and self.shield.operator_direct_ip in val:
                                leaks_direct_ip = True

                    # Verify exit IP does not directly match operator
                    try:
                        self.shield.verify_exit_ip(observed_exit_ip)
                    except DirectIPExposureError:
                        leaks_direct_ip = True
        except Exception:
            # Fallback connectivity attempt via basic ip echo
            try:
                ok, exit_ip, _ = self.shield.check_proxy_exit_ip(proxy_url, timeout=timeout)
                if ok:
                    is_alive = True
                    observed_exit_ip = exit_ip
            except Exception:
                is_alive = False

        latency_ms = int((time.perf_counter() - start) * 1000)

        # 2. Test HTTPS CONNECT support
        if is_alive:
            try:
                with httpx.Client(proxy=proxy_url, timeout=timeout) as client:
                    resp_https = client.get("https://httpbin.org/ip")
                    if resp_https.status_code == 200:
                        https_supported = True
            except Exception:
                https_supported = False

        if observed_exit_ip and host_ip and observed_exit_ip != host_ip:
            ip_mismatch = True

        proto = proxy_url.split("://")[0] if "://" in proxy_url else "http"
        risk_score, risk_label, warnings = calculate_risk_score(
            protocol=proto,
            is_alive=is_alive,
            https_supported=https_supported,
            leaks_direct_ip=leaks_direct_ip,
            ip_mismatch=ip_mismatch,
            latency_ms=latency_ms,
            unexpected_headers=unexpected_headers
        )

        return {
            "proxy_url": proxy_url,
            "protocol": proto,
            "is_alive": is_alive,
            "latency_ms": latency_ms,
            "observed_exit_ip": observed_exit_ip,
            "https_supported": https_supported,
            "leaks_direct_ip": leaks_direct_ip,
            "ip_mismatch": ip_mismatch,
            "risk_score": risk_score,
            "risk_label": risk_label,
            "security_warnings": warnings,
            "verified_at": datetime.datetime.utcnow().isoformat()
        }
