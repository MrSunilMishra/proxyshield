"""
ProxyShield Branding Engine
Coordinates branding metadata, header rendering, system information badges,
and safe configuration queries for CLI and Bash script integration.

Author: Quarkova
Website: https://quarkova.com
"""

import os
import sys
import platform
import argparse
from typing import Optional, Dict, Any, List

from proxyshield import __version__, __author__, __organization__, __website__, __license__
from proxyshield.config_manager import (
    load_config,
    get_identity,
    get_banner_config,
    get_colors_config,
    get_display_config,
    get_theme_config,
    get_config_path,
)
from proxyshield.font_engine import render_ascii_text, apply_effect, align_lines, get_terminal_width
from proxyshield.color_engine import (
    colorize_text,
    apply_horizontal_gradient,
    apply_vertical_gradient,
    apply_rainbow,
    apply_neon,
    strip_ansi,
    RESET,
    BOLD,
    DIM,
)


def get_system_info() -> Dict[str, str]:
    """Gathers system information for display badge."""
    return {
        "os": f"{platform.system()} {platform.release()}",
        "architecture": platform.machine(),
        "python": platform.python_version(),
    }


def render_branding_banner(
    config_path: Optional[str] = None,
    text_override: Optional[str] = None,
    font_override: Optional[str] = None,
    color_override: Optional[str] = None,
    gradient_override: Optional[str] = None,
    align_override: Optional[str] = None,
    effect_override: Optional[str] = None,
    show_details: bool = True
) -> str:
    """
    Renders the complete ProxyShield branding display including ASCII banner
    and metadata badges.
    """
    config = load_config(config_path)
    identity = get_identity(config)
    banner_cfg = get_banner_config(config)
    colors_cfg = get_colors_config(config)
    display_cfg = get_display_config(config)
    theme_cfg = get_theme_config(config)

    # Apply overrides if provided
    text = text_override or banner_cfg.get("text", "ProxyShield")
    font = font_override or banner_cfg.get("font", "3d")
    align = align_override or banner_cfg.get("alignment", "center")
    effect = effect_override or banner_cfg.get("effect", "shade")

    term_width = get_terminal_width()

    output_lines: List[str] = []

    if banner_cfg.get("enabled", True):
        # 1. Render ASCII text
        raw_lines, used_font = render_ascii_text(text, font=font, max_width=term_width)

        # 2. Apply Text Effect (shade, shadow, 3d, outline)
        effected_lines = apply_effect(raw_lines, effect=effect)

        # 3. Apply Color Mode
        if gradient_override:
            # e.g. "red,blue" or "#ff5500,#00ffff"
            parts = gradient_override.split(",")
            c_start = parts[0].strip() if len(parts) > 0 else "#ff5500"
            c_end = parts[1].strip() if len(parts) > 1 else "#00ffff"
            colored_lines = apply_horizontal_gradient(effected_lines, c_start, c_end, bold=colors_cfg.get("bold", True))
        elif color_override:
            colored_lines = [
                colorize_text(line, color_override, bold=colors_cfg.get("bold", True))
                for line in effected_lines
            ]
        elif colors_cfg.get("rainbow", False) or colors_cfg.get("mode") == "rainbow":
            colored_lines = apply_rainbow(effected_lines, bold=colors_cfg.get("bold", True))
        elif colors_cfg.get("mode") == "neon":
            neon_col = colors_cfg.get("color_start", "cyan")
            colored_lines = apply_neon(effected_lines, neon_color=neon_col, bold=colors_cfg.get("bold", True))
        elif colors_cfg.get("gradient", True) or colors_cfg.get("mode") == "gradient":
            c_start = colors_cfg.get("color_start", "#ff5500")
            c_end = colors_cfg.get("color_end", "#00ffff")
            colored_lines = apply_horizontal_gradient(effected_lines, c_start, c_end, bold=colors_cfg.get("bold", True))
        else:
            c = colors_cfg.get("color_start", "cyan")
            colored_lines = [
                colorize_text(line, c, bold=colors_cfg.get("bold", True))
                for line in effected_lines
            ]

        # 4. Apply Alignment
        aligned_banner = align_lines(colored_lines, alignment=align, terminal_width=term_width)
        output_lines.extend(aligned_banner)

    # 5. Metadata Badges (Author, Version, Tagline, System Info, etc.)
    if show_details:
        primary_col = theme_cfg.get("primary", "cyan")
        sec_col = theme_cfg.get("secondary", "yellow")
        badge_parts = []

        if display_cfg.get("show_version", True):
            badge_parts.append(f"{colorize_text('v' + identity['version'], primary_col, bold=True)}")

        if display_cfg.get("show_author", True):
            # Author must strictly show Quarkova
            badge_parts.append(f"{colorize_text('Author: Quarkova', sec_col, bold=True)}")

        if display_cfg.get("show_license", True):
            badge_parts.append(f"{colorize_text('MIT License', 'gray')}")

        if badge_parts:
            badge_str = " | ".join(badge_parts)
            aligned_badge = align_lines([badge_str], alignment=align, terminal_width=term_width)
            output_lines.append("")
            output_lines.extend(aligned_badge)

        if display_cfg.get("show_tagline", True) and identity.get("tagline"):
            tag_str = colorize_text(f"« {identity['tagline']} »", "bright_white", bold=False)
            output_lines.extend(align_lines([tag_str], alignment=align, terminal_width=term_width))

        if display_cfg.get("show_website", True) and identity.get("website"):
            web_str = colorize_text(identity["website"], primary_col)
            output_lines.extend(align_lines([web_str], alignment=align, terminal_width=term_width))

        if display_cfg.get("show_system_info", True):
            sys_info = get_system_info()
            sys_str = colorize_text(
                f"[ Platform: {sys_info['os']} | Arch: {sys_info['architecture']} | Python: {sys_info['python']} ]",
                "gray"
            )
            output_lines.append("")
            output_lines.extend(align_lines([sys_str], alignment=align, terminal_width=term_width))

    return "\n".join(output_lines)


def get_branding_value(section_and_key: str, config_path: Optional[str] = None) -> str:
    """
    Safely retrieves a configuration key formatted as 'SECTION.KEY' (e.g. 'IDENTITY.author').
    Safe for consumption by external tools and Bash scripts.
    """
    config = load_config(config_path)
    if "." not in section_and_key:
        return ""
    section, key = section_and_key.split(".", 1)
    section = section.strip().upper()
    key = key.strip().lower()

    if section == "IDENTITY" and key == "author":
        return "Quarkova"

    if section in config and key in config[section]:
        return config[section][key]

    return ""


def main():
    """CLI helper when called directly (e.g. by Bash scripts or python -m proxyshield.branding)."""
    parser = argparse.ArgumentParser(description="ProxyShield Branding Reader")
    parser.add_argument("--get", help="Get a specific config key e.g. IDENTITY.tool_name or IDENTITY.author")
    parser.add_argument("--render", action="store_true", help="Render full branding banner")
    parser.add_argument("--config", help="Custom configuration path")
    args = parser.parse_args()

    if args.get:
        val = get_branding_value(args.get, args.config)
        print(val)
    elif args.render:
        print(render_branding_banner(args.config))
    else:
        print(render_branding_banner(args.config))


if __name__ == "__main__":
    main()

