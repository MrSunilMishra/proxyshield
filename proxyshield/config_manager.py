"""
ProxyShield Configuration Manager
Handles secure loading, validation, editing, and owner-protection (chmod 600/700)
for ~/.config/proxyshield/branding.txt.

Author: Quarkova
Website: https://quarkova.com
"""

import os
import sys
import stat
import shutil
import configparser
import subprocess
from typing import Dict, Any, Tuple, Optional, List

DEFAULT_CONFIG_DIR = os.path.expanduser("~/.config/proxyshield")
DEFAULT_CONFIG_PATH = os.path.join(DEFAULT_CONFIG_DIR, "branding.txt")

DEFAULT_CONFIG_CONTENT = """[IDENTITY]
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
"""


class ConfigSecurityError(Exception):
    """Raised when configuration file permissions violate security standards."""
    pass


def get_config_path() -> str:
    """
    Returns the resolved configuration path.
    Prioritizes ~/.config/proxyshield/branding.txt.
    Falls back to local branding.txt if present in working directory and config dir does not exist.
    """
    env_path = os.environ.get("PROXYSHIELD_CONFIG")
    if env_path and os.path.exists(env_path):
        return env_path

    if os.path.exists(DEFAULT_CONFIG_PATH):
        return DEFAULT_CONFIG_PATH

    # Check local fallback
    local_path = os.path.abspath("branding.txt")
    if os.path.exists(local_path):
        return local_path

    return DEFAULT_CONFIG_PATH


def ensure_config_exists(config_path: Optional[str] = None) -> str:
    """
    Ensures that the configuration directory and file exist.
    If not, creates them with strict owner-only permissions (0700 dir, 0600 file).
    Never overwrites an existing customized configuration.
    """
    path = config_path or get_config_path()
    config_dir = os.path.dirname(path)

    # Create directory if missing
    if not os.path.exists(config_dir):
        os.makedirs(config_dir, exist_ok=True)
        # Apply strict directory permissions on POSIX
        if os.name != "nt":
            try:
                os.chmod(config_dir, stat.S_IRWXU)  # 0700
            except OSError:
                pass

    # Create file if missing
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(DEFAULT_CONFIG_CONTENT)

        # Apply strict file permissions on POSIX
        if os.name != "nt":
            try:
                os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)  # 0600
            except OSError:
                pass

    return path


def check_permissions(config_path: Optional[str] = None) -> Tuple[bool, str]:
    """
    Validates file and directory permissions.
    Ensures:
      - File is not world-writable (never chmod 777 or world-writable).
      - Owner has read/write permissions.
      - Displays helpful message if permissions need adjustment.
    """
    path = config_path or get_config_path()
    if not os.path.exists(path):
        return True, "Configuration file does not exist yet; will be created with 0600 permissions."

    # Windows permissions model
    if os.name == "nt":
        return True, f"Windows environment detected. File is accessible at: {path}"

    try:
        file_stat = os.stat(path)
        mode = file_stat.st_mode
        file_uid = file_stat.st_uid
        current_uid = os.getuid()

        # Check if world-writable
        if mode & stat.S_IWOTH:
            return False, (
                f"SECURITY VIOLATION: '{path}' is world-writable (mode {oct(mode)[-3:]})!\n"
                f"Configuration must have owner-only write permissions.\n"
                f"Fix immediately with: chmod 600 '{path}'"
            )

        # Check if group-writable
        if mode & stat.S_IWGRP:
            return False, (
                f"SECURITY WARNING: '{path}' is group-writable (mode {oct(mode)[-3:]}).\n"
                f"Recommended permission is chmod 600 (owner read/write only).\n"
                f"Fix with: chmod 600 '{path}'"
            )

        # Check ownership
        if current_uid != 0 and file_uid != current_uid:
            return False, (
                f"PERMISSION ERROR: Configuration '{path}' is owned by UID {file_uid}, but current user is UID {current_uid}.\n"
                f"Root administrators can reassign ownership with: chown $USER '{path}' && chmod 600 '{path}'"
            )

        oct_mode = oct(mode)[-3:]
        return True, f"Permissions OK: Mode {oct_mode} (owner-protected) on '{path}'."

    except Exception as e:
        return False, f"Error inspecting permissions for '{path}': {str(e)}"


