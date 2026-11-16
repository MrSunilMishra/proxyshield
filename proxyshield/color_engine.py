"""
ProxyShield Color Engine
Provides TrueColor (24-bit RGB/HEX), 256-color fallback, gradients,
rainbow, neon, and ANSI formatting for terminal typography.

Author: Quarkova
Website: https://quarkova.com
"""

import os
import re
import math
import sys
from typing import List, Tuple, Union, Optional
import colorama

# Initialize colorama for Windows ANSI support
colorama.init(autoreset=False)

# ANSI escape sequence regex for clean length calculations
ANSI_ESCAPE_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

# Standard & Bright 16 Named Colors
NAMED_COLORS = {
    "black": (0, 0, 0),
    "red": (220, 20, 60),
    "green": (50, 205, 50),
    "yellow": (255, 215, 0),
    "blue": (30, 144, 255),
    "magenta": (218, 112, 214),
    "purple": (138, 43, 226),
    "cyan": (0, 220, 255),
    "white": (255, 255, 255),
    "gray": (128, 128, 128),
    "grey": (128, 128, 128),
    "orange": (255, 128, 0),
    "pink": (255, 105, 180),
    "bright_red": (255, 80, 80),
    "bright_green": (100, 255, 100),
    "bright_yellow": (255, 255, 100),
    "bright_blue": (100, 180, 255),
    "bright_magenta": (255, 120, 255),
    "bright_cyan": (100, 255, 255),
    "bright_white": (255, 255, 255),
}

# Standard ANSI 16 color codes for graceful fallback
BASIC_ANSI_CODES = {
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "bright_red": "\033[91m",
    "bright_green": "\033[92m",
    "bright_yellow": "\033[93m",
    "bright_blue": "\033[94m",
    "bright_magenta": "\033[95m",
    "bright_cyan": "\033[96m",
    "bright_white": "\033[97m",
}

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"


def strip_ansi(text: str) -> str:
    """Removes all ANSI escape sequences from the string."""
    return ANSI_ESCAPE_RE.sub('', text)


