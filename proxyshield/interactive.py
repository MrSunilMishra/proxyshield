"""
ProxyShield Interactive Terminal Interface (REPL)
Provides a menu-driven, interactive command-line experience
styled like Termux-SSH with ASCII box branding and interactive prompts.

Author: Quarkova
Website: https://quarkova.com
License: MIT
"""

import sys
import os
import shlex
import webbrowser
import glob
from typing import List, Optional

try:
    import readline  # Enable arrow key navigation & command history on Linux/macOS/Termux
except ImportError:
    pass

from proxyshield import __version__, __author__, __organization__, __website__
from proxyshield.color_engine import colorize_text, RESET, BOLD
from proxyshield.security_shield import StrictProxyShield, LEGAL_PRIVACY_NOTICE, DirectIPExposureError
from proxyshield.proxy_engine import (
    fetch_free_proxies,
    diagnose_proxies_concurrent,
    render_proxy_table,
    get_random_free_proxy,
    export_proxies_to_file,
)
from proxyshield.auditor import NetworkAuditEngine
from proxyshield.reporter import export_multi_format_reports
from proxyshield.branding import render_branding_banner
from proxyshield.config_manager import (
    get_config_path,
    ensure_config_exists,
    check_permissions,
    enforce_permissions,
    validate_config,
    reset_config,
    open_editor,
)


def get_interactive_header() -> str:
    """Returns the branded ProxyShield CFonts banner matching the tool theme."""
    banner = render_branding_banner()
    note_line = (
        colorize_text("\n[Note] ", "bright_yellow", bold=True)
        + colorize_text("ProxyShield Public Proxy Intelligence & Authorized Security Auditor.\n", "white")
        + colorize_text("Type 'help' to view available commands, or 'exit' to quit.\n", "bright_cyan")
    )
    return banner + "\n" + note_line


def print_interactive_help() -> None:
    """Prints the command table in exact ASCII box format."""
    table_lines = [
        "+-------------+------------------------------------------------------+",
        "|   command   |                     description                      |",
        "+-------------+------------------------------------------------------+",
        "|    help     | show available commands and descriptions             |",
        "|    clear    | clears console screen                                |",
        "|    proxy    | fetch and display live free proxies                  |",
        "|    fetch    | fetch proxies with protocol/country filters          |",
        "|    check    | test live connectivity & latency across proxies      |",
        "|   random    | get a single fast working proxy URL                  |",
        "|    audit    | conduct strict proxy security audit on target URL    |",
        "|     ip      | check operator real public IP & direct-IP guard      |",
        "|   banner    | render CFonts typography branding banner             |",
        "|   config    | show, validate, or edit branding configuration       |",
        "|   report    | view / open generated audit security reports         |",
        "|   version   | display version, author (Quarkova) & license         |",
        "|    exit     | exit ProxyShield interactive console                 |",
        "+-------------+------------------------------------------------------+",
    ]
    for idx, line in enumerate(table_lines):
        if idx in (0, 1, 2, len(table_lines) - 1):
            print(colorize_text(line, "bright_green"))
        else:
            parts = line.split("|")
            if len(parts) >= 3:
                cmd_col = colorize_text(parts[1], "bright_cyan", bold=True)
                desc_col = colorize_text(parts[2], "white")
                border = colorize_text("|", "bright_green")
                print(f"{border}{cmd_col}{border}{desc_col}{border}")
            else:
                print(colorize_text(line, "bright_green"))


