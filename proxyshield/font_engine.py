"""
ProxyShield Font Engine
Provides CFonts-inspired ASCII typography rendering, font style mappings,
effect processing (shade, shadow, 3d, outline), auto-resizing, and terminal alignment.

Author: Quarkova
Website: https://quarkova.com
"""

import shutil
from typing import List, Optional, Tuple
import pyfiglet
from proxyshield.color_engine import strip_ansi

# Map of standard friendly font style names to pyfiglet fonts
FONT_STYLE_MAP = {
    "standard": "standard",
    "block": "block",
    "3d": "larry3d",
    "huge": "big",
    "shadow": "ansi_shadow",
    "shade": "ansi_shadow",
    "console": "term",
    "slant": "slant",
    "small": "small",
    "banner": "banner3",
    "digital": "digital",
}

# Fallback sequence when width overflows
FONT_FALLBACK_SEQUENCE = ["huge", "3d", "standard", "slant", "small", "digital"]


def get_terminal_width(default: int = 80) -> int:
    """Returns the current terminal width or default."""
    try:
        return shutil.get_terminal_size(fallback=(default, 24)).columns
    except Exception:
        return default


def list_available_fonts() -> List[str]:
    """Returns a list of supported friendly font names and popular fonts."""
    return list(FONT_STYLE_MAP.keys())


def list_all_pyfiglet_fonts() -> List[str]:
    """Returns all installed pyfiglet fonts."""
    return sorted(pyfiglet.FigletFont.getFonts())


def resolve_font_name(font: str) -> str:
    """Resolves a friendly font style name or returns the pyfiglet font directly."""
    clean = font.strip().lower()
    if clean in FONT_STYLE_MAP:
        return FONT_STYLE_MAP[clean]
    
    # Check if directly in pyfiglet
    all_fonts = set(list_all_pyfiglet_fonts())
    if clean in all_fonts:
        return clean
    if font in all_fonts:
        return font
    
    return "standard"


def render_ascii_text(
    text: str,
    font: str = "standard",
    max_width: Optional[int] = None,
    auto_resize: bool = True
) -> Tuple[List[str], str]:
    """
    Renders text to ASCII art lines with automatic width detection and fallback.
    Returns (rendered_lines, font_used).
    """
    if max_width is None:
        max_width = get_terminal_width()

    chosen_style = font.strip().lower()
    pyfiglet_font = resolve_font_name(chosen_style)

    # First attempt with requested font
    try:
        fig = pyfiglet.Figlet(font=pyfiglet_font, width=max(max_width, 1000))
        art = fig.renderText(text)
        lines = [line.rstrip() for line in art.splitlines() if line.strip() != ""]
    except Exception:
        fig = pyfiglet.Figlet(font="standard")
        art = fig.renderText(text)
        lines = [line.rstrip() for line in art.splitlines() if line.strip() != ""]
        pyfiglet_font = "standard"

    rendered_width = max((len(strip_ansi(line)) for line in lines), default=0)

    # If it overflows max_width and auto_resize is True, step through fallbacks
    if auto_resize and rendered_width > max_width and max_width > 20:
        for fb_style in FONT_FALLBACK_SEQUENCE:
            fb_font = resolve_font_name(fb_style)
            if fb_font == pyfiglet_font:
                continue
            try:
                test_fig = pyfiglet.Figlet(font=fb_font, width=max(max_width, 1000))
                test_art = test_fig.renderText(text)
                test_lines = [l.rstrip() for l in test_art.splitlines() if l.strip() != ""]
                test_width = max((len(strip_ansi(l)) for l in test_lines), default=0)
                if test_width <= max_width:
                    return test_lines, fb_style
            except Exception:
                continue

    return lines, chosen_style


def apply_effect(lines: List[str], effect: str = "none") -> List[str]:
    """
    Applies typographical effects:
      - 'shade': progressive halftone unicode block shading (▓, ▒, ░)
      - 'shadow': adds extruded drop shadow blocks
      - '3d': adds pseudo-3D diagonal extrusion
      - 'outline': creates outline / wireframe borders
      - 'none': clean unaltered text
    """
    eff = effect.strip().lower()
    if eff == "none" or not lines:
        return lines

    if eff == "shade":
        # Halftone gradient shading based on vertical position
        num_lines = len(lines)
        shaded_lines = []
        for i, line in enumerate(lines):
            ratio = i / max(num_lines - 1, 1)
            if ratio < 0.35:
                char_replace = "█"
            elif ratio < 0.70:
                char_replace = "▓"
            else:
                char_replace = "▒"

            # Replace solid block characters or dense ASCII with shade
            new_line = []
            for char in line:
                if char in ("█", "#", "@", "%"):
                    new_line.append(char_replace)
                elif char in ("|", "/", "\\", "_"):
                    new_line.append(char)
                elif char != " ":
                    new_line.append(char_replace)
                else:
                    new_line.append(" ")
            shaded_lines.append("".join(new_line))
        return shaded_lines

    elif eff == "shadow":
        # Add drop shadow with '░' to right and bottom
        shadowed = []
        for line in lines:
            # Add shadow to non-blank characters on the right
            chars = list(line)
            res = []
            for j, c in enumerate(chars):
                res.append(c)
                if c != " " and (j + 1 >= len(chars) or chars[j + 1] == " "):
                    res.append("░")
            shadowed.append("".join(res))
        # Add a subtle bottom shadow row
        if shadowed:
            last = shadowed[-1]
            bottom_shadow = "".join(["░" if c != " " else " " for c in last])
            shadowed.append(bottom_shadow)
        return shadowed

    elif eff == "3d":
        # Extrusion effect with diagonal ╲ or /
        extruded = []
        for line in lines:
            chars = list(line)
            res = []
            for j, c in enumerate(chars):
                res.append(c)
                if c != " " and (j + 1 >= len(chars) or chars[j + 1] == " "):
                    res.append("▌")
            extruded.append("".join(res))
        return extruded

    elif eff == "outline":
        # Wireframe / outline effect
        outlined = []
        for line in lines:
            res = []
            for c in line:
                if c == "█":
                    res.append("□")
                elif c != " ":
                    res.append("◦")
                else:
                    res.append(" ")
            outlined.append("".join(res))
        return outlined

    return lines


def align_lines(
    lines: List[str],
    alignment: str = "center",
    terminal_width: Optional[int] = None
) -> List[str]:
    """
    Aligns text lines (Left, Center, Right) relative to the terminal width.
    """
    if not lines:
        return []

    if terminal_width is None:
        terminal_width = get_terminal_width()

    align = alignment.strip().lower()
    max_line_len = max((len(strip_ansi(line)) for line in lines), default=0)

    if align == "left":
        return lines

    aligned = []
    for line in lines:
        clean_len = len(strip_ansi(line))
        if align == "center":
            pad = max(0, (terminal_width - max_line_len) // 2)
            aligned.append(" " * pad + line)
        elif align == "right":
            pad = max(0, terminal_width - max_line_len)
            aligned.append(" " * pad + line)
        else:
            aligned.append(line)

    return aligned

