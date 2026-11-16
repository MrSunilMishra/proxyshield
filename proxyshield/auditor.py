"""
ProxyShield Authorized Target Security Auditor & Firewall Diagnostic Engine
Conducts low-rate HTTP requests across verified public proxy endpoints against authorized targets,
records observed exit IPs, classifies responses, and distinguishes true firewall blocks from proxy failures.

Author: Quarkova
Website: https://quarkova.com
"""

import time
import socket
import datetime
from urllib.parse import urlparse
from typing import List, Dict, Any, Optional, Tuple
import httpx

from proxyshield.security_shield import StrictProxyShield, DirectIPExposureError, ProxyConnectivityError
from proxyshield.db import get_session, AuditSession, AuditResult, ProxyRecord


def collect_target_intelligence(target_url: str, resp: Optional[httpx.Response] = None) -> Dict[str, Any]:
    """
    Collects web target metadata: DNS-resolved IP, service port,
    server header, technologies (X-Powered-By), CDN/WAF detection,
    and security headers.
    """
    parsed = urlparse(target_url)
    hostname = parsed.hostname or ""
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    # DNS Resolution
    resolved_ip = "Unknown"
    if hostname:
        try:
            resolved_ip = socket.gethostbyname(hostname)
        except Exception as e:
            resolved_ip = f"Resolution error: {e}"

    intel = {
        "hostname": hostname,
        "resolved_ip": resolved_ip,
        "port": port,
        "scheme": parsed.scheme or "https",
        "server": "Undisclosed / Hidden",
        "powered_by": "None disclosed",
        "cdn_waf": "No CDN/WAF header detected",
        "security_headers": {
            "strict_transport_security": "Missing",
            "content_security_policy": "Missing",
            "x_frame_options": "Missing",
            "x_content_type_options": "Missing"
        }
    }

    if resp:
        headers = {k.lower(): v for k, v in resp.headers.items()}
        if "server" in headers:
            intel["server"] = headers["server"]
        if "x-powered-by" in headers:
            intel["powered_by"] = headers["x-powered-by"]

        # CDN / WAF Detection
        srv_lower = intel["server"].lower()
        if "cf-ray" in headers or "cf-cache-status" in headers or "cloudflare" in srv_lower:
            intel["cdn_waf"] = "Cloudflare"
        elif "x-amz-cf-id" in headers or "x-amz-cf-pop" in headers:
            intel["cdn_waf"] = "Amazon CloudFront"
        elif "x-akamai-transformed" in headers or "akamai" in srv_lower:
            intel["cdn_waf"] = "Akamai"
        elif "x-fastly-request-id" in headers:
            intel["cdn_waf"] = "Fastly"
        elif "x-sucuri-id" in headers:
            intel["cdn_waf"] = "Sucuri WAF"
        elif "x-iinfo" in headers:
            intel["cdn_waf"] = "Imperva Incapsula"

        # Security Headers
        sec_h = {
            "strict_transport_security": headers.get("strict-transport-security", "Missing"),
            "content_security_policy": "Present" if "content-security-policy" in headers else "Missing",
            "x_frame_options": headers.get("x-frame-options", "Missing"),
            "x_content_type_options": headers.get("x-content-type-options", "Missing")
        }
        intel["security_headers"] = sec_h

    return intel


