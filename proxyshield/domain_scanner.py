"""
ProxyShield Advanced Domain Security Scanner & Reconnaissance Engine
Nmap-style network service inspection, port availability, DNS profiling,
SSL/TLS certificate intelligence, web server fingerprinting, and security headers audit.

Author: Quarkova
Website: https://quarkova.com
"""

import socket
import ssl
import subprocess
import time
import datetime
from urllib.parse import urlparse
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from proxyshield.color_engine import colorize_text, BOLD, RESET

# Top 25 Standard Server & Web Service Ports
COMMON_PORTS = [
    (21, "FTP", "File Transfer Protocol"),
    (22, "SSH", "Secure Shell"),
    (23, "Telnet", "Unencrypted Telnet"),
    (25, "SMTP", "Simple Mail Transfer"),
    (53, "DNS", "Domain Name System"),
    (80, "HTTP", "Hypertext Transfer"),
    (110, "POP3", "Post Office Protocol"),
    (143, "IMAP", "Internet Message Access"),
    (443, "HTTPS", "HTTP Secure (TLS)"),
    (465, "SMTPS", "SMTP over SSL"),
    (587, "Submission", "Mail Submission"),
    (993, "IMAPS", "IMAP over SSL"),
    (995, "POP3S", "POP3 over SSL"),
    (2082, "cPanel", "cPanel Web Admin"),
    (2083, "cPanel-SSL", "cPanel Secure Admin"),
    (3306, "MySQL", "MySQL Database"),
    (3389, "RDP", "Remote Desktop Protocol"),
    (5432, "PostgreSQL", "PostgreSQL Database"),
    (6379, "Redis", "Redis Cache / KV"),
    (8000, "HTTP-Alt", "Common HTTP Alt / Dev"),
    (8080, "HTTP-Proxy", "HTTP Proxy / Alt Web"),
    (8443, "HTTPS-Alt", "HTTPS Alternate Web"),
    (8888, "HTTP-Alt", "Alternate Web App"),
    (9000, "PHP-FPM/Sonar", "PHP-FPM / Services"),
    (27017, "MongoDB", "MongoDB NoSQL Database"),
]


def clean_target_hostname(raw_target: str) -> Tuple[str, str, int]:
    """
    Extracts hostname, scheme, and default port from target URL or bare domain.
    """
    target = raw_target.strip()
    if not target.startswith("http://") and not target.startswith("https://"):
        scheme = "https"
        url = f"https://{target}"
    else:
        url = target
        scheme = urlparse(url).scheme or "https"

    parsed = urlparse(url)
    hostname = parsed.hostname or target.split("/")[0].split(":")[0]
    default_port = 443 if scheme == "https" else 80
    port = parsed.port or default_port
    return hostname, scheme, port


def query_dns_records(domain: str) -> Dict[str, List[str]]:
    """
    Queries DNS records (A, AAAA, MX, NS, TXT) using platform nslookup.
    """
    records = {"A": [], "AAAA": [], "MX": [], "NS": [], "TXT": []}

    def _lookup(qtype: str):
        try:
            res = subprocess.run(
                ["nslookup", f"-type={qtype}", domain],
                capture_output=True,
                text=True,
                timeout=2.5
            )
            lines = res.stdout.splitlines()
            entries = []
            for l in lines:
                l_strip = l.strip()
                if not l_strip or l_strip.startswith("Server:") or l_strip.startswith("Address:"):
                    continue
                if qtype == "MX" and ("mail exchanger" in l_strip.lower() or "mx" in l_strip.lower()):
                    entries.append(l_strip.split("=")[-1].strip())
                elif qtype == "NS" and ("nameserver" in l_strip.lower() or "ns" in l_strip.lower()):
                    entries.append(l_strip.split("=")[-1].strip())
                elif qtype == "TXT" and "text" in l_strip.lower():
                    entries.append(l_strip.split("=")[-1].strip().strip('"'))
            return qtype, entries
        except Exception:
            return qtype, []

    with ThreadPoolExecutor(max_workers=3) as ex:
        for qtype, results in ex.map(lambda t: _lookup(t), ["MX", "NS", "TXT"]):
            if results:
                records[qtype] = results[:4]

    return records