def handle_interactive_audit(cmd_args: List[str]) -> None:
    """Handles the `audit` command within the interactive shell."""
    target_url = None
    limit = 10
    delay = 1.0

    if cmd_args:
        # Check if first arg is target or flags
        if cmd_args[0].startswith("http://") or cmd_args[0].startswith("https://"):
            target_url = cmd_args[0]
        elif not cmd_args[0].startswith("-"):
            target_url = cmd_args[0]
        else:
            # Parse flags
            import argparse
            p = argparse.ArgumentParser()
            p.add_argument("-t", "--target", type=str)
            p.add_argument("-n", "--limit", type=int, default=10)
            p.add_argument("-d", "--delay", type=float, default=1.0)
            try:
                parsed, _ = p.parse_known_args(cmd_args)
                target_url = parsed.target
                limit = parsed.limit or 10
                delay = parsed.delay or 1.0
            except Exception:
                pass

    if not target_url:
        print(colorize_text("Enter authorized target URL (e.g. https://example.com): ", "bright_cyan"), end="")
        try:
            target_url = input().strip()
        except (KeyboardInterrupt, EOFError):
            print()
            return

    if not target_url:
        print(colorize_text("Audit aborted: No target URL provided.", "bright_yellow"))
        return

    if not target_url.startswith("http://") and not target_url.startswith("https://"):
        target_url = "https://" + target_url

    print(colorize_text(f"\n[Audit Target] {target_url}", "bright_white", bold=True))
    shield = StrictProxyShield()
    print(colorize_text(f"[Direct-IP Guard] Baseline Operator IP: {shield.operator_direct_ip}", "bright_cyan"))
    print(colorize_text("[Direct-IP Guard] Direct connection fallback: DISABLED (Enforced)", "bright_green", bold=True))

    print(colorize_text(f"\n[1/3] Fetching candidate proxy pool (limit: {limit})...", "bright_cyan"))
    proxies = fetch_free_proxies(source="all", limit=limit)
    if not proxies:
        print(colorize_text("Error: Could not retrieve proxies for audit.", "bright_red"))
        return

    print(colorize_text(f"Fetched {len(proxies)} candidate proxies. Beginning sequential low-rate testing...", "bright_yellow"))
    auditor = NetworkAuditEngine(shield=shield)
    audit_data = auditor.audit_target(
        target_url=target_url,
        proxies=proxies,
        rate_limit_delay=delay,
        max_requests=limit,
        timeout=6
    )

    print(colorize_text("\n[2/3] Diagnostic Request Breakdown:", "bright_yellow", bold=True))
    for r in audit_data.get("results", []):
        status_str = f"HTTP {r['status_code']}" if r.get('status_code') else r.get('category')
        cat = r.get('category', 'UNKNOWN')
        col = 'bright_green' if cat == 'SUCCESS' else ('bright_yellow' if '403' in cat or '429' in cat else 'bright_red')
        print(f"  • {r['endpoint'].ljust(35)} Exit IP: {str(r.get('exit_ip')).ljust(16)} -> {colorize_text(status_str, col)} ({r.get('latency_ms', 0)} ms)")

    report_base = "audit_report"
    print(colorize_text(f"\n[3/3] Generating multi-format audit reports ({report_base}.*)...", "bright_cyan"))
    out_files = export_multi_format_reports(audit_data, report_base)
    for fmt, pth in out_files.items():
        print(colorize_text(f"  ✓ {fmt.upper()} Report: {os.path.abspath(pth)}", "bright_green"))

    print(colorize_text("\nAudit completed under strict proxy-only mode. Type 'report' to open HTML report.\n", "bright_cyan", bold=True))


def handle_interactive_proxy(cmd_args: List[str]) -> None:
    """Handles proxy fetching and listing in the interactive shell."""
    source = "all"
    protocol = None
    country = None
    limit = 15

    # Check for simple arguments: e.g. `proxy geonode`, `proxy socks5`, `proxy 20`
    idx = 0
    while idx < len(cmd_args):
        arg = cmd_args[idx]
        if arg in ("geonode", "proxyscrape", "all"):
            source = arg
        elif arg.lower() in ("http", "https", "socks4", "socks5"):
            protocol = arg.lower()
        elif len(arg) == 2 and arg.isalpha():
            country = arg.upper()
        elif arg.isdigit():
            limit = int(arg)
        elif arg in ("-s", "--source") and idx + 1 < len(cmd_args):
            idx += 1
            source = cmd_args[idx]
        elif arg in ("-p", "--protocol") and idx + 1 < len(cmd_args):
            idx += 1
            protocol = cmd_args[idx]
        elif arg in ("-c", "--country") and idx + 1 < len(cmd_args):
            idx += 1
            country = cmd_args[idx]
        elif arg in ("-n", "-l", "--limit") and idx + 1 < len(cmd_args):
            idx += 1
            limit = int(cmd_args[idx])
        idx += 1

    source_label = "ProxyScrape + Geonode" if source == "all" else source.capitalize()
    print(colorize_text(f"\n[ProxyShield] Querying free proxy pool ({source_label})...", "bright_cyan"))
    try:
        proxies = fetch_free_proxies(
            source=source,
            protocol=protocol,
            country=country,
            limit=limit
        )
    except Exception as e:
        print(colorize_text(f"Error fetching proxies: {e}", "bright_red"))
        return

    if not proxies:
        print(colorize_text("No proxies matched your filter criteria.", "bright_yellow"))
        return

    render_proxy_table(proxies, title="ProxyShield Free Proxy Pool")