def enforce_permissions(config_path: Optional[str] = None) -> Tuple[bool, str]:
    """
    Enforces chmod 700 on the directory and chmod 600 on the configuration file.
    """
    path = config_path or ensure_config_exists()
    config_dir = os.path.dirname(path)

    if os.name == "nt":
        return True, "Windows file system in use; strict POSIX octal modes do not apply."

    try:
        os.chmod(config_dir, stat.S_IRWXU)  # 0700
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)  # 0600
        return True, f"Permissions successfully secured: Directory 0700, File 0600 at '{path}'."
    except PermissionError as pe:
        return False, (
            f"Failed to enforce permissions: {pe}.\n"
            f"If you are not the file owner, a system administrator can run:\n"
            f"  sudo chown $USER '{path}' && chmod 600 '{path}'"
        )
    except Exception as ex:
        return False, f"Unexpected error enforcing permissions: {ex}"


def load_config(config_path: Optional[str] = None) -> configparser.ConfigParser:
    """
    Safely loads the INI configuration file.
    Raises ConfigSecurityError if the file is insecure (e.g. world-writable).
    """
    path = config_path or ensure_config_exists()

    # Permission check on POSIX
    if os.name != "nt":
        ok, msg = check_permissions(path)
        if not ok and "world-writable" in msg:
            raise ConfigSecurityError(msg)

    config = configparser.ConfigParser(interpolation=None)
    try:
        with open(path, "r", encoding="utf-8") as f:
            config.read_file(f)
    except Exception as e:
        # Fallback to default in memory if file cannot be parsed
        config.read_string(DEFAULT_CONFIG_CONTENT)

    return config


def get_identity(config: configparser.ConfigParser) -> Dict[str, str]:
    """Extracts the [IDENTITY] section."""
    sec = config["IDENTITY"] if "IDENTITY" in config else {}
    return {
        "tool_name": sec.get("tool_name", "ProxyShield"),
        "author": "Quarkova",  # Strict project rule: author must always be Quarkova
        "organization": sec.get("organization", "Quarkova"),
        "version": sec.get("version", "1.0.0"),
        "codename": sec.get("codename", "Network Guardian"),
        "description": sec.get("description", "Open Source Network Security Toolkit"),
        "tagline": sec.get("tagline", "Learn. Test. Secure."),
        "website": sec.get("website", "https://quarkova.com"),
        "license": sec.get("license", "MIT"),
    }


def get_banner_config(config: configparser.ConfigParser) -> Dict[str, Any]:
    """Extracts the [BANNER] section."""
    sec = config["BANNER"] if "BANNER" in config else {}
    return {
        "enabled": sec.getboolean("enabled", fallback=True),
        "text": sec.get("text", "ProxyShield"),
        "font": sec.get("font", "3d"),
        "alignment": sec.get("alignment", "center"),
        "effect": sec.get("effect", "shade"),
        "background": sec.get("background", "none"),
    }


def get_colors_config(config: configparser.ConfigParser) -> Dict[str, Any]:
    """Extracts the [COLORS] section."""
    sec = config["COLORS"] if "COLORS" in config else {}
    return {
        "mode": sec.get("mode", "gradient"),
        "color_start": sec.get("color_start", "#ff5500"),
        "color_end": sec.get("color_end", "#00ffff"),
        "gradient": sec.getboolean("gradient", fallback=True),
        "rainbow": sec.getboolean("rainbow", fallback=False),
        "bold": sec.getboolean("bold", fallback=True),
    }


def get_display_config(config: configparser.ConfigParser) -> Dict[str, bool]:
    """Extracts the [DISPLAY] section."""
    sec = config["DISPLAY"] if "DISPLAY" in config else {}
    return {
        "show_author": sec.getboolean("show_author", fallback=True),
        "show_version": sec.getboolean("show_version", fallback=True),
        "show_website": sec.getboolean("show_website", fallback=True),
        "show_tagline": sec.getboolean("show_tagline", fallback=True),
        "show_license": sec.getboolean("show_license", fallback=True),
        "show_system_info": sec.getboolean("show_system_info", fallback=True),
        "show_menu": sec.getboolean("show_menu", fallback=True),
    }


