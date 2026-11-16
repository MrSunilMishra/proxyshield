"""
ProxyShield Main CLI Entry Point
Handles commands: banner, config (show, validate, edit, reset, permissions),
and interactive startup branding menu.

Author: Quarkova
Website: https://quarkova.com
"""

import sys
import os
import argparse
from typing import List

from proxyshield import __version__, __author__, __organization__, __website__
from proxyshield.branding import render_branding_banner
from proxyshield.banner import add_banner_parser, handle_banner_cli
from proxyshield.config_manager import (
    get_config_path,
    ensure_config_exists,
    check_permissions,
    enforce_permissions,
    validate_config,
    reset_config,
    open_editor,
)
from proxyshield.color_engine import colorize_text, RESET, BOLD


def handle_config_cli(args: argparse.Namespace) -> int:
    """Handles `proxyshield config` subcommands."""
    action = args.action

    if action == "show":
        path = get_config_path()
        if not os.path.exists(path):
            path = ensure_config_exists()
        print(colorize_text(f"\n--- ProxyShield Configuration ({path}) ---", "bright_cyan", bold=True))
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("["):
                    print(colorize_text(line.strip(), "bright_yellow", bold=True))
                elif "=" in line:
                    k, v = line.split("=", 1)
                    print(f"  {colorize_text(k.strip(), 'cyan')} = {colorize_text(v.strip(), 'white')}")
                else:
                    print(line.rstrip())
        print()
        return 0

    elif action == "validate":
        path = get_config_path()
        print(colorize_text(f"Validating configuration at '{path}'...", "bright_cyan"))
        is_valid, messages = validate_config(path)
        for msg in messages:
            if "WARNING" in msg or "ERROR" in msg or "VIOLATION" in msg:
                print(colorize_text(msg, "bright_red"))
            else:
                print(colorize_text(msg, "bright_yellow"))
        if is_valid:
            print(colorize_text("✓ Configuration is valid and passes security checks.", "bright_green", bold=True))
            return 0
        else:
            print(colorize_text("✗ Configuration validation failed. Review the warnings above.", "bright_red", bold=True))
            return 1

    elif action == "edit":
        path = ensure_config_exists()
        print(colorize_text(f"Opening configuration '{path}' in system editor...", "bright_cyan"))
        ok, msg = open_editor(path)
        print(msg)
        return 0 if ok else 1

    elif action == "reset":
        path = get_config_path()
        if not args.yes:
            print(colorize_text(f"WARNING: This will reset '{path}' to factory defaults.", "bright_yellow", bold=True))
            confirm = input("Are you sure you want to proceed? [y/N]: ").strip().lower()
            if confirm not in ("y", "yes"):
                print("Reset cancelled.")
                return 0
        ok, msg = reset_config(path, force=True)
        if ok:
            print(colorize_text("✓ " + msg, "bright_green"))
            return 0
        else:
            print(colorize_text("✗ " + msg, "bright_red"))
            return 1

    elif action == "permissions":
        path = get_config_path()
        print(colorize_text(f"Checking permissions on '{path}'...", "bright_cyan"))
        ok, status_msg = check_permissions(path)
        if ok:
            print(colorize_text("✓ " + status_msg, "bright_green"))
        else:
            print(colorize_text("! " + status_msg, "bright_red"))

        # Enforce if requested or if insecure
        if args.fix or not ok:
            print(colorize_text("\nEnforcing owner-only permissions (0700 dir, 0600 file)...", "bright_yellow"))
            enf_ok, enf_msg = enforce_permissions(path)
            if enf_ok:
                print(colorize_text("✓ " + enf_msg, "bright_green"))
            else:
                print(colorize_text("✗ " + enf_msg, "bright_red"))
        return 0

    return 0


from proxyshield.proxy_engine import (
    fetch_free_proxies,
    diagnose_proxies_concurrent,
    render_proxy_table,
    export_proxies_to_file,
    get_random_free_proxy,
)