def handle_interactive_check(cmd_args: List[str]) -> None:
    """Runs concurrent diagnostics on live proxies."""
    limit = 10
    if cmd_args and cmd_args[0].isdigit():
        limit = int(cmd_args[0])

    print(colorize_text(f"\n[ProxyShield] Fetching {limit} proxies for live diagnostic testing...", "bright_cyan"))
    proxies = fetch_free_proxies(source="all", limit=limit)
    if not proxies:
        print(colorize_text("Error: Could not retrieve proxies.", "bright_red"))
        return

    print(colorize_text(f"Testing live reachability across {len(proxies)} endpoints concurrently...", "bright_yellow"))
    diagnosed = diagnose_proxies_concurrent(proxies, max_workers=15, timeout=4)
    render_proxy_table(diagnosed, title="ProxyShield Live Diagnostic Results", verified=True)


def handle_interactive_reports(cmd_args: List[str] = None) -> None:
    """Launches local web server dashboard and opens reports in browser."""
    from proxyshield.web_server import start_report_server, _ACTIVE_PORT
    port = 8080
    if cmd_args and cmd_args[0].isdigit():
        port = int(cmd_args[0])

    print(colorize_text("\n[ProxyShield Report & Diagnostics Center]", "bright_cyan", bold=True))
    if _ACTIVE_PORT:
        local_url = f"http://127.0.0.1:{_ACTIVE_PORT}"
        domain_url = f"http://proxyshield.test:{_ACTIVE_PORT}"
        print(colorize_text(f"Dashboard web server already running at: {local_url}", "bright_green"))
        webbrowser.open(local_url)
    else:
        local_url, actual_port = start_report_server(port=port, open_browser=True, background=True)
        domain_url = f"http://proxyshield.test:{actual_port}"
        print(colorize_text(f"✓ Started background web server: {local_url}", "bright_green", bold=True))
        print(colorize_text(f"  • Custom Domain: {domain_url} (if mapped in hosts file)", "bright_cyan"))
        print(colorize_text(f"  • Tip: Add '127.0.0.1 proxyshield.test' to your system hosts file.", "gray"))
        webbrowser.open(local_url)

    print(colorize_text("Opened Report Dashboard in your default browser.\n", "white"))


def handle_interactive_ip() -> None:
    """Discovers and displays the operator's real public IP and direct-IP protection."""
    print(colorize_text("\n[Direct-IP Guard Verification]", "bright_cyan", bold=True))
    try:
        shield = StrictProxyShield()
        print(f"  • Operator Baseline Public IP : {colorize_text(str(shield.operator_direct_ip), 'bright_white', bold=True)}")
        print(f"  • Direct Fallback Policy      : {colorize_text('DISABLED (Enforced - No Fallback Allowed)', 'bright_green', bold=True)}")
        print(f"  • IP Exposure Guard Status    : {colorize_text('ACTIVE', 'bright_green', bold=True)}")
        print(colorize_text("\nYour direct IP is strictly safeguarded. Requests failing via proxy are aborted immediately.\n", "gray"))
    except Exception as e:
        print(colorize_text(f"Error checking IP: {e}", "bright_red"))


def handle_interactive_banner(cmd_args: List[str]) -> None:
    """Handles banner generation and previews in the interactive shell."""
    from proxyshield.banner import display_font_preview, display_font_list
    if not cmd_args:
        banner = render_branding_banner()
        print(banner)
        return

    first = cmd_args[0].lower()
    if first in ("--preview", "-p", "preview"):
        display_font_preview()
    elif first in ("--list-fonts", "-l", "fonts", "list"):
        display_font_list()
    else:
        text = " ".join(cmd_args)
        banner = render_branding_banner(text_override=text)
        print(banner)


