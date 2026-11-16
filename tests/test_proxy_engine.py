"""
Unit tests for ProxyShield Multi-Source Free Proxy Engine
"""

import tempfile
import os
from proxyshield.proxy_engine import (
    fetch_free_proxies,
    export_proxies_to_file,
    get_random_free_proxy,
)


def test_proxy_structure_and_keys():
    # Fetch 3 proxies from Geonode
    proxies = fetch_free_proxies(source="geonode", limit=3)
    assert len(proxies) <= 3
    if proxies:
        p = proxies[0]
        assert "proxy" in p
        assert "ip" in p
        assert "port" in p
        assert "protocol" in p
        assert "country_code" in p
        assert "timeout_ms" in p
        assert p["source"] == "Geonode"


def test_proxy_filtering_protocol():
    proxies = fetch_free_proxies(source="geonode", protocol="socks5", limit=5)
    for p in proxies:
        assert p["protocol"] == "socks5"


def test_proxy_export_txt_and_json():
    sample = [
        {"proxy": "http://1.1.1.1:80", "ip": "1.1.1.1", "port": 80, "protocol": "http"},
        {"proxy": "socks5://2.2.2.2:1080", "ip": "2.2.2.2", "port": 1080, "protocol": "socks5"}
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        txt_path = os.path.join(tmpdir, "proxies.txt")
        ok_txt, msg_txt = export_proxies_to_file(sample, txt_path, file_format="txt")
        assert ok_txt is True
        assert os.path.exists(txt_path)
        with open(txt_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines()]
            assert "http://1.1.1.1:80" in lines

        json_path = os.path.join(tmpdir, "proxies.json")
        ok_json, msg_json = export_proxies_to_file(sample, json_path, file_format="json")
        assert ok_json is True
        assert os.path.exists(json_path)


def test_random_proxy():
    p = get_random_free_proxy(source="geonode")
    if p:
        assert "://" in p.get("proxy", "")
