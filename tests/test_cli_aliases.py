"""
Unit tests for ProxyShield CLI Aliases (pxs, p, a, b, c) and Help Functions (-h, --help)
"""

import pytest
from proxyshield.cli import build_parser, normalize_aliases


def test_parser_short_aliases_proxy():
    parser = build_parser()
    args = parser.parse_args(["p", "f", "--protocol", "socks5", "-n", "5"])
    assert args.command == "p"
    assert args.proxy_action == "f"
    assert args.protocol == "socks5"
    assert args.limit == 5

    # Normalize
    args = normalize_aliases(args)
    assert args.command == "proxy"
    assert args.proxy_action == "fetch"


def test_parser_short_aliases_audit():
    parser = build_parser()
    args = parser.parse_args(["a", "-t", "https://example.com", "-n", "10", "-d", "0.5"])
    assert args.command == "a"
    assert args.target == "https://example.com"
    assert args.limit == 10
    assert args.delay == 0.5

    args = normalize_aliases(args)
    assert args.command == "audit"


def test_parser_short_aliases_banner():
    parser = build_parser()
    args = parser.parse_args(["b", "-t", "HELLO", "-f", "3d", "-g", "red,blue", "-a", "center"])
    assert args.command == "b"
    assert args.text == "HELLO"
    assert args.font == "3d"
    assert args.gradient == "red,blue"
    assert args.align == "center"

    args = normalize_aliases(args)
    assert args.command == "banner"


def test_parser_short_aliases_config():
    parser = build_parser()
    args = parser.parse_args(["c", "s"])
    assert args.command == "c"
    assert args.action == "s"

    args = normalize_aliases(args)
    assert args.command == "config"
    assert args.action == "show"


def test_help_and_version_flags(capsys):
    parser = build_parser()

    # --version
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["-v"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "ProxyShield (pxs)" in captured.out or "ProxyShield (pxs)" in captured.err

    # -h
    with pytest.raises(SystemExit) as exc_h:
        parser.parse_args(["-h"])
    assert exc_h.value.code == 0
    captured_h = capsys.readouterr()
    assert "pxs" in captured_h.out