def start_interactive_shell() -> int:
    """Main interactive REPL loop."""
    print(get_interactive_header())

    while True:
        try:
            # Styled prompt: ProxyShield >>
            prompt = colorize_text("ProxyShield", "bright_green", bold=True) + colorize_text(" >> ", "bright_yellow", bold=True)
            user_input = input(prompt).strip()
        except KeyboardInterrupt:
            print(colorize_text("\nUse 'exit' or Ctrl+D to quit ProxyShield.", "bright_yellow"))
            continue
        except EOFError:
            print(colorize_text("\n[ProxyShield] Exiting. Stay safe and secure!", "bright_green"))
            break

        if not user_input:
            continue

        try:
            tokens = shlex.split(user_input)
        except Exception:
            tokens = user_input.split()

        if not tokens:
            continue

        cmd = tokens[0].lower()
        cmd_args = tokens[1:]

        # Strip 'pxs' or 'proxyshield' prefix if user typed it inside REPL
        if cmd in ("pxs", "proxyshield"):
            if not cmd_args:
                continue
            cmd = cmd_args[0].lower()
            cmd_args = cmd_args[1:]

        try:
            if cmd in ("exit", "quit", "close", "q"):
                print(colorize_text("[ProxyShield] Exiting. Stay safe and secure!", "bright_green"))
                break

            elif cmd in ("help", "?", "-h", "--help"):
                print_interactive_help()

            elif cmd in ("clear", "cls"):
                os.system("cls" if os.name == "nt" else "clear")
                print(get_interactive_header())

            elif cmd in ("proxy", "proxies", "p"):
                if cmd_args and cmd_args[0] in ("check", "c"):
                    handle_interactive_check(cmd_args[1:])
                elif cmd_args and cmd_args[0] in ("random", "r"):
                    p = get_random_free_proxy(source="all")
                    if p:
                        print(colorize_text(f"\n{p.get('proxy', '')}\n", "bright_green", bold=True))
                    else:
                        print(colorize_text("No working proxy found.", "bright_red"))
                else:
                    handle_interactive_proxy(cmd_args)

            elif cmd in ("fetch", "f"):
                handle_interactive_proxy(cmd_args)

            elif cmd in ("check", "c"):
                handle_interactive_check(cmd_args)

            elif cmd in ("random", "rand", "r"):
                proto = cmd_args[0] if cmd_args else None
                p = get_random_free_proxy(source="all", protocol=proto)
                if p:
                    print(colorize_text(f"\n{p.get('proxy', '')}\n", "bright_green", bold=True))
                else:
                    print(colorize_text("No matching free proxy found.", "bright_red"))

            elif cmd in ("audit", "a", "scan"):
                handle_interactive_audit(cmd_args)

            elif cmd in ("ip", "myip", "guard"):
                handle_interactive_ip()

            elif cmd in ("banner", "b"):
                handle_interactive_banner(cmd_args)

            elif cmd in ("config", "cfg"):
                sub = cmd_args[0] if cmd_args else "show"
                path = get_config_path()
                if sub == "show":
                    if not os.path.exists(path):
                        path = ensure_config_exists()
                    print(colorize_text(f"\n--- ProxyShield Configuration ({path}) ---", "bright_cyan", bold=True))
                    with open(path, "r", encoding="utf-8") as f:
                        print(f.read())
                elif sub == "validate":
                    ok, errs = validate_config(path)
                    if ok:
                        print(colorize_text("✓ Configuration is valid and secure.", "bright_green"))
                    else:
                        for e in errs:
                            print(colorize_text(f"✗ {e}", "bright_red"))
                elif sub == "edit":
                    open_editor(path)
                elif sub == "reset":
                    reset_config(path)
                    print(colorize_text("✓ Configuration reset to defaults.", "bright_green"))
                elif sub == "permissions":
                    ok, msg = check_permissions(path)
                    print(colorize_text(f"Permissions: {msg}", "bright_green" if ok else "bright_red"))

            elif cmd in ("report", "reports", "serve", "dashboard", "web"):
                handle_interactive_reports(cmd_args)

            elif cmd in ("version", "-v", "--version", "v"):
                print(f"\n{colorize_text('ProxyShield', 'bright_green', bold=True)} v{__version__}")
                print(f"Author       : {colorize_text(__author__, 'bright_cyan')}")
                print(f"Organization : {colorize_text(__organization__, 'bright_cyan')}")
                print(f"Website      : {colorize_text(__website__, 'bright_cyan')}")
                print(f"License      : MIT Open Source Network Security & Diagnostics Toolkit\n")

            else:
                print(colorize_text(f"[!] Unknown command: '{cmd}'. Type 'help' for available commands.", "bright_yellow"))
        except Exception as err:
            print(colorize_text(f"[Error] Failed to execute '{cmd}': {err}", "bright_red"))

    return 0
