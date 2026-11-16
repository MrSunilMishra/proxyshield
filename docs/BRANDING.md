# ProxyShield Branding & Typography Engine

Welcome to the **ProxyShield** Terminal Branding Engine documentation. Inspired by CFonts, ProxyShield provides dynamic typography, rich gradients, Unicode shade/shadow effects, and owner-protected configuration management.

---

## 1. Project Identity

* **Tool Name:** ProxyShield
* **Author:** Quarkova
* **Organization:** Quarkova
* **Website:** [https://quarkova.com](https://quarkova.com)
* **License:** MIT
* **Category:** Network Security & Diagnostics

> [!IMPORTANT]
> The author is strictly designated as **Quarkova**. No personal author names are used.

---

## 2. Typography Engine

ProxyShield includes an advanced ASCII art rendering engine backed by `pyfiglet`, `rich`, and `colorama`.

### Supported Font Styles

| Style Name | Description | PyFiglet Mapping |
| :--- | :--- | :--- |
| `standard` | Classic FIGlet standard style | `standard` |
| `block` | High-density block letters | `block` |
| `3d` | Isometric pseudo-3D extrusion | `larry3d` |
| `huge` | Large prominent header typography | `big` / `colossal` |
| `shadow` | Outline with drop-shadow effects | `ansi_shadow` |
| `shade` | Halftone Unicode gradient blocks (`█`, `▓`, `▒`, `░`) | `ansi_shadow` + shade filter |
| `console` | Compact monospaced terminal styling | `term` |
| `slant` | Dynamic forward-leaning slanted characters | `slant` |
| `small` | Compact ASCII art for tight widths | `small` |
| `banner` | Wide banner lettering | `banner3` |
| `digital` | Segmented digital clock display | `digital` |

Over 570 backend fonts are accessible via `--list-fonts`.

### Text Effects

* **`shade`**: Applies progressive vertical halftone shading (`█` → `▓` → `▒`).
* **`shadow`**: Renders subtle right/bottom drop-shadow blocks (`░`).
* **`3d`**: Adds 3D extrusion borders (`▌`).
* **`outline`**: Converts solid blocks into hollow/wireframe glyphs (`□` / `◦`).
* **`none`**: Standard unmodified output.

### Color Modes & Gradients

* **Hex Codes:** e.g. `#ff5500`, `#00ffff`
* **RGB Values:** e.g. `rgb(255, 85, 0)` or `255,85,0`
* **Named Colors:** `cyan`, `yellow`, `red`, `green`, `blue`, `magenta`, `white`, `bright_red`, etc.
* **Gradients:**
  * Horizontal: Interpolated left-to-right across line width (`--gradient red,blue`).
  * Vertical: Interpolated top-to-bottom across ASCII height.
* **Rainbow:** 7-stage vibrant spectral cycle.
* **Neon:** High-intensity glowing contrast with soft highlights.

---

## 3. Configuration Management

Configuration is stored in INI format at:
```bash
~/.config/proxyshield/branding.txt
```

### Example `branding.txt`

```ini
[IDENTITY]
tool_name = ProxyShield
author = Quarkova
organization = Quarkova
version = 1.0.0
codename = Network Guardian
description = Open Source Network Security Toolkit
tagline = Learn. Test. Secure.
website = https://quarkova.com
license = MIT

[BANNER]
enabled = true
text = ProxyShield
font = 3d
alignment = center
effect = shade
background = none

[COLORS]
mode = gradient
color_start = #ff5500
color_end = #00ffff
gradient = true
rainbow = false
bold = true

[DISPLAY]
show_author = true
show_version = true
show_website = true
show_tagline = true
show_license = true
show_system_info = true
show_menu = true

[THEME]
name = dark
primary = cyan
secondary = yellow
success = green
warning = yellow
error = red
```

---

## 4. Security & File Permissions

To safeguard branding integrity and prevent unauthorized modifications:
* **Directory Permission:** `chmod 700 ~/.config/proxyshield` (owner read/write/execute only).
* **File Permission:** `chmod 600 ~/.config/proxyshield/branding.txt` (owner read/write only).
* **World-Writable Prohibition:** Configuration is never made world-writable (`chmod 777` is strictly forbidden).
* **Safe Parser:** Bash scripts do **not** use `source` or `eval` on `branding.txt`, preventing arbitrary command injection.

Verify or enforce permissions at any time:
```bash
proxyshield config permissions --fix
```

---

## 5. CLI Commands

### Banner Commands

```bash
# Render default configured banner
proxyshield banner

# Custom text
proxyshield banner --text "HELLO WORLD"

# Custom font
proxyshield banner --font 3d
proxyshield banner --font huge

# Custom colors and gradients
proxyshield banner --color red
proxyshield banner --gradient red,blue
proxyshield banner --color rainbow

# Text alignment
proxyshield banner --align center
proxyshield banner --align left
proxyshield banner --align right

# Visual effects
proxyshield banner --effect shade
proxyshield banner --effect shadow

# Font gallery & listing
proxyshield banner --preview
proxyshield banner --list-fonts
```

### Config Commands

```bash
# Display active settings
proxyshield config show

# Validate keys, color hexes, and permissions
proxyshield config validate

# Edit in $EDITOR (nano / vim / notepad)
proxyshield config edit

# Restore defaults (prompts for confirmation)
proxyshield config reset

# Verify and secure permissions (chmod 600)
proxyshield config permissions
```

---

## 6. Bash Integration

Bash scripts can read the branding parameters safely using the dedicated CLI reader or AWK parser:

```bash
# Query single values
AUTHOR=$(python3 -m proxyshield.branding --get IDENTITY.author)
TOOL=$(python3 -m proxyshield.branding --get IDENTITY.tool_name)

# Render full banner in shell script
python3 -m proxyshield.branding --render
```

See [branding-preview.sh](file:///c:/Users/SUNIL%20MISHRA/OneDrive/Desktop/ProxyShield/scripts/branding-preview.sh) for a turnkey example.

