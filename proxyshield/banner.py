"""
ProxyShield Banner CLI & Render Engine
Handles standalone banner generation, font preview gallery, and banner CLI flags.

Author: Quarkova
Website: https://quarkova.com
"""

import sys
import argparse
from typing import Optional, List

from proxyshield.font_engine import (
    list_available_fonts,
    list_all_pyfiglet_fonts,
    render_ascii_text,
    apply_effect,
    align_lines,
    get_terminal_width,
)
from proxyshield.color_engine import (
    colorize_text,
    apply_horizontal_gradient,
    apply_rainbow,
    apply_neon,
    RESET,
    BOLD,
)
from proxyshield.branding import render_branding_banner


def render_standalone_banner(
    text: str = "ProxyShield",
    font: str = "3d",
    color: Optional[str] = None,
    gradient: Optional[str] = None,
    align: str = "center",
    effect: str = "shade",
    bold: bool = True
) -> str:
    """Renders an isolated typography banner with custom parameters."""
    term_width = get_terminal_width()

    # 1. Render ASCII
    raw_lines, used_font = render_ascii_text(text, font=font, max_width=term_width)

    # 2. Text Effect
    effected_lines = apply_effect(raw_lines, effect=effect)

    # 3. Coloring
    if gradient:
        parts = gradient.split(",")
        c_start = parts[0].strip() if len(parts) > 0 else "#ff5500"
        c_end = parts[1].strip() if len(parts) > 1 else "#00ffff"
        colored_lines = apply_horizontal_gradient(effected_lines, c_start, c_end, bold=bold)
    elif color:
        c_lower = color.strip().lower()
        if c_lower == "rainbow":
            colored_lines = apply_rainbow(effected_lines, bold=bold)
        elif c_lower == "neon":
            colored_lines = apply_neon(effected_lines, neon_color="cyan", bold=bold)
        else:
            colored_lines = [colorize_text(line, color, bold=bold) for line in effected_lines]
    else:
        # Default gradient
        colored_lines = apply_horizontal_gradient(effected_lines, "#ff5500", "#00ffff", bold=bold)

    # 4. Alignment
    aligned_lines = align_lines(colored_lines, alignment=align, terminal_width=term_width)
    return "\n".join(aligned_lines)


def display_font_preview(sample_text: str = "ProxyShield") -> None:
    """
    Renders an interactive visual gallery displaying available font styles,
    color modes, and typography effects.
    """
    print(colorize_text("\n=== ProxyShield Typography Engine Showcase ===\n", "bright_yellow", bold=True))

    styles = [
        ("Standard", "standard", "cyan", "none"),
        ("Block", "block", "yellow", "none"),
        ("3D (Larry3D)", "3d", "orange", "none"),
        ("Huge", "huge", "bright_red", "none"),
        ("Shadow (ANSI Shadow)", "shadow", "green", "shadow"),
        ("Shade (Halftone)", "shade", "#ff007f", "shade"),
        ("Console (Term)", "console", "bright_green", "none"),
        ("Slant", "slant", "bright_blue", "none"),
        ("Small", "small", "purple", "none"),
        ("Digital", "digital", "bright_white", "none"),
    ]

    for label, font_name, col, eff in styles:
        print(colorize_text(f"--- Style: {label} [font={font_name}, effect={eff}] ---", "gray"))
        rendered = render_standalone_banner(
            text=sample_text,
            font=font_name,
            color=col,
            align="center",
            effect=eff,
            bold=True
        )
        print(rendered)
        print()

    print(colorize_text("--- Color Effect: Rainbow Gradient ---", "gray"))
    rainbow_sample = render_standalone_banner(
        text=sample_text,
        font="shadow",
        color="rainbow",
        align="center",
        bold=True
    )
    print(rainbow_sample)
    print()

    print(colorize_text("--- Color Effect: Custom Dual Gradient (#ff5500 -> #00ffff) ---", "gray"))
    gradient_sample = render_standalone_banner(
        text=sample_text,
        font="3d",
        gradient="#ff5500,#00ffff",
        align="center",
        bold=True
    )
    print(gradient_sample)
    print()


def display_font_list() -> None:
    """Prints the list of friendly font styles and all supported pyfiglet fonts."""
    print(colorize_text("Supported ProxyShield Font Styles:", "bright_cyan", bold=True))
    for f in list_available_fonts():
        print(f"  • {f}")

    print("\n" + colorize_text("Available Backend Fonts (Total: " + str(len(list_all_pyfiglet_fonts())) + "):", "bright_yellow", bold=True))
    all_fonts = list_all_pyfiglet_fonts()
    col_width = 20
    cols = max(1, get_terminal_width() // col_width)
    for i in range(0, len(all_fonts), cols):
        chunk = all_fonts[i:i + cols]
        print("  " + "".join(f.ljust(col_width) for f in chunk))


def handle_banner_cli(args: argparse.Namespace) -> int:
    """CLI handler for `proxyshield banner` subcommands."""
    if args.list_fonts:
        display_font_list()
        return 0

    if args.preview:
        sample = args.text or "ProxyShield"
        display_font_preview(sample)
        return 0

    # If any specific banner override is passed, render standalone
    if any([args.text, args.font, args.color, args.gradient, args.align, args.effect]):
        rendered = render_standalone_banner(
            text=args.text or "ProxyShield",
            font=args.font or "3d",
            color=args.color,
            gradient=args.gradient,
            align=args.align or "center",
            effect=args.effect or "none",
        )
        print(rendered)
        return 0

    # Otherwise render full default branding banner from configuration
    full_banner = render_branding_banner()
    print(full_banner)
    return 0


def add_banner_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Registers the 'banner' command arguments."""
    parser = subparsers.add_parser("banner", help="Custom typography banner generator")
    parser.add_argument("--text", type=str, help="Text to display in banner")
    parser.add_argument("--font", type=str, help="Font style (standard, block, 3d, huge, shadow, shade, console, slant, small, banner, digital)")
    parser.add_argument("--color", type=str, help="Single color name, hex code (#ff5500), or 'rainbow'")
    parser.add_argument("--gradient", type=str, help="Two comma-separated colors (e.g. 'red,blue' or '#ff5500,#00ffff')")
    parser.add_argument("--align", type=str, choices=["left", "center", "right"], help="Text alignment")
    parser.add_argument("--effect", type=str, choices=["shade", "shadow", "3d", "outline", "none"], help="Text visual effect")
    parser.add_argument("--list-fonts", action="store_true", help="List all available fonts")
    parser.add_argument("--preview", action="store_true", help="Showcase preview gallery of fonts and effects")
    return parser


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ProxyShield Banner Tool")
    parser.add_argument("--text", type=str)
    parser.add_argument("--font", type=str)
    parser.add_argument("--color", type=str)
    parser.add_argument("--gradient", type=str)
    parser.add_argument("--align", type=str)
    parser.add_argument("--effect", type=str)
    parser.add_argument("--list-fonts", action="store_true")
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    handle_banner_cli(args)

