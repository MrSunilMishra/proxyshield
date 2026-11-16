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


def print_main_menu() -> None:
    """Displays the terminal startup branding screen and quick actions menu."""
    banner = render_branding_banner()
    print(banner)

    print("\n" + colorize_text("Available Commands:", "bright_yellow", bold=True))
    commands = [
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
    """Builds the main argument parser."""
    parser = argparse.ArgumentParser(
        prog="proxyshield",
        description="ProxyShield - Advanced CFonts-Style Terminal Branding Engine"
    )
    parser.add_argument("-v", "--version", action="version", version=f"ProxyShield {__version__} by Quarkova")

    subparsers = parser.add_subparsers(dest="command", help="Subcommand to execute")

    # banner subcommand
    add_banner_parser(subparsers)

    # config subcommand
    config_parser = subparsers.add_parser("config", help="Manage branding configuration")
    config_sub = config_parser.add_subparsers(dest="action", required=True)

    config_sub.add_parser("show", help="Show active configuration")
    config_sub.add_parser("validate", help="Validate configuration keys and security")
    config_sub.add_parser("edit", help="Edit configuration in $EDITOR")

    reset_p = config_sub.add_parser("reset", help="Reset configuration to defaults")
    reset_p.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")

    perm_p = config_sub.add_parser("permissions", help="Verify and secure configuration file permissions")
    perm_p.add_argument("--fix", action="store_true", help="Automatically enforce 0600 permissions")

    return parser


def main(argv: List[str] = None) -> int:
    """Main CLI execution flow."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "banner":
        return handle_banner_cli(args)
    elif args.command == "config":
        return handle_config_cli(args)
    else:
        print_main_menu()
        return 0


if __name__ == "__main__":
    sys.exit(main())

