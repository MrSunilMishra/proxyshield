# ProxyShield – Advanced CFonts-Style Terminal Branding Engine

## 1. Project Identity

Tool Name: ProxyShield  
Author: Quarkova  
Organization: Quarkova  
Website: https://quarkova.com  
License: MIT  
Category: Network Security & Diagnostics

IMPORTANT: Author must always be Quarkova. Do not use any personal author name.

## 2. Terminal Typography Engine

Create an advanced terminal typography engine inspired by CFonts.

It must support:

### Font Styles

- Standard
- Block
- 3D
- Huge
- Shadow
- Shade
- Console
- Slant
- Small
- Banner
- Digital
- Custom ASCII fonts

Use Python libraries such as:

- pyfiglet
- Rich
- Colorama

### Color Effects

- Single color
- Multiple colors
- RGB colors
- HEX colors
- Rainbow gradient
- Horizontal gradient
- Vertical gradient
- Bright colors
- Custom color combinations

### Text Effects

- 3D appearance
- Shadow
- Outline
- Background patterns
- Neon-style colors
- Bold typography

### Text Alignment

- Left
- Center
- Right

### Terminal Features

- Automatic terminal width detection
- Automatic font resizing or fallback
- Unicode support
- ANSI color support
- Graceful fallback for unsupported terminals

## 3. Branding Configuration

Create a customizable file named:

`branding.txt`

Example:

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

## 4. Customization Commands

Support these commands:

`proxyshield banner`

`proxyshield banner --text "HELLO WORLD"`

`proxyshield banner --font 3d`

`proxyshield banner --font huge`

`proxyshield banner --color red`

`proxyshield banner --gradient red,blue`

`proxyshield banner --align center`

`proxyshield banner --effect shade`

`proxyshield banner --list-fonts`

`proxyshield banner --preview`

All banner options must work independently of the network testing modules.

## 5. Protected Configuration File

The branding configuration must have owner-only write permissions.

On Linux:

- Set file owner to the installing user.
- Apply permission `chmod 600 branding.txt`.
- Apply directory permission `chmod 700` to the private configuration directory.
- Verify permissions during installation.
- Never make the configuration world-writable.
- Do not use chmod 777.
- Do not overwrite an existing customized configuration during updates.

Suggested location:

`~/.config/proxyshield/branding.txt`

The owner can edit all branding settings.

Python and Bash scripts should have read access to the same file.

If another user runs the application without permission, display a helpful error instead of silently modifying permissions.

Explain that root administrators can still change ownership and permissions.

## 6. Configuration Management

Provide:

`proxyshield config show`

`proxyshield config validate`

`proxyshield config edit`

`proxyshield config reset`

`proxyshield config permissions`

The reset command must request confirmation before overwriting customized settings.

Never reset or overwrite the configuration automatically during an update.

## 7. Bash Integration

Bash scripts must read the same branding configuration.

Do not execute branding.txt using `source`.

Use a safe INI parser or a dedicated Python configuration reader to avoid arbitrary shell command execution.

The Bash startup script should display the same banner and branding as the Python CLI.

## 8. Project Structure

Add:

- proxyshield/banner.py
- proxyshield/branding.py
- proxyshield/color_engine.py
- proxyshield/font_engine.py
- proxyshield/config_manager.py
- branding.example.txt
- scripts/branding-preview.sh
- docs/BRANDING.md

## 9. Installation Dependencies

Install and verify:

- pyfiglet
- rich
- colorama

Keep dependencies compatible with Python 3 and Termux.

## 10. Final Acceptance Criteria

1. The terminal startup screen must resemble the supplied CFonts visual reference.
2. Multiple ASCII font styles must work.
3. Gradient and custom colors must work.
4. The user must be able to change every branding field.
5. Author must display as Quarkova.
6. Python and Bash must use the same configuration.
7. Configuration must be owner-protected.
8. Updates must preserve user customization.
9. Linux and Termux must both be supported.
10. Include automated tests for configuration parsing, permissions and banner rendering.

Build a functional typography engine, not a static ASCII logo.
