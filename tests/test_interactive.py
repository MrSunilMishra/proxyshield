"""
Unit tests for ProxyShield Interactive Interface (REPL)
Validates Termux-SSH style ASCII cow-box branding, command help table,
and interactive command parsing.
"""

import sys
import io
import pytest
from proxyshield.interactive import (
    get_interactive_header,
    print_interactive_help,
    start_interactive_shell,
)
from proxyshield.cli import build_parser, normalize_aliases


def test_interactive_header_branding():
    header = get_interactive_header()
    assert "< ProxyShield >" in header
    assert "A tool by Quarkova" in header
    assert "+------------------------------------+" in header
    assert "[Note]" in header


def test_interactive_help_table(capsys):
    print_interactive_help()
    captured = capsys.readouterr().out
    assert "+-------------+------------------------------------------------------+" in captured
    assert "command" in captured
    assert "description" in captured
    assert "help" in captured
    assert "proxy" in captured
    assert "check" in captured
    assert "random" in captured
    assert "audit" in captured
    assert "ip" in captured
    assert "banner" in captured
    assert "config" in captured
    assert "report" in captured
    assert "exit" in captured


def test_interactive_shell_exit_command(monkeypatch, capsys):
    # Simulate user typing 'exit'
    monkeypatch.setattr("builtins.input", lambda prompt="": "exit")
    ret = start_interactive_shell()
    assert ret == 0
    captured = capsys.readouterr().out
    assert "Exiting. Stay safe and secure!" in captured


def test_interactive_cli_argument_parser():
    parser = build_parser()
    args = parser.parse_args(["-i"])
    assert args.interactive is True

    args2 = parser.parse_args(["interactive"])
    assert args2.command == "interactive"

    args3 = parser.parse_args(["i"])
    args3 = normalize_aliases(args3)
    assert args3.command == "interactive"
