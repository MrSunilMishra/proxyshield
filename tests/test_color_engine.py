"""
Unit tests for ProxyShield Color Engine
"""

from proxyshield.color_engine import (
    parse_color,
    interpolate_rgb,
    multi_stop_gradient,
    generate_rainbow_colors,
    strip_ansi,
    colorize_text,
    apply_horizontal_gradient,
    apply_vertical_gradient,
    apply_rainbow,
    apply_neon,
)


def test_parse_color_hex():
    assert parse_color("#ff0000") == (255, 0, 0)
    assert parse_color("00ff00") == (0, 255, 0)
    assert parse_color("#00f") == (0, 0, 255)


def test_parse_color_rgb():
    assert parse_color("rgb(10, 20, 30)") == (10, 20, 30)
    assert parse_color("100,150,200") == (100, 150, 200)


def test_parse_named_colors():
    assert parse_color("red") == (220, 20, 60)
    assert parse_color("cyan") == (0, 220, 255)
    assert parse_color("yellow") == (255, 215, 0)


def test_interpolate_rgb():
    c1 = (0, 0, 0)
    c2 = (100, 200, 50)
    assert interpolate_rgb(c1, c2, 0.0) == (0, 0, 0)
    assert interpolate_rgb(c1, c2, 1.0) == (100, 200, 50)
    assert interpolate_rgb(c1, c2, 0.5) == (50, 100, 25)


def test_multi_stop_gradient():
    colors = [(0, 0, 0), (255, 255, 255)]
    grad = multi_stop_gradient(colors, 5)
    assert len(grad) == 5
    assert grad[0] == (0, 0, 0)
    assert grad[-1] == (255, 255, 255)


def test_rainbow_generator():
    rainbow = generate_rainbow_colors(10)
    assert len(rainbow) == 10
    # First stop should be red
    assert rainbow[0] == (255, 0, 0)


def test_strip_ansi():
    colored = colorize_text("Hello World", "cyan", bold=True)
    plain = strip_ansi(colored)
    assert plain == "Hello World"


def test_gradient_rendering():
    lines = ["=====", "====="]
    res_h = apply_horizontal_gradient(lines, "#ff0000", "#0000ff")
    assert len(res_h) == 2
    # Verify uncolored text matches original length
    for line in res_h:
        assert strip_ansi(line) == "====="

    res_v = apply_vertical_gradient(lines, "red", "blue")
    assert len(res_v) == 2
    for line in res_v:
        assert strip_ansi(line) == "====="


def test_neon_effect():
    lines = ["PROXY", "SHIELD"]
    neon = apply_neon(lines, neon_color="cyan")
    assert len(neon) == 2
    assert strip_ansi(neon[0]) == "PROXY"

