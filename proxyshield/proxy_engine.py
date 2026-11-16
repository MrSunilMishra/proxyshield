"""
ProxyShield Free Proxy Engine & Diagnostics
Multi-source free proxy aggregator supporting:
  1. ProxyScrape v4 API
  2. Geonode Proxy List API
Combines, deduplicates, filters, verifies, and benchmarks live proxies.

Author: Quarkova
Website: https://quarkova.com
"""

import os
import sys
import json
import time
import socket
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from rich.console import Console
from rich.table import Table
from rich import box

from proxyshield.color_engine import colorize_text, RESET, BOLD

PROXYSCRAPE_API_URL = (
    "https://api.proxyscrape.com/v4/free-proxy-list/get"
    "?request=display_proxies&proxy_format=protocolipport&format=json"
)

GEONODE_API_URL = (
    "https://proxylist.geonode.com/api/proxy-list"
    "?page=1&limit=500&sort_by=responseTime&sort_type=asc"
)

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 ProxyShield/1.0.0"


def fetch_proxyscrape_proxies(timeout: int = 10) -> List[Dict[str, Any]]:
    """Fetches and normalizes fresh proxies from ProxyScrape v4 API (no stale cache)."""
    api_url = f"{PROXYSCRAPE_API_URL}&_nocache={int(time.time())}"
    req = urllib.request.Request(
        api_url,
        headers={
            "User-Agent": DEFAULT_USER_AGENT,
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache"
        }
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    results = []
    for item in payload.get("proxies", []):
        if not item.get("alive", False):
            continue
        ip_data = item.get("ip_data") or {}
        proto = item.get("protocol", "http").lower()
        endpoint = item.get("proxy", "")
        ip = endpoint.split("://")[-1].split(":")[0] if "://" in endpoint else endpoint.split(":")[0]
        port = int(item.get("port") or (endpoint.split(":")[-1] if ":" in endpoint else 80))

        results.append({
            "source": "ProxyScrape",
            "proxy": endpoint,
            "protocol": proto,
            "ip": ip,
            "port": port,
            "country_code": ip_data.get("countryCode", "").upper(),
            "country_name": ip_data.get("country", "Unknown"),
            "city": ip_data.get("city", ""),
            "anonymity": item.get("anonymity", "unknown").lower(),
            "ssl": item.get("ssl", False),
            "timeout_ms": int(item.get("timeout") or 9999),
            "uptime": float(item.get("uptime") or 0),
        })
    return results


def fetch_geonode_proxies(limit: int = 500, timeout: int = 10) -> List[Dict[str, Any]]:
    """Fetches and normalizes fresh proxies from Geonode API (no stale cache)."""
    url = f"https://proxylist.geonode.com/api/proxy-list?page=1&limit={limit}&sort_by=responseTime&sort_type=asc&_nocache={int(time.time())}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": DEFAULT_USER_AGENT,
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache"
        }
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    results = []
    for item in payload.get("data", []):
        ip = item.get("ip", "")
        port = int(item.get("port", 80))
        protocols = item.get("protocols") or ["http"]
        proto = protocols[0].lower() if protocols else "http"
        endpoint = f"{proto}://{ip}:{port}"
        country_code = item.get("country", "").upper()
        anon = item.get("anonymityLevel", "unknown").lower()
        ssl_support = "https" in [p.lower() for p in protocols] or proto == "https"
        resp_time = int(item.get("responseTime") or item.get("latency") or 9999)
        uptime = float(item.get("upTime") or 0)

        results.append({
            "source": "Geonode",
            "proxy": endpoint,
            "protocol": proto,
            "ip": ip,
            "port": port,
            "country_code": country_code,
            "country_name": item.get("country", country_code),
            "city": item.get("city", ""),
            "anonymity": anon,
            "ssl": ssl_support,
            "timeout_ms": resp_time,
            "uptime": uptime,
        })
    return results


