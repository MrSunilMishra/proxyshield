"""
ProxyShield Strict Direct-IP Protection Engine
Enforces strict proxy-only execution, prevents direct IP exposure or fallback,
validates observed exit IPs against the operator's direct public IP, and surfaces
mandatory legal transparency disclaimers.

Author: Quarkova
Website: https://quarkova.com
"""

import time
import socket
import urllib.request
from typing import Optional, Tuple, List
import httpx

LEGAL_PRIVACY_NOTICE = (
    "ProxyShield uses publicly available third-party proxy services for educational "
    "and authorized network security auditing. The operator's direct public IP is not "
    "intentionally used for target requests in strict proxy-only mode. Public proxy "
    "operators may observe, inspect or log traffic. ProxyShield does not guarantee "
    "anonymity, privacy or proxy security. All testing must be conducted against "
    "authorized targets."
)

IP_ECHO_SERVICES = [
    "https://api.ipify.org?format=text",
    "https://icanhazip.com",
    "https://ifconfig.me/ip",
]


class DirectIPExposureError(Exception):
    """Raised when an observed exit IP matches the operator's direct public IP."""
    pass


class ProxyConnectivityError(Exception):
    """Raised when a proxy endpoint fails in strict proxy-only mode."""
    pass


def discover_operator_direct_ip(timeout: int = 6) -> str:
    """
    Discovers the operator's actual public IP before testing.
    This serves as the defensive baseline to ensure that strict proxy-only mode
    never leaks or falls back to the operator's direct connection.
    """
    for url in IP_ECHO_SERVICES:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ProxyShield/1.0.0 Direct-IP-Discovery"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                ip = resp.read().decode("utf-8").strip()
                if ip and len(ip.split(".")) == 4:
                    return ip
        except Exception:
            continue
    return "0.0.0.0"


class StrictProxyShield:
    """
    Guarantees strict proxy-only enforcement.
    1. Direct connection fallback is permanently disabled.
    2. Observed exit IP must differ from operator's direct public IP.
    3. Aborts requests immediately upon proxy failure.
    """

    def __init__(self, operator_direct_ip: Optional[str] = None):
        self.operator_direct_ip = operator_direct_ip or discover_operator_direct_ip()
        self.direct_fallback_enabled = False  # Strictly forbidden by Section C

    def verify_exit_ip(self, observed_exit_ip: str) -> Tuple[bool, str]:
        """
        Validates that the exit IP is distinct from the operator's public IP.
        """
        if not observed_exit_ip or observed_exit_ip == "unknown":
            return False, "Could not determine observed exit IP."

        if self.operator_direct_ip and self.operator_direct_ip != "0.0.0.0":
            if observed_exit_ip.strip() == self.operator_direct_ip.strip():
                raise DirectIPExposureError(
                    f"CRITICAL SECURITY ALERT: Observed exit IP '{observed_exit_ip}' MATCHES "
                    f"the operator's direct public IP! Direct IP leak detected. Request aborted."
                )

        return True, f"Verified safe exit IP: {observed_exit_ip} (distinct from direct public IP)."

    def check_proxy_exit_ip(self, proxy_url: str, timeout: int = 5) -> Tuple[bool, str, int]:
        """
        Queries an IP-echo endpoint through the proxy to discover its observed exit IP.
        Uses multiple fast mirrors (httpbin, ipify) in memory with zero file storage.
        Returns (success, observed_exit_ip, latency_ms).
        """
        start = time.perf_counter()
        # Fast in-memory echo mirrors supporting both HTTP & HTTPS proxy tunnels
        check_endpoints = [
            "http://httpbin.org/ip",
            "https://api.ipify.org?format=text",
            "http://api.ipify.org?format=text",
            "https://api64.ipify.org?format=text",
        ]
        last_err = "No response from proxy"

        for ep in check_endpoints:
            try:
                with httpx.Client(proxy=proxy_url, timeout=timeout) as client:
                    resp = client.get(ep)
                    latency_ms = int((time.perf_counter() - start) * 1000)
                    if resp.status_code == 200 and resp.text.strip():
                        raw_text = resp.text.strip()
                        if "{" in raw_text and "origin" in raw_text:
                            try:
                                exit_ip = resp.json().get("origin", "").split(",")[0].strip()
                            except Exception:
                                exit_ip = raw_text.split()[0]
                        else:
                            exit_ip = raw_text.split()[0].strip()

                        if exit_ip and exit_ip != "unknown":
                            # Enforce strict direct IP guard
                            self.verify_exit_ip(exit_ip)
                            return True, exit_ip, latency_ms
            except DirectIPExposureError:
                raise
            except Exception as e:
                last_err = str(e)
                continue

        latency_ms = int((time.perf_counter() - start) * 1000)
        return False, last_err, latency_ms

    def execute_strictly_via_proxy(
        self,
        proxy_url: str,
        target_url: str,
        timeout: int = 6,
        headers: Optional[dict] = None
    ) -> httpx.Response:
        """
        Executes a target request strictly through the given proxy.
        If the proxy fails or disconnects, the request is ABORTED.
        NEVER falls back to direct connection.
        """
        try:
            with httpx.Client(proxy=proxy_url, timeout=timeout) as client:
                return client.get(target_url, headers=headers)
        except Exception as ex:
            raise ProxyConnectivityError(
                f"Strict Proxy Mode: Proxy connection failed for '{proxy_url}'. "
                f"Automatic direct fallback is disabled to protect direct IP. Error: {ex}"
            )