def handle_proxy_cli(args: argparse.Namespace) -> int:
    """Handles `proxyshield proxy` subcommands."""
    action = getattr(args, "proxy_action", "list")
    source = getattr(args, "source", "all")

    if action == "random":
        p = get_random_free_proxy(
            source=source,
            protocol=args.protocol,
            country=args.country,
            anonymity=args.anonymity
        )
        if p:
            print(p.get("proxy", ""))
            return 0
        else:
            print("No matching free proxy found.", file=sys.stderr)
            return 1

    limit = args.limit or (10 if action == "check" else 20)
    source_label = "ProxyScrape + Geonode" if source == "all" else source.capitalize()
    print(colorize_text(f"\n[ProxyShield] Querying free proxy pool ({source_label})...", "bright_cyan"))

    try:
        proxies = fetch_free_proxies(
            source=source,
            protocol=args.protocol,
            country=args.country,
            anonymity=args.anonymity,
            ssl_only=args.ssl,
            max_timeout=args.max_timeout,
            limit=limit
        )
    except Exception as e:
        print(colorize_text(f"Error fetching proxies: {e}", "bright_red"))
        return 1

    if not proxies:
        print(colorize_text("No proxies matched your filter criteria.", "bright_yellow"))
        return 0

    if action == "check":
        print(colorize_text(f"Running concurrent connectivity diagnostics on {len(proxies)} proxies...", "bright_yellow"))
        diagnosed = diagnose_proxies_concurrent(proxies, max_workers=args.workers or 15, timeout=args.timeout or 4)
        render_proxy_table(diagnosed, title="ProxyShield Live Diagnostic Results", verified=True)

        if args.output:
            # Filter alive if saving
            to_save = [p for p in diagnosed if p.get("verified_alive", False)] if args.alive_only else diagnosed
            ok, msg = export_proxies_to_file(to_save, args.output, file_format=args.format or "txt")
            print(colorize_text(msg, "bright_green" if ok else "bright_red"))
        return 0
    else:
        render_proxy_table(proxies, title="ProxyShield Free Proxy Pool")
        if args.output:
            ok, msg = export_proxies_to_file(proxies, args.output, file_format=args.format or "txt")
            print(colorize_text(msg, "bright_green" if ok else "bright_red"))
        return 0


from proxyshield.security_shield import StrictProxyShield, LEGAL_PRIVACY_NOTICE, DirectIPExposureError
from proxyshield.auditor import NetworkAuditEngine
from proxyshield.reporter import export_multi_format_reports


def handle_audit_cli(args: argparse.Namespace) -> int:
    """Handles `proxyshield audit` command."""
    target_url = args.target
    print(colorize_text("\n=======================================================", "bright_yellow", bold=True))
    print(colorize_text("🛡️  PROXYSHIELD STRICT PROXY SECURITY AUDIT", "bright_cyan", bold=True))
    print(colorize_text("=======================================================", "bright_yellow", bold=True))
    print(colorize_text("\n[PRIVACY & LEGAL TRANSPARENCY NOTICE]", "bright_yellow", bold=True))
    print(colorize_text(LEGAL_PRIVACY_NOTICE, "white"))
    print()

    shield = StrictProxyShield()
    print(colorize_text(f"[Direct-IP Guard] Baseline Operator IP: {shield.operator_direct_ip}", "bright_cyan"))
    print(colorize_text("[Direct-IP Guard] Direct connection fallback: DISABLED (Enforced)", "bright_green", bold=True))
    print(colorize_text(f"[Target] Auditing authorized target: {target_url}", "bright_white", bold=True))

    # Fetch live candidate proxies
    print(colorize_text("\n[1/3] Gathering verified proxy pool...", "bright_cyan"))
    proxies = fetch_free_proxies(source="all", limit=args.limit or 10)
    if not proxies:
        print(colorize_text("Error: No proxies available for audit.", "bright_red"))
        return 1

    print(colorize_text(f"Fetched {len(proxies)} candidate proxies. Beginning sequential low-rate testing...", "bright_yellow"))
    auditor = NetworkAuditEngine(shield=shield)
    audit_data = auditor.audit_target(
        target_url=target_url,
        proxies=proxies,
        rate_limit_delay=args.delay,
        max_requests=args.limit or 10,
        timeout=args.timeout or 6
    )

    print(colorize_text("\n[2/3] Diagnostic Request Breakdown:", "bright_yellow", bold=True))
    for r in audit_data["results"]:
        status_str = f"HTTP {r['status_code']}" if r.get('status_code') else r.get('category')
        cat = r.get('category', 'UNKNOWN')
        col = 'bright_green' if cat == 'SUCCESS' else ('bright_yellow' if '403' in cat or '429' in cat else 'bright_red')
        print(f"  • {r['endpoint'].ljust(35)} Exit IP: {str(r.get('exit_ip')).ljust(16)} -> {colorize_text(status_str, col)} ({r.get('latency_ms', 0)} ms)")

    # Generate Reports (HTML, JSON, CSV)
    report_base = args.report or "audit_report"
    print(colorize_text(f"\n[3/3] Generating multi-format audit reports ({report_base}.*)...", "bright_cyan"))
    out_files = export_multi_format_reports(audit_data, report_base)
    for fmt, pth in out_files.items():
        print(colorize_text(f"  ✓ {fmt.upper()} Report: {os.path.abspath(pth)}", "bright_green"))

    print(colorize_text("\nAudit successfully concluded under strict proxy-only mode.\n", "bright_cyan", bold=True))
    return 0