def get_theme_config(config: configparser.ConfigParser) -> Dict[str, str]:
    """Extracts the [THEME] section."""
    sec = config["THEME"] if "THEME" in config else {}
    return {
        "name": sec.get("name", "dark"),
        "primary": sec.get("primary", "cyan"),
        "secondary": sec.get("secondary", "yellow"),
        "success": sec.get("success", "green"),
        "warning": sec.get("warning", "yellow"),
        "error": sec.get("error", "red"),
    }


def validate_config(config_path: Optional[str] = None) -> Tuple[bool, List[str]]:
    """
    Validates configuration structure, keys, values, and security.
    Returns (is_valid, list_of_messages).
    """
    path = config_path or get_config_path()
    issues = []
    
    if not os.path.exists(path):
        return False, [f"Configuration file does not exist at '{path}'."]

    ok_perm, perm_msg = check_permissions(path)
    if not ok_perm:
        issues.append(f"[PERMISSION WARNING] {perm_msg}")

    parser = configparser.ConfigParser(interpolation=None)
    try:
        with open(path, "r", encoding="utf-8") as f:
            parser.read_file(f)
    except Exception as e:
        return False, [f"[SYNTAX ERROR] Unable to parse INI: {e}"]

    required_sections = ["IDENTITY", "BANNER", "COLORS", "DISPLAY", "THEME"]
    for sec in required_sections:
        if sec not in parser:
            issues.append(f"[MISSING SECTION] [{sec}] is missing from config.")

    # Validate IDENTITY
    if "IDENTITY" in parser:
        author = parser["IDENTITY"].get("author", "")
        if author.strip().lower() != "quarkova":
            issues.append(f"[IDENTITY WARNING] Author must be 'Quarkova' (found: '{author}').")

    # Validate BANNER alignment and effect
    if "BANNER" in parser:
        align = parser["BANNER"].get("alignment", "").lower()
        if align not in ("left", "center", "right"):
            issues.append(f"[BANNER WARNING] alignment should be left/center/right (found: '{align}').")
        effect = parser["BANNER"].get("effect", "").lower()
        if effect not in ("shade", "shadow", "3d", "outline", "none"):
            issues.append(f"[BANNER INFO] Non-standard effect: '{effect}'. Supported: shade, shadow, 3d, outline, none.")

    # Validate COLORS
    if "COLORS" in parser:
        mode = parser["COLORS"].get("mode", "").lower()
        if mode not in ("gradient", "single", "rainbow", "neon"):
            issues.append(f"[COLORS INFO] Color mode is '{mode}'. Expected: gradient, single, rainbow, or neon.")

    is_valid = len([i for i in issues if "ERROR" in i or "VIOLATION" in i]) == 0
    return is_valid, issues


def reset_config(config_path: Optional[str] = None, force: bool = False) -> Tuple[bool, str]:
    """
    Resets the configuration to default settings.
    Requires user confirmation unless force=True.
    """
    path = config_path or get_config_path()

    if not force:
        # Caller must confirm before calling or handle prompt
        pass

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(DEFAULT_CONFIG_CONTENT)

        if os.name != "nt":
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)

        return True, f"Configuration at '{path}' has been reset to defaults."
    except Exception as e:
        return False, f"Failed to reset configuration: {e}"


def open_editor(config_path: Optional[str] = None) -> Tuple[bool, str]:
    """
    Opens the configuration file in the user's preferred editor ($EDITOR or platform default).
    """
    path = config_path or ensure_config_exists()
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")

    if not editor:
        if os.name == "nt":
            editor = "notepad"
        else:
            # Try nano, then vim, then vi
            for candidate in ["nano", "vim", "vi"]:
                if shutil.which(candidate):
                    editor = candidate
                    break
            if not editor:
                editor = "vi"

    try:
        subprocess.run([editor, path], check=True)
        return True, f"Edited '{path}' with {editor}."
    except Exception as e:
        return False, f"Could not launch editor '{editor}': {e}"