def fetch_free_proxies(
    source: str = "all",
    protocol: Optional[str] = None,
    country: Optional[str] = None,
    anonymity: Optional[str] = None,
    ssl_only: bool = False,
    max_timeout: Optional[int] = None,
    limit: Optional[int] = None,
    timeout: int = 10
) -> List[Dict[str, Any]]:
    """
    Fetches, aggregates, deduplicates, and filters proxies from multiple providers.
    Sources supported: 'all', 'geonode', 'proxyscrape'.
    """
    candidates: List[Dict[str, Any]] = []
    source_lower = (source or "all").lower()

    if source_lower == "geonode":
        candidates = fetch_geonode_proxies(limit=limit or 500, timeout=timeout)
    elif source_lower == "proxyscrape":
        candidates = fetch_proxyscrape_proxies(timeout=timeout)
    else:
        # Fetch concurrently from both Geonode & ProxyScrape
        with ThreadPoolExecutor(max_workers=2) as executor:
            fut_geo = executor.submit(fetch_geonode_proxies, limit=500, timeout=timeout)
            fut_scr = executor.submit(fetch_proxyscrape_proxies, timeout=timeout)

            try:
                candidates.extend(fut_geo.result())
            except Exception:
                pass  # Fallback gracefully if one API is momentarily slow

            try:
                candidates.extend(fut_scr.result())
            except Exception:
                pass

    # Deduplicate by (IP, Port)
    seen = set()
    deduped: List[Dict[str, Any]] = []
    for item in candidates:
        key = (item["ip"], item["port"])
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    # Apply Filters
    filtered: List[Dict[str, Any]] = []
    for item in deduped:
        p_proto = item.get("protocol", "").lower()
        p_country = item.get("country_code", "").upper()
        p_anon = item.get("anonymity", "").lower()
        p_ssl = item.get("ssl", False)
        p_timeout = item.get("timeout_ms", 99999)

        if protocol and protocol.lower() != "all" and p_proto != protocol.lower():
            continue

        if country and country.upper() != "ALL" and p_country != country.upper():
            continue

        if anonymity and anonymity.lower() != "all" and p_anon != anonymity.lower():
            continue

        if ssl_only and not p_ssl:
            continue

        if max_timeout is not None and p_timeout > max_timeout:
            continue

        filtered.append(item)

    # Sort by fastest latency/response time
    filtered.sort(key=lambda x: x.get("timeout_ms", 99999))

    if limit and len(filtered) > limit:
        filtered = filtered[:limit]

    return filtered


def test_proxy_connectivity(
    proxy_url: str,
    test_target: str = "http://httpbin.org/ip",
    timeout: int = 5
) -> Tuple[bool, int, str]:
    """
    Tests live proxy connectivity and measures real round-trip latency in milliseconds.
    Returns (is_alive, latency_ms, details).
    """
    start_time = time.perf_counter()
    proto = proxy_url.split("://")[0].lower() if "://" in proxy_url else "http"

    try:
        proxy_handler = urllib.request.ProxyHandler({
            proto: proxy_url,
            "http": proxy_url,
            "https": proxy_url
        })
        opener = urllib.request.build_opener(proxy_handler)
        req = urllib.request.Request(test_target, headers={"User-Agent": DEFAULT_USER_AGENT})

        with opener.open(req, timeout=timeout) as resp:
            data = resp.read(256)
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            return True, elapsed_ms, "Connected successfully"
    except urllib.error.HTTPError as he:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        return False, elapsed_ms, f"HTTP Error {he.code}"
    except Exception as e:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        return False, elapsed_ms, str(e)


