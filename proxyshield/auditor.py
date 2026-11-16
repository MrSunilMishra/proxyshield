"""
ProxyShield Authorized Target Security Auditor & Firewall Diagnostic Engine
Conducts low-rate HTTP requests across verified public proxy endpoints against authorized targets,
records observed exit IPs, classifies responses, and distinguishes true firewall blocks from proxy failures.

Author: Quarkova
Website: https://quarkova.com
"""

import time
import socket
import ssl
import datetime
from urllib.parse import urlparse
from typing import List, Dict, Any, Optional, Tuple
import httpx

from proxyshield.security_shield import StrictProxyShield, DirectIPExposureError, ProxyConnectivityError
from proxyshield.db import get_session, AuditSession, AuditResult, ProxyRecord


def collect_target_intelligence(
    target_url: str,
    resp: Optional[httpx.Response] = None,
    existing_intel: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Collects web target metadata & security profiling:
    - Hostname & DNS-resolved IP
    - Web service port availability (80, 443, 8080, 8443)
    - SSL/TLS certificate details (TLS version, cipher, issuer, expiry)
    - Server header & software version
    - Framework / Backend technology (X-Powered-By)
    - CDN & Web Application Firewall (WAF) detection
    - Security headers audit (HSTS, CSP, X-Frame-Options, X-Content-Type-Options)
    """
    if existing_intel and resp:
        # Fast path: update headers from response without re-probing ports/SSL
        intel = dict(existing_intel)
        headers = {k.lower(): v for k, v in resp.headers.items()}
        if "server" in headers:
            intel["server"] = headers["server"]
        if "x-powered-by" in headers:
            intel["powered_by"] = headers["x-powered-by"]

        srv_lower = intel.get("server", "").lower()
        if "cf-ray" in headers or "cf-cache-status" in headers or "cloudflare" in srv_lower:
            intel["cdn_waf"] = "Cloudflare WAF / CDN"
        elif "x-amz-cf-id" in headers or "x-amz-cf-pop" in headers:
            intel["cdn_waf"] = "Amazon CloudFront"
        elif "x-akamai-transformed" in headers or "akamai" in srv_lower:
            intel["cdn_waf"] = "Akamai Edge"
        elif "x-sucuri-id" in headers or "sucuri" in srv_lower:
            intel["cdn_waf"] = "Sucuri CloudProxy WAF"
        elif "x-fastly-request-id" in headers:
            intel["cdn_waf"] = "Fastly Edge Cloud"
        elif "x-cdn" in headers and "incapsula" in headers.get("x-cdn", "").lower():
            intel["cdn_waf"] = "Imperva Incapsula"

        sec_headers = dict(intel.get("security_headers", {}))
        sec_headers["strict_transport_security"] = headers.get("strict-transport-security", "Missing")
        sec_headers["content_security_policy"] = "Configured" if "content-security-policy" in headers else "Missing"
        sec_headers["x_frame_options"] = headers.get("x-frame-options", "Missing")
        sec_headers["x_content_type_options"] = headers.get("x-content-type-options", "Missing")
        intel["security_headers"] = sec_headers
        return intel
    parsed = urlparse(target_url)
    hostname = parsed.hostname or ""
    scheme = parsed.scheme or "https"
    default_port = 443 if scheme == "https" else 80
    port = parsed.port or default_port

    # 1. DNS Resolution
    resolved_ip = "Unknown"
    if hostname:
        try:
            resolved_ip = socket.gethostbyname(hostname)
        except Exception as e:
            resolved_ip = f"Resolution error: {e}"

    # 2. Web Service Ports Check (fast concurrent check on initial discovery only)
    open_ports = []
    test_ports = [80, 443, 8080, 8443]
    if hostname and resolved_ip != "Unknown" and not resolved_ip.startswith("Resolution error") and resp is None:
        def _test_p(p):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.4)
                    if s.connect_ex((hostname, p)) == 0:
                        return {
                            "port": p,
                            "service": "HTTPS" if p in (443, 8443) else "HTTP",
                            "state": "OPEN"
                        }
            except Exception:
                pass
            return None

        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as ex:
            for res_p in ex.map(_test_p, test_ports):
                if res_p:
                    open_ports.append(res_p)

    # 3. SSL/TLS Certificate Analysis
    ssl_info = {
        "ssl_active": False,
        "tls_version": "N/A",
        "cipher": "N/A",
        "issuer": "N/A",
        "expires": "N/A"
    }
    if scheme == "https" and hostname:
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=3.0) as sock:
                with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    version = ssock.version()
                    issuer_dict = dict(x[0] for x in cert.get('issuer', []))
                    ssl_info = {
                        "ssl_active": True,
                        "tls_version": version or "TLS",
                        "cipher": cipher[0] if cipher else "Unknown",
                        "issuer": issuer_dict.get('organizationName') or issuer_dict.get('commonName', 'Unknown'),
                        "expires": cert.get('notAfter', 'Unknown')
                    }
        except Exception:
            pass

    intel = {
        "hostname": hostname,
        "resolved_ip": resolved_ip,
        "port": port,
        "scheme": scheme,
        "open_web_ports": open_ports,
        "ssl": ssl_info,
        "server": "Undisclosed / Hidden",
        "powered_by": "None disclosed",
        "cdn_waf": "Direct Origin / No CDN header detected",
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

        # CDN & WAF Fingerprinting
        srv_lower = intel["server"].lower()
        if "cf-ray" in headers or "cf-cache-status" in headers or "cloudflare" in srv_lower:
            intel["cdn_waf"] = "Cloudflare WAF / CDN"
        elif "x-amz-cf-id" in headers or "x-amz-cf-pop" in headers:
            intel["cdn_waf"] = "Amazon CloudFront"
        elif "x-akamai-transformed" in headers or "akamai" in srv_lower:
            intel["cdn_waf"] = "Akamai Edge"
        elif "x-fastly-request-id" in headers:
            intel["cdn_waf"] = "Fastly CDN"
        elif "x-sucuri-id" in headers:
            intel["cdn_waf"] = "Sucuri Cloud WAF"
        elif "x-iinfo" in headers:
            intel["cdn_waf"] = "Imperva Incapsula"

        # Security Headers Audit
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
        discarded_dead = 0

        # In-memory candidate pool with zero disk storage
        candidate_pool = list(proxies)
        pool_idx = 0
        fetched_fallback = False

        while len(results) < max_requests and pool_idx < len(candidate_pool):
            proxy_item = candidate_pool[pool_idx]
            pool_idx += 1
            proxy_url = proxy_item["proxy"]

            # 1. Discover & Validate observed exit IP first (Strict Direct-IP Guard)
            try:
                ok_exit, observed_exit_ip, _ = self.shield.check_proxy_exit_ip(proxy_url, timeout=timeout)
                if not ok_exit or not observed_exit_ip:
                    # Stale / dead proxy: discard immediately, do not clutter results
                    discarded_dead += 1
                    # If pool runs low, replenish once from in-memory iplocate feeds
                    if pool_idx >= len(candidate_pool) and not fetched_fallback and len(results) < max_requests:
                        fetched_fallback = True
                        try:
                            from proxyshield.proxy_engine import fetch_iplocate_proxies
                            fresh = fetch_iplocate_proxies(timeout=timeout)
                            for it in fresh:
                                if it not in candidate_pool:
                                    candidate_pool.append(it)
                        except Exception:
                            pass
                    continue
            except DirectIPExposureError:
                direct_exposure_prevented += 1
                continue

            # 2. Execute target test strictly via verified working proxy
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
                target_intel = collect_target_intelligence(target_url, resp, existing_intel=target_intel)
            except Exception:
                # Proxy dropped connection to target: discard and continue
                discarded_dead += 1
                if pool_idx >= len(candidate_pool) and not fetched_fallback and len(results) < max_requests:
                    fetched_fallback = True
                    try:
                        from proxyshield.proxy_engine import fetch_iplocate_proxies
                        fresh = fetch_iplocate_proxies(timeout=timeout)
                        for it in fresh:
                            if it not in candidate_pool:
                                candidate_pool.append(it)
                    except Exception:
                        pass
                continue

            elapsed_ms = int((time.perf_counter() - start_req) * 1000)
            category, evidence = self.classify_target_response(status_code, exception_obj)
            total += 1

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

        # If all candidates died and zero requests succeeded, add a notice
        if not results:
            results.append({
                "endpoint": "all_candidates_exhausted",
                "exit_ip": "none",
                "status_code": None,
                "category": "PROXY_POOL_EXHAUSTED",
                "evidence": f"Tested {discarded_dead} candidates from free pool; none maintained live connection to target. Fetching new proxies recommended.",
                "latency_ms": 0,
            })

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