class NetworkAuditEngine:
    """
    Executes controlled, low-rate security diagnostic requests across
    verified public proxy endpoints against an authorized target.
    """

    def __init__(self, shield: Optional[StrictProxyShield] = None):
        self.shield = shield or StrictProxyShield()

    def classify_target_response(
        self,
        status_code: Optional[int],
        exception: Optional[Exception]
    ) -> Tuple[str, str]:
        """
        Distinguishes response categories (Section F):
        - SUCCESS
        - HTTP_403
        - HTTP_429
        - HTTP_5XX
        - TCP_FAIL
        - TLS_FAIL
        - DNS_FAIL
        - PROXY_FAIL
        - FIREWALL_BLOCK (requires server-side verification)
        """
        if exception:
            err_str = str(exception).lower()
            if "proxy" in err_str or isinstance(exception, ProxyConnectivityError):
                return "PROXY_FAIL", f"Proxy connection failure: {exception}"
            elif "dns" in err_str or "name resolution" in err_str or "getaddrinfo" in err_str:
                return "DNS_FAIL", f"DNS lookup failed: {exception}"
            elif "tls" in err_str or "ssl" in err_str or "certificate" in err_str:
                return "TLS_FAIL", f"TLS handshake failed: {exception}"
            elif "timeout" in err_str or "timed out" in err_str:
                return "TIMEOUT", f"Connection or read timeout: {exception}"
            elif "connect" in err_str or "connection refused" in err_str:
                return "TCP_FAIL", f"TCP connection rejected: {exception}"
            return "NETWORK_ERROR", str(exception)

        if status_code == 403:
            return "HTTP_403", "HTTP 403 Forbidden: Endpoint or WAF blocked access."
        elif status_code == 429:
            return "HTTP_429", "HTTP 429 Too Many Requests: Target rate limit triggered."
        elif status_code and 500 <= status_code <= 599:
            return "HTTP_5XX", f"HTTP {status_code} Server Error on target."
        elif status_code and 200 <= status_code < 400:
            return "SUCCESS", f"HTTP {status_code} OK / Redirect."

        return f"HTTP_{status_code}", f"HTTP Status {status_code}"

    def audit_target(
        self,
        target_url: str,
        proxies: List[Dict[str, Any]],
        rate_limit_delay: float = 1.0,
        max_requests: int = 20,
        timeout: int = 6
    ) -> Dict[str, Any]:
        """
        Performs sequential, low-rate security checks across verified proxy endpoints.
        Enforces strict Direct-IP Protection on every request.
        """
        db_session = get_session()
        audit_rec = AuditSession(
            target_url=target_url,
            operator_direct_ip=self.shield.operator_direct_ip or "0.0.0.0",
            status="IN_PROGRESS"
        )
        db_session.add(audit_rec)
        db_session.commit()

        target_intel = collect_target_intelligence(target_url)

        results: List[Dict[str, Any]] = []
        total = 0
        success = 0
        blocked = 0
        direct_exposure_prevented = 0

        for proxy_item in proxies[:max_requests]:
            proxy_url = proxy_item["proxy"]
            total += 1

            # 1. Discover & Validate observed exit IP first (Strict Direct-IP Guard)
            try:
                ok_exit, observed_exit_ip, _ = self.shield.check_proxy_exit_ip(proxy_url, timeout=timeout)
                if not ok_exit:
                    cat, evidence = "PROXY_FAIL", f"Failed to verify exit IP on {proxy_url}"
                    res_entry = {
                        "endpoint": proxy_url,
                        "exit_ip": "unknown",
                        "status_code": None,
                        "category": cat,
                        "evidence": evidence,
                        "latency_ms": 0,
                    }
                    results.append(res_entry)
                    continue
            except DirectIPExposureError as die:
                direct_exposure_prevented += 1
                res_entry = {
                    "endpoint": proxy_url,
                    "exit_ip": self.shield.operator_direct_ip,
                    "status_code": None,
                    "category": "DIRECT_IP_LEAK_PREVENTED",
                    "evidence": str(die),
                    "latency_ms": 0,
                }
                results.append(res_entry)
                continue

            # 2. Execute target test strictly via proxy
            start_req = time.perf_counter()
            status_code = None
            exception_obj = None

            try:
                resp = self.shield.execute_strictly_via_proxy(
                    proxy_url=proxy_url,
                    target_url=target_url,
                    timeout=timeout,
                    headers={"User-Agent": "ProxyShield-Auditor/1.0.0 (Authorized Network Security Audit)"}
                )
                status_code = resp.status_code
                if status_code in (403, 429):
                    blocked += 1
                elif 200 <= status_code < 400:
                    success += 1
                # Collect target technology intelligence from live response
                target_intel = collect_target_intelligence(target_url, resp)
            except Exception as e:
                exception_obj = e

            elapsed_ms = int((time.perf_counter() - start_req) * 1000)
            category, evidence = self.classify_target_response(status_code, exception_obj)

            res_entry = {
                "endpoint": proxy_url,
                "exit_ip": observed_exit_ip,
                "status_code": status_code,
                "category": category,
                "evidence": evidence,
                "latency_ms": elapsed_ms,
            }
            results.append(res_entry)

            # Record in SQLite
            db_res = AuditResult(
                session_id=audit_rec.id,
                endpoint_used=proxy_url,
                observed_exit_ip=observed_exit_ip,
                status_code=status_code,
                response_time_ms=elapsed_ms,
                result_category=category,
                evidence=evidence
            )
            db_session.add(db_res)
            db_session.commit()

            # Respect low-rate safety delay
            if rate_limit_delay > 0:
                time.sleep(rate_limit_delay)

        audit_rec.total_requests = total
        audit_rec.successful_requests = success
        audit_rec.blocked_requests = blocked
        audit_rec.direct_ip_exposure_blocked = direct_exposure_prevented
        audit_rec.status = "COMPLETED"
        audit_rec.completed_at = datetime.datetime.utcnow()
        db_session.commit()

        return {
            "session_id": audit_rec.id,
            "target_url": target_url,
            "target_intel": target_intel,
            "operator_direct_ip": self.shield.operator_direct_ip,
            "total_requests": total,
            "successful_requests": success,
            "blocked_requests": blocked,
            "direct_exposure_prevented": direct_exposure_prevented,
            "results": results
        }


def parse_server_firewall_log(log_filepath: str, exit_ip: str) -> Optional[Dict[str, str]]:
    """
    Optional server-side agent helper to verify whether an observed exit IP
    was genuinely blocked by server-side firewall rules (iptables / ufw).
    """
    try:
        with open(log_filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if exit_ip in line and any(w in line.lower() for w in ["drop", "block", "reject", "deny"]):
                    return {
                        "confirmed": True,
                        "line": line.strip(),
                        "rule": "Firewall DROP/REJECT rule matched."
                    }
    except Exception:
        pass
    return None