def diagnose_proxies_concurrent(
    proxies: List[Dict[str, Any]],
    max_workers: int = 15,
    timeout: int = 4
) -> List[Dict[str, Any]]:
    """
    Diagnoses a batch of proxies concurrently.
    """
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(test_proxy_connectivity, item["proxy"], timeout=timeout): item
            for item in proxies
        }

        for future in as_completed(future_map):
            item = future_map[future]
            try:
                alive, latency, details = future.result()
                res = dict(item)
                res["verified_alive"] = alive
                res["measured_latency_ms"] = latency
                res["diagnostic_detail"] = details
                results.append(res)
            except Exception as ex:
                res = dict(item)
                res["verified_alive"] = False
                res["measured_latency_ms"] = 0
                res["diagnostic_detail"] = str(ex)
                results.append(res)

    # Sort: verified alive first, then by measured latency
    results.sort(key=lambda x: (not x.get("verified_alive", False), x.get("measured_latency_ms", 99999)))
    return results


def render_proxy_table(
    proxies: List[Dict[str, Any]],
    title: str = "ProxyShield Multi-Source Free Proxy Pool",
    verified: bool = False
) -> None:
    """
    Renders an elegant Rich table displaying proxies and health metrics.
    """
    console = Console()
    table = Table(
        title=f"\n[bold cyan]🛡️  {title} ({len(proxies)} proxies)[/bold cyan]",
        box=box.ROUNDED,
        header_style="bold yellow",
        show_lines=False
    )

    table.add_column("Provider", style="dim cyan", no_wrap=True)
    table.add_column("Protocol", style="cyan", no_wrap=True)
    table.add_column("Proxy Endpoint (IP:Port)", style="bright_white", no_wrap=True)
    table.add_column("Country", style="bright_blue")
    table.add_column("Anonymity", style="magenta")
    table.add_column("SSL", style="green")

    if verified:
        table.add_column("Status", justify="center")
        table.add_column("Measured Latency", justify="right")
    else:
        table.add_column("API Latency", justify="right")
        table.add_column("Uptime", justify="right")

    for p in proxies:
        provider = p.get("source", "API")
        proto = p.get("protocol", "http").upper()
        endpoint = p.get("proxy", "")
        country = f"{p.get('country_code', '??')} ({p.get('city') or p.get('country_name', '')})"
        anon = p.get("anonymity", "unknown").capitalize()
        ssl_badge = "[green]✓ Yes[/green]" if p.get("ssl") else "[dim]No[/dim]"

        if verified:
            is_alive = p.get("verified_alive", False)
            status_badge = "[green]ALIVE[/green]" if is_alive else "[red]DEAD[/red]"
            lat = f"{p.get('measured_latency_ms', 0)} ms"
            if is_alive and p.get("measured_latency_ms", 9999) < 800:
                lat_style = f"[green]{lat}[/green]"
            elif is_alive:
                lat_style = f"[yellow]{lat}[/yellow]"
            else:
                lat_style = f"[dim red]{lat}[/dim red]"
            table.add_row(provider, proto, endpoint, country, anon, ssl_badge, status_badge, lat_style)
        else:
            api_lat = f"{p.get('timeout_ms', 0)} ms"
            uptime = f"{int(p.get('uptime', 0))}%"
            table.add_row(provider, proto, endpoint, country, anon, ssl_badge, api_lat, uptime)

    console.print(table)


def export_proxies_to_file(
    proxies: List[Dict[str, Any]],
    output_path: str,
    file_format: str = "txt"
) -> Tuple[bool, str]:
    """Exports proxies to a TXT or JSON file."""
    try:
        dir_name = os.path.dirname(os.path.abspath(output_path))
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        if file_format.lower() == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(proxies, f, indent=2)
        else:
            with open(output_path, "w", encoding="utf-8") as f:
                for p in proxies:
                    f.write(p.get("proxy", "") + "\n")
        return True, f"Successfully exported {len(proxies)} proxies to '{output_path}'."
    except Exception as e:
        return False, f"Failed to export proxies: {e}"


def get_random_free_proxy(
    source: str = "all",
    protocol: Optional[str] = None,
    country: Optional[str] = None,
    anonymity: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Returns a single random free proxy."""
    import random
    proxies = fetch_free_proxies(
        source=source,
        protocol=protocol,
        country=country,
        anonymity=anonymity,
        limit=50
    )
    if proxies:
        return random.choice(proxies)
    return None