def is_color_supported() -> bool:
    """Checks if the current terminal supports ANSI colors."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        # Allow override via FORCE_COLOR
        if os.environ.get("FORCE_COLOR"):
            return True
        return False
    return True


def is_truecolor_supported() -> bool:
    """Detects TrueColor (24-bit RGB) support in the terminal."""
    if not is_color_supported():
        return False
    colorterm = os.environ.get("COLORTERM", "").lower()
    if colorterm in ("truecolor", "24bit"):
        return True
    term = os.environ.get("TERM", "").lower()
    if "xterm-256color" in term or "alacritty" in term or "kitty" in term or "konsole" in term or "windows" in os.name:
        return True
    return True  # Modern terminals generally support 24-bit ANSI


def parse_color(color_val: Union[str, Tuple[int, int, int]]) -> Tuple[int, int, int]:
    """
    Parses a color representation into an (R, G, B) tuple.
    Accepts:
      - Hex: '#ff5500', 'ff5500', '#f50'
      - RGB string: 'rgb(255, 85, 0)', '255,85,0'
      - Named colors: 'cyan', 'yellow', 'bright_red', etc.
      - Tuple: (255, 85, 0)
    """
    if isinstance(color_val, (tuple, list)):
        r, g, b = int(color_val[0]), int(color_val[1]), int(color_val[2])
        return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

    if not isinstance(color_val, str):
        return (255, 255, 255)

    clean = color_val.strip().lower()

    if clean in NAMED_COLORS:
        return NAMED_COLORS[clean]

    # Hex match: #ffffff or #fff
    hex_match = re.match(r'^#?([0-9a-f]{3}|[0-9a-f]{6})$', clean)
    if hex_match:
        h = hex_match.group(1)
        if len(h) == 3:
            h = ''.join([c * 2 for c in h])
        r = int(h[0:2], 16)
        g = int(h[2:4], 16)
        b = int(h[4:6], 16)
        return (r, g, b)

    # RGB string match: rgb(r, g, b) or r,g,b
    rgb_match = re.match(r'^(?:rgb\s*\()?\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)?$', clean)
    if rgb_match:
        r = max(0, min(255, int(rgb_match.group(1))))
        g = max(0, min(255, int(rgb_match.group(2))))
        b = max(0, min(255, int(rgb_match.group(3))))
        return (r, g, b)

    # Fallback default
    return (255, 255, 255)


def ansi_fg_rgb(r: int, g: int, b: int) -> str:
    """Generates 24-bit TrueColor foreground ANSI escape sequence."""
    return f"\033[38;2;{r};{g};{b}m"


def ansi_bg_rgb(r: int, g: int, b: int) -> str:
    """Generates 24-bit TrueColor background ANSI escape sequence."""
    return f"\033[48;2;{r};{g};{b}m"


def interpolate_rgb(c1: Tuple[int, int, int], c2: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    """Linearly interpolates between two RGB colors (t between 0.0 and 1.0)."""
    t = max(0.0, min(1.0, t))
    r = int(c1[0] + (c2[0] - c1[0]) * t)
    g = int(c1[1] + (c2[1] - c1[1]) * t)
    b = int(c1[2] + (c2[2] - c1[2]) * t)
    return (r, g, b)


def multi_stop_gradient(colors: List[Tuple[int, int, int]], steps: int) -> List[Tuple[int, int, int]]:
    """Generates a gradient through multiple color stops."""
    if steps <= 0:
        return []
    if len(colors) == 0:
        return [(255, 255, 255)] * steps
    if len(colors) == 1:
        return [colors[0]] * steps
    if steps == 1:
        return [colors[0]]

    result = []
    num_segments = len(colors) - 1
    steps_per_segment = (steps - 1) / num_segments

    for i in range(steps):
        segment = min(int(i / steps_per_segment), num_segments - 1)
        seg_t = (i - segment * steps_per_segment) / steps_per_segment
        result.append(interpolate_rgb(colors[segment], colors[segment + 1], seg_t))

    return result


def generate_rainbow_colors(steps: int) -> List[Tuple[int, int, int]]:
    """Generates a spectrum of vibrant rainbow colors."""
    rainbow_stops = [
        (255, 0, 0),      # Red
        (255, 127, 0),    # Orange
        (255, 255, 0),    # Yellow
        (0, 255, 0),      # Green
        (0, 255, 255),    # Cyan
        (0, 100, 255),    # Blue
        (139, 0, 255),    # Violet
    ]
    return multi_stop_gradient(rainbow_stops, steps)


def colorize_text(
    text: str,
    color: Union[str, Tuple[int, int, int]],
    bold: bool = False,
    background: Optional[Union[str, Tuple[int, int, int]]] = None
) -> str:
    """Colorizes a single text string using TrueColor ANSI."""
    if not is_color_supported():
        return text

    r, g, b = parse_color(color)
    codes = []
    if bold:
        codes.append(BOLD)
    codes.append(ansi_fg_rgb(r, g, b))

    if background and background != "none":
        br, bg_c, bb = parse_color(background)
        codes.append(ansi_bg_rgb(br, bg_c, bb))

    prefix = "".join(codes)
    return f"{prefix}{text}{RESET}"


def apply_horizontal_gradient(
    lines: List[str],
    color_start: Union[str, Tuple[int, int, int]],
    color_end: Union[str, Tuple[int, int, int]],
    bold: bool = False
) -> List[str]:
    """
    Applies a smooth horizontal gradient across each line from left to right.
    """
    if not is_color_supported():
        return lines

    c1 = parse_color(color_start)
    c2 = parse_color(color_end)

    max_width = max((len(strip_ansi(line)) for line in lines), default=1)
    if max_width <= 1:
        max_width = 1

    palette = multi_stop_gradient([c1, c2], max_width)

    output = []
    for line in lines:
        colored_chars = []
        col_idx = 0
        for char in line:
            if char == ' ':
                colored_chars.append(' ')
                col_idx += 1
            else:
                idx = min(col_idx, len(palette) - 1)
                r, g, b = palette[idx]
                prefix = BOLD if bold else ""
                colored_chars.append(f"{prefix}{ansi_fg_rgb(r, g, b)}{char}{RESET}")
                col_idx += 1
        output.append("".join(colored_chars))

    return output


def apply_vertical_gradient(
    lines: List[str],
    color_start: Union[str, Tuple[int, int, int]],
    color_end: Union[str, Tuple[int, int, int]],
    bold: bool = False
) -> List[str]:
    """
    Applies a smooth vertical gradient from top line to bottom line.
    """
    if not is_color_supported():
        return lines

    c1 = parse_color(color_start)
    c2 = parse_color(color_end)

    num_lines = len(lines)
    palette = multi_stop_gradient([c1, c2], max(num_lines, 1))

    output = []
    for i, line in enumerate(lines):
        r, g, b = palette[i]
        prefix = BOLD if bold else ""
        colored_line = f"{prefix}{ansi_fg_rgb(r, g, b)}{line}{RESET}"
        output.append(colored_line)

    return output


def apply_rainbow(lines: List[str], bold: bool = False, horizontal: bool = True) -> List[str]:
    """
    Applies a spectrum rainbow effect either horizontally or vertically.
    """
    if not is_color_supported():
        return lines

    if horizontal:
        max_width = max((len(strip_ansi(line)) for line in lines), default=1)
        palette = generate_rainbow_colors(max(max_width, 1))

        output = []
        for line in lines:
            colored_chars = []
            col_idx = 0
            for char in line:
                if char == ' ':
                    colored_chars.append(' ')
                    col_idx += 1
                else:
                    idx = min(col_idx, len(palette) - 1)
                    r, g, b = palette[idx]
                    prefix = BOLD if bold else ""
                    colored_chars.append(f"{prefix}{ansi_fg_rgb(r, g, b)}{char}{RESET}")
                    col_idx += 1
            output.append("".join(colored_chars))
        return output
    else:
        palette = generate_rainbow_colors(max(len(lines), 1))
        output = []
        for i, line in enumerate(lines):
            r, g, b = palette[i]
            prefix = BOLD if bold else ""
            output.append(f"{prefix}{ansi_fg_rgb(r, g, b)}{line}{RESET}")
        return output


def apply_neon(
    lines: List[str],
    neon_color: Union[str, Tuple[int, int, int]] = "cyan",
    bold: bool = True
) -> List[str]:
    """
    Applies a neon glowing effect with high-intensity vibrant foreground
    and soft highlights.
    """
    if not is_color_supported():
        return lines

    base = parse_color(neon_color)
    # Brighten for glow
    bright = (
        min(255, int(base[0] * 1.3) + 30),
        min(255, int(base[1] * 1.3) + 30),
        min(255, int(base[2] * 1.3) + 30),
    )

    palette = [bright, base]
    output = []
    for i, line in enumerate(lines):
        # Alternate glow intensity
        color = palette[i % len(palette)]
        prefix = BOLD if bold else ""
        output.append(f"{prefix}{ansi_fg_rgb(*color)}{line}{RESET}")
    return output

