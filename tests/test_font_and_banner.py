"""
Unit tests for ProxyShield Font Engine & Banner Renderer
"""

import os
from proxyshield.font_engine import (
    FONT_STYLE_MAP,
    resolve_font_name,
    render_ascii_text,
    apply_effect,
    align_lines,
    list_available_fonts,
)
from proxyshield.banner import render_standalone_banner
from proxyshield.branding import render_branding_banner, get_branding_value


def test_font_style_resolutions():
    required_styles = [
        "standard",
        "block",
        "3d",
        "huge",
        "shadow",
        "shade",
        "console",
        "slant",
        "small",
        "banner",
        "digital",
    ]
    for style in required_styles:
        assert style in FONT_STYLE_MAP
        resolved = resolve_font_name(style)
        assert isinstance(resolved, str) and len(resolved) > 0


def test_render_ascii_text():
    lines, used_font = render_ascii_text("TEST", font="small")
    assert len(lines) > 0
    assert any("TEST" in line or any(c in line for c in ["_", "|", "/", "\\"]) for line in lines)


def test_text_effects():
    sample = ["██████", "██████"]
    shade = apply_effect(sample, effect="shade")
    assert len(shade) == 2
    # Verify shade replacement characters exist
    assert any("▓" in l or "▒" in l or "█" in l for l in shade)

    shadow = apply_effect(sample, effect="shadow")
    assert any("░" in l for l in shadow)

    outline = apply_effect(sample, effect="outline")
    assert any("□" in l or "◦" in l for l in outline)


def test_alignment():
    lines = ["ABC"]
    term_width = 80

    left = align_lines(lines, alignment="left", terminal_width=term_width)
    assert left[0] == "ABC"

    center = align_lines(lines, alignment="center", terminal_width=term_width)
    assert center[0].startswith(" ") and center[0].endswith("ABC")

    right = align_lines(lines, alignment="right", terminal_width=term_width)
    assert right[0].startswith(" ") and right[0].endswith("ABC")
    assert len(right[0]) == term_width


def test_standalone_banner_renderer():
    banner = render_standalone_banner(
        text="ProxyShield",
        font="slant",
        gradient="#ff0000,#00ffff",
        align="center",
        effect="none"
    )
    assert len(banner) > 0
    assert "ProxyShield" in banner or "\\" in banner or "/" in banner


def test_branding_banner_contains_quarkova():
    full_output = render_branding_banner()
    assert "Quarkova" in full_output
    assert "https://quarkova.com" in full_output
    assert "MIT License" in full_output


def test_safe_ini_get_value():
    author = get_branding_value("IDENTITY.author")
    assert author == "Quarkova"
    tool = get_branding_value("IDENTITY.tool_name")
    assert tool == "ProxyShield"