def grab_service_banner(hostname: str, port: int, service_name: str, timeout: float = 1.0) -> str:
    """Attempts to grab a banner from an open port."""
    if service_name in ("HTTP", "HTTPS", "HTTP-Proxy", "HTTPS-Alt", "HTTP-Alt"):
        return f"{service_name} Web Service"

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((hostname, port))
            if service_name in ("SSH", "FTP", "SMTP", "POP3", "IMAP"):
                banner = s.recv(128).decode("utf-8", errors="ignore").strip()
                if banner:
                    return banner.splitlines()[0][:60]
    except Exception:
        pass
    return f"{service_name} Service Active"


def scan_target_ports(
    hostname: str,
    ports: Optional[List[Tuple[int, str, str]]] = None,
    timeout: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Scans server ports concurrently and grabs service banners for open ports.
    """
    target_ports = ports or COMMON_PORTS
    results = []

    def _probe_port(item: Tuple[int, str, str]):
        p, sname, desc = item
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                if s.connect_ex((hostname, p)) == 0:
                    banner = grab_service_banner(hostname, p, sname)
                    return {
                        "port": p,
                        "service": sname,
                        "description": desc,
                        "state": "OPEN",
                        "banner": banner
                    }
        except Exception:
            pass
        return None

    with ThreadPoolExecutor(max_workers=min(25, len(target_ports))) as ex:
        for r in ex.map(_probe_port, target_ports):
            if r:
                results.append(r)

    results.sort(key=lambda x: x["port"])
    return results


def inspect_ssl_certificate(hostname: str, port: int = 443) -> Dict[str, Any]:
    """Inspects detailed SSL/TLS certificate security parameters."""
    ssl_data = {
        "ssl_active": False,
        "tls_version": "N/A",
        "cipher": "N/A",
        "issuer": "N/A",
        "subject": "N/A",
        "expires": "N/A",
        "days_left": None,
        "san_count": 0,
    }

    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=3.0) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                cipher = ssock.cipher()
                version = ssock.version()
                issuer_dict = dict(x[0] for x in cert.get("issuer", []))
                subject_dict = dict(x[0] for x in cert.get("subject", []))
                sans = [x[1] for x in cert.get("subjectAltName", []) if x[0] == "DNS"]
                not_after = cert.get("notAfter")

                days_left = None
                if not_after:
                    try:
                        exp_dt = datetime.datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                        days_left = (exp_dt - datetime.datetime.utcnow()).days
                    except Exception:
                        pass

                ssl_data = {
                    "ssl_active": True,
                    "tls_version": version or "TLS",
                    "cipher": cipher[0] if cipher else "Unknown",
                    "issuer": issuer_dict.get("organizationName") or issuer_dict.get("commonName", "Unknown"),
                    "subject": subject_dict.get("commonName", hostname),
                    "expires": not_after or "Unknown",
                    "days_left": days_left,
                    "san_count": len(sans),
                }
    except Exception as e:
        ssl_data["error"] = str(e)

    return ssl_data


def inspect_http_technologies(url: str, timeout: float = 4.0) -> Dict[str, Any]:
    """
    Fingerprints web server software, frameworks, CDN/WAF, and security headers.
    """
    tech_data = {
        "status_code": None,
        "server": "Undisclosed / Hidden",
        "powered_by": "None disclosed",
        "cdn_waf": "Direct Origin / No CDN detected",
        "security_headers": {
            "strict_transport_security": "Missing",
            "content_security_policy": "Missing",
            "x_frame_options": "Missing",
            "x_content_type_options": "Missing",
            "referrer_policy": "Missing"
        }
    }

    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ProxyShield-SecurityScanner/1.0"}
            )
            tech_data["status_code"] = resp.status_code
            headers = {k.lower(): v for k, v in resp.headers.items()}

            if "server" in headers:
                tech_data["server"] = headers["server"]
            if "x-powered-by" in headers:
                tech_data["powered_by"] = headers["x-powered-by"]

            srv_lower = tech_data["server"].lower()
            if "cf-ray" in headers or "cf-cache-status" in headers or "cloudflare" in srv_lower:
                tech_data["cdn_waf"] = "Cloudflare WAF / Edge CDN"
            elif "x-amz-cf-id" in headers or "x-amz-cf-pop" in headers:
                tech_data["cdn_waf"] = "Amazon CloudFront CDN"
            elif "x-akamai-transformed" in headers or "akamai" in srv_lower:
                tech_data["cdn_waf"] = "Akamai Edge WAF"
            elif "x-sucuri-id" in headers or "sucuri" in srv_lower:
                tech_data["cdn_waf"] = "Sucuri CloudProxy WAF"
            elif "x-fastly-request-id" in headers:
                tech_data["cdn_waf"] = "Fastly Edge Cloud"
            elif "x-cdn" in headers and "incapsula" in headers.get("x-cdn", "").lower():
                tech_data["cdn_waf"] = "Imperva Incapsula WAF"

            sec = tech_data["security_headers"]
            sec["strict_transport_security"] = headers.get("strict-transport-security", "Missing")
            sec["content_security_policy"] = "Configured" if "content-security-policy" in headers else "Missing"
            sec["x_frame_options"] = headers.get("x-frame-options", "Missing")
            sec["x_content_type_options"] = headers.get("x-content-type-options", "Missing")
            sec["referrer_policy"] = headers.get("referrer-policy", "Missing")
    except Exception as e:
        tech_data["error"] = str(e)

    return tech_data


def scan_domain(target: str) -> Dict[str, Any]:
    """
    Executes a comprehensive Nmap-style domain reconnaissance and profiling scan.
    """
    hostname, scheme, port = clean_target_hostname(target)
    start_time = time.perf_counter()

    # 1. DNS Resolution
    resolved_ipv4 = "Unknown"
    resolved_ipv6 = "None detected"
    reverse_ptr = "None"

    try:
        resolved_ipv4 = socket.gethostbyname(hostname)
        try:
            ptr_info = socket.gethostbyaddr(resolved_ipv4)
            reverse_ptr = ptr_info[0] if ptr_info else "None"
        except Exception:
            pass
    except Exception as e:
        resolved_ipv4 = f"Resolution error: {e}"

    try:
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_INET6)
        ipv6_list = list(set([x[4][0] for x in addr_info]))
        if ipv6_list:
            resolved_ipv6 = ipv6_list[0]
    except Exception:
        pass

    # 2. DNS Records
    dns_records = query_dns_records(hostname)

    # 3. Port Scan & Service Detection
    open_ports = scan_target_ports(hostname)

    # 4. SSL/TLS Certificate Analysis
    ssl_info = inspect_ssl_certificate(hostname, port=443) if 443 in [p["port"] for p in open_ports] or scheme == "https" else {"ssl_active": False}

    # 5. Web Technology & Headers
    target_url = f"{scheme}://{hostname}"
    tech_info = inspect_http_technologies(target_url)

    elapsed = round(time.perf_counter() - start_time, 2)

    return {
        "target": target,
        "hostname": hostname,
        "scheme": scheme,
        "ipv4": resolved_ipv4,
        "ipv6": resolved_ipv6,
        "reverse_ptr": reverse_ptr,
        "dns_records": dns_records,
        "open_ports": open_ports,
        "ssl": ssl_info,
        "technologies": tech_info,
        "scan_duration_seconds": elapsed,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def render_domain_scan_results(scan: Dict[str, Any]) -> None:
    """
    Renders Nmap-style domain security scan results on the terminal using Rich.
    """
    console = Console()

    console.print(f"\n[bold green]🛡️  ProxyShield Domain Security Scanner (Nmap-Style Recon)[/bold green]")
    console.print(f"[dim]Author: Quarkova | https://quarkova.com | Scan Duration: {scan.get('scan_duration_seconds', 0)}s[/dim]\n")

    # Panel: Target Host & DNS Details
    host_text = (
        f"[bold white]Target Domain   :[/bold white] [cyan]{scan['hostname']}[/cyan]\n"
        f"[bold white]IPv4 Address    :[/bold white] [bold green]{scan['ipv4']}[/bold green]\n"
        f"[bold white]IPv6 Address    :[/bold white] [bright_blue]{scan['ipv6']}[/bright_blue]\n"
        f"[bold white]Reverse PTR Host:[/bold white] [yellow]{scan['reverse_ptr']}[/yellow]\n"
    )
    if scan.get("dns_records", {}).get("NS"):
        host_text += f"[bold white]Name Servers    :[/bold white] [dim]{', '.join(scan['dns_records']['NS'][:3])}[/dim]\n"
    if scan.get("dns_records", {}).get("MX"):
        host_text += f"[bold white]Mail Servers    :[/bold white] [dim]{', '.join(scan['dns_records']['MX'][:2])}[/dim]\n"

    console.print(Panel(host_text, title="[bold yellow]Target Host & DNS Intelligence[/bold yellow]", border_style="cyan"))

    # Table: Open Ports & Services
    open_ports = scan.get("open_ports", [])
    port_table = Table(
        title=f"[bold cyan]Port Scan & Active Services ({len(open_ports)} open ports discovered)[/bold cyan]",
        box=box.ROUNDED,
        header_style="bold yellow"
    )
    port_table.add_column("PORT", style="bold white", width=10)
    port_table.add_column("STATE", style="bold green", width=10)
    port_table.add_column("SERVICE", style="cyan", width=16)
    port_table.add_column("VERSION / BANNER / DETAILS", style="bright_white")

    if open_ports:
        for p in open_ports:
            state_badge = "[bold green]OPEN[/bold green]"
            port_table.add_row(f"{p['port']}/tcp", state_badge, p["service"], p.get("banner", p["description"]))
    else:
        port_table.add_row("-", "[yellow]FILTERED[/yellow]", "None open", "Standard web ports closed or firewalled")

    console.print(port_table)

    # SSL/TLS Certificate Panel
    ssl_info = scan.get("ssl", {})
    if ssl_info.get("ssl_active"):
        days = ssl_info.get("days_left")
        days_str = f"[bold green]{days} days remaining[/bold green]" if days and days > 30 else f"[bold yellow]{days} days[/bold yellow]"
        ssl_text = (
            f"[bold white]Active TLS Protocol :[/bold white] [bold green]{ssl_info.get('tls_version')}[/bold green]\n"
            f"[bold white]Negotiated Cipher   :[/bold white] [cyan]{ssl_info.get('cipher')}[/cyan]\n"
            f"[bold white]Certificate Issuer  :[/bold white] [bright_white]{ssl_info.get('issuer')}[/bright_white]\n"
            f"[bold white]Subject Common Name :[/bold white] [bright_white]{ssl_info.get('subject')}[/bright_white]\n"
            f"[bold white]SANs Alt Domains    :[/bold white] [bright_blue]{ssl_info.get('san_count')} hostnames[/bright_blue]\n"
            f"[bold white]Certificate Expiry  :[/bold white] {ssl_info.get('expires')} ({days_str})"
        )
        console.print(Panel(ssl_text, title="[bold green]🔒 SSL/TLS Certificate Security Profiling[/bold green]", border_style="green"))

    # Web Technology & Security Headers Panel
    tech = scan.get("technologies", {})
    sec = tech.get("security_headers", {})

    def _badge(val: str) -> str:
        if val in ("Missing", "None disclosed"):
            return f"[bold red]✗ {val}[/bold red]"
        return f"[bold green]✓ {val}[/bold green]"

    tech_text = (
        f"[bold white]Web Server Software :[/bold white] [cyan]{tech.get('server', 'Undisclosed')}[/cyan]\n"
        f"[bold white]Backend Stack       :[/bold white] [bright_white]{tech.get('powered_by', 'None disclosed')}[/bright_white]\n"
        f"[bold white]WAF / CDN Protection:[/bold white] [bold magenta]{tech.get('cdn_waf', 'Direct Origin')}[/bold magenta]\n"
        f"\n[bold yellow]Security Headers Audit:[/bold yellow]\n"
        f"  • Strict-Transport-Security (HSTS) : {_badge(sec.get('strict_transport_security', 'Missing'))}\n"
        f"  • Content-Security-Policy (CSP)    : {_badge(sec.get('content_security_policy', 'Missing'))}\n"
        f"  • X-Frame-Options (Clickjacking)   : {_badge(sec.get('x_frame_options', 'Missing'))}\n"
        f"  • X-Content-Type-Options (MIME)    : {_badge(sec.get('x_content_type_options', 'Missing'))}\n"
        f"  • Referrer-Policy                  : {_badge(sec.get('referrer_policy', 'Missing'))}\n"
    )
    console.print(Panel(tech_text, title="[bold cyan]🌐 Web Server & Security Headers Intelligence[/bold cyan]", border_style="cyan"))