def print_main_menu() -> None:
    """Displays the terminal startup branding screen and quick actions menu."""
    banner = render_branding_banner()
    print(banner)

    print("\n" + colorize_text("LEGAL & PRIVACY TRANSPARENCY NOTICE:", "bright_yellow", bold=True))
    print(colorize_text(LEGAL_PRIVACY_NOTICE, "gray"))

    print("\n" + colorize_text("Available Commands:", "bright_yellow", bold=True))
    commands = [
        ("proxyshield proxy", "Fetch and display live free proxies (Geonode + ProxyScrape)"),
        ("proxyshield proxy check", "Run concurrent latency & connectivity diagnostics"),
        ("proxyshield proxy random", "Get a single fast random proxy endpoint"),
        ("proxyshield audit --target <URL>", "Conduct authorized security audit strictly through proxies"),
        ("proxyshield banner", "Render branding banner with active configuration"),
        ("proxyshield banner --preview", "Display font style & color effect showcase"),
        ("proxyshield banner --list-fonts", "List all supported typography fonts"),
        ("proxyshield banner [options]", "Generate custom banner (--text, --font, --gradient, --align, --effect)"),
        ("proxyshield config show", "Display current branding configuration"),
        ("proxyshield config validate", "Check configuration syntax, keys, and security"),
        ("proxyshield config edit", "Open branding configuration in system editor"),
        ("proxyshield config reset", "Safely restore default configuration"),
        ("proxyshield config permissions", "Verify & enforce 0600 file security"),
    ]
    for cmd, desc in commands:
        print(f"  {colorize_text(cmd.ljust(35), 'bright_cyan')} {colorize_text(desc, 'white')}")
    print()


def build_parser() -> argparse.ArgumentParser:
    """Builds the main argument parser with full aliases and rich descriptions."""
    epilog_text = (
        "Short-form Aliases:\n"
        "  pxs                         Short alias for 'proxyshield'\n"
        "  pxs p, proxyshield proxy     Proxy pool & diagnostics (fetch, check, random)\n"
        "  pxs a, proxyshield audit     Strict security audit against authorized target\n"
        "  pxs b, proxyshield banner    Typography banner generator\n"
        "  pxs c, proxyshield config    Configuration & permissions management\n\n"
        "Examples:\n"
        "  pxs -h                      Display this help overview\n"
        "  pxs p check --limit 15      Quick proxy check\n"
        "  pxs a -t https://target     Strict proxy audit\n"
        "  pxs b --gradient red,blue   Render colorful banner\n"
    )

    parser = argparse.ArgumentParser(
        prog="proxyshield",
        description="ProxyShield (pxs) - Advanced CFonts Terminal Branding & Public Proxy Intelligence Platform\nAuthor: Quarkova (https://quarkova.com)",
        epilog=epilog_text,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-v", "--version", action="version", version=f"ProxyShield (pxs) v{__version__} by Quarkova")
    parser.add_argument("-i", "--interactive", action="store_true", help="Launch interactive shell prompt (Termux-SSH style REPL)")
    parser.add_argument("--menu", action="store_true", help="Display static branding banner and menu overview")

    subparsers = parser.add_subparsers(dest="command", help="Subcommand to execute (use -h with any subcommand)")

    # interactive subcommand (aliases: i, shell, repl)
    subparsers.add_parser(
        "interactive",
        aliases=["i", "shell", "repl"],
        help="Launch interactive shell prompt (Termux-SSH style REPL)"
    )

    # proxy subcommand (aliases: p, proxies)
    proxy_parser = subparsers.add_parser(
        "proxy",
        aliases=["p", "proxies"],
        help="Fetch, verify, and filter free proxies from ProxyScrape and Geonode"
    )
    proxy_sub = proxy_parser.add_subparsers(dest="proxy_action")

    # audit subcommand (aliases: a, scan)
    audit_parser = subparsers.add_parser(
        "audit",
        aliases=["a", "scan"],
        help="Authorized target security testing strictly via verified proxies"
    )
    audit_parser.add_argument("--target", "-t", type=str, required=True, help="Target URL (authorized targets only)")
    audit_parser.add_argument("--limit", "-n", type=int, default=10, help="Number of proxies to audit against target")
    audit_parser.add_argument("--delay", "-d", type=float, default=1.0, help="Rate limit delay between requests in seconds")
    audit_parser.add_argument("--timeout", type=int, default=6, help="Request timeout in seconds")
    audit_parser.add_argument("--report", "-r", type=str, default="audit_report", help="Base filename for generated reports (HTML, JSON, CSV)")

    # proxy fetch / list
    def add_filter_args(p):
        p.add_argument("--source", "-s", choices=["all", "geonode", "proxyscrape"], default="all", help="Proxy provider source")
        p.add_argument("--protocol", choices=["http", "socks4", "socks5", "all"], default="all", help="Proxy protocol")
        p.add_argument("--country", "-c", type=str, help="Country code filter (e.g. US, DE, IN, ES, CN)")
        p.add_argument("--anonymity", choices=["elite", "anonymous", "transparent", "all"], default="all", help="Anonymity level")
        p.add_argument("--ssl", action="store_true", help="SSL/HTTPS support only")
        p.add_argument("--max-timeout", type=int, help="Maximum API latency in milliseconds")
        p.add_argument("--limit", "-n", type=int, default=15, help="Number of proxies to fetch/display")
        p.add_argument("--output", "-o", type=str, help="Output file path (e.g. proxies.txt or proxies.json)")
        p.add_argument("--format", choices=["txt", "json"], default="txt", help="Output format")

    fetch_p = proxy_sub.add_parser("fetch", aliases=["f"], help="Fetch and filter free proxies")
    add_filter_args(fetch_p)

    list_p = proxy_sub.add_parser("list", aliases=["l", "ls"], help="List free proxies in formatted table")
    add_filter_args(list_p)

    check_p = proxy_sub.add_parser("check", aliases=["c", "test"], help="Test live proxy connectivity and measure roundtrip latency")
    add_filter_args(check_p)
    check_p.add_argument("--workers", "-w", type=int, default=15, help="Number of concurrent check threads")
    check_p.add_argument("--timeout", type=int, default=4, help="Connection timeout in seconds")
    check_p.add_argument("--alive-only", action="store_true", help="Only save verified working proxies to output")

    rand_p = proxy_sub.add_parser("random", aliases=["r", "rand"], help="Output a single working free proxy")
    rand_p.add_argument("--source", "-s", choices=["all", "geonode", "proxyscrape"], default="all")
    rand_p.add_argument("--protocol", choices=["http", "socks4", "socks5", "all"], default="all")
    rand_p.add_argument("--country", "-c", type=str)
    rand_p.add_argument("--anonymity", choices=["elite", "anonymous", "transparent", "all"], default="all")

    # Set default action on bare 'proxyshield proxy'
    add_filter_args(proxy_parser)

    # banner subcommand (aliases: b)
    banner_parser = subparsers.add_parser("banner", aliases=["b"], help="Custom typography banner generator")
    banner_parser.add_argument("--text", "-t", type=str, help="Text to display in banner")
    banner_parser.add_argument("--font", "-f", type=str, help="Font style (standard, block, 3d, huge, shadow, shade, console, slant, small, banner, digital)")
    banner_parser.add_argument("--color", type=str, help="Single color name, hex code (#ff5500), or 'rainbow'")
    banner_parser.add_argument("--gradient", "-g", type=str, help="Two comma-separated colors (e.g. 'red,blue' or '#ff5500,#00ffff')")
    banner_parser.add_argument("--align", "-a", type=str, choices=["left", "center", "right"], help="Text alignment")
    banner_parser.add_argument("--effect", "-e", type=str, choices=["shade", "shadow", "3d", "outline", "none"], help="Text visual effect")
    banner_parser.add_argument("--list-fonts", action="store_true", help="List all available fonts")
    banner_parser.add_argument("--preview", action="store_true", help="Showcase preview gallery of fonts and effects")

    # config subcommand (aliases: c, cfg)
    config_parser = subparsers.add_parser("config", aliases=["c", "cfg"], help="Manage branding configuration")
    config_sub = config_parser.add_subparsers(dest="action", required=True)

    config_sub.add_parser("show", aliases=["s"], help="Show active configuration")
    config_sub.add_parser("validate", aliases=["v", "val"], help="Validate configuration keys and security")
    config_sub.add_parser("edit", aliases=["e"], help="Edit configuration in $EDITOR")

    reset_p = config_sub.add_parser("reset", aliases=["r"], help="Reset configuration to defaults")
    reset_p.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")

    perm_p = config_sub.add_parser("permissions", aliases=["p", "perm"], help="Verify and secure configuration file permissions")
    perm_p.add_argument("--fix", action="store_true", help="Automatically enforce 0600 permissions")

    return parser


def normalize_aliases(args: argparse.Namespace) -> argparse.Namespace:
    """Normalizes short-form command and action aliases."""
    cmd_map = {
        "p": "proxy", "proxies": "proxy",
        "a": "audit", "scan": "audit",
        "b": "banner",
        "c": "config", "cfg": "config",
        "i": "interactive", "shell": "interactive", "repl": "interactive",
    }
    action_map = {
        "f": "fetch", "l": "list", "ls": "list",
        "c": "check", "test": "check", "r": "random", "rand": "random",
        "s": "show", "v": "validate", "val": "validate", "e": "edit",
        "p": "permissions", "perm": "permissions"
    }

    if hasattr(args, "command") and args.command in cmd_map:
        args.command = cmd_map[args.command]

    if hasattr(args, "proxy_action") and args.proxy_action in action_map:
        args.proxy_action = action_map[args.proxy_action]

    if hasattr(args, "action") and args.action in action_map:
        args.action = action_map[args.action]

    return args


def main(argv: List[str] = None) -> int:
    """Main CLI execution flow."""
    parser = build_parser()
    args = parser.parse_args(argv)
    args = normalize_aliases(args)

    if getattr(args, "interactive", False) or args.command == "interactive":
        from proxyshield.interactive import start_interactive_shell
        return start_interactive_shell()
    elif getattr(args, "menu", False):
        print_main_menu()
        return 0
    elif args.command == "audit":
        return handle_audit_cli(args)
    elif args.command == "proxy":
        return handle_proxy_cli(args)
    elif args.command == "banner":
        return handle_banner_cli(args)
    elif args.command == "config":
        return handle_config_cli(args)
    else:
        # If running in an interactive terminal, launch the interactive shell!
        if sys.stdin.isatty():
            from proxyshield.interactive import start_interactive_shell
            return start_interactive_shell()
        else:
            print_main_menu()
            return 0


if __name__ == "__main__":
    sys.exit(main())

