#!/usr/bin/env bash
# ==============================================================================
# ProxyShield - Automated 1-Click Bootstrap & Launch Script
#
# Automatically:
#  1. Detects OS environment (Linux, Termux, macOS, Windows Git-Bash)
#  2. Installs 'uv' package manager if missing (zero system pollution)
#  3. Creates isolated virtual environment (.venv)
#  4. Installs ProxyShield and all dependencies
#  5. Activates environment and executes ProxyShield CLI (pxs)
#
# Author: Quarkova
# Organization: Quarkova
# Website: https://quarkova.com
# License: MIT
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ANSI Colors
CYAN="\033[36m"
GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
RESET="\033[0m"
BOLD="\033[1m"

echo -e "${CYAN}${BOLD}[ProxyShield Bootstrap] Initializing automated environment...${RESET}"

# ------------------------------------------------------------------------------
# 1. Detect & Ensure 'uv' Package Manager
# ------------------------------------------------------------------------------
# Add standard user cargo/local bin directories to PATH if present
export PATH="${HOME}/.cargo/bin:${HOME}/.local/bin:${PATH}"

UV_BIN=""
if command -v uv >/dev/null 2>&1; then
    UV_BIN="uv"
elif [ -f "${HOME}/.cargo/bin/uv" ]; then
    UV_BIN="${HOME}/.cargo/bin/uv"
elif [ -f "${HOME}/.local/bin/uv" ]; then
    UV_BIN="${HOME}/.local/bin/uv"
fi

if [ -z "$UV_BIN" ]; then
    echo -e "${YELLOW}[!] 'uv' not found. Installing uv automatically (standalone, fast, isolated)...${RESET}"
    if command -v curl >/dev/null 2>&1; then
        curl -LsSf https://astral.sh/uv/install.sh | sh || true
    elif command -v wget >/dev/null 2>&1; then
        wget -qO- https://astral.sh/uv/install.sh | sh || true
    fi

    # Refresh PATH check
    export PATH="${HOME}/.cargo/bin:${HOME}/.local/bin:${PATH}"
    if command -v uv >/dev/null 2>&1; then
        UV_BIN="uv"
    elif [ -f "${HOME}/.cargo/bin/uv" ]; then
        UV_BIN="${HOME}/.cargo/bin/uv"
    fi
fi

# ------------------------------------------------------------------------------
# 2. Create Isolated Virtual Environment (.venv)
# ------------------------------------------------------------------------------
VENV_PYTHON=""
if [ -n "$UV_BIN" ]; then
    if [ ! -d ".venv" ]; then
        echo -e "${CYAN}[*] Creating isolated virtual environment via uv (.venv)...${RESET}"
        "$UV_BIN" venv .venv
    fi

    # Locate venv python binary (POSIX vs Windows Git Bash)
    if [ -f ".venv/bin/python" ]; then
        VENV_PYTHON=".venv/bin/python"
    elif [ -f ".venv/Scripts/python.exe" ]; then
        VENV_PYTHON=".venv/Scripts/python.exe"
    fi

    # Check if installed
    if [ ! -f ".venv/.installed" ]; then
        echo -e "${CYAN}[*] Installing dependencies into isolated environment with uv...${RESET}"
        "$UV_BIN" pip install -e .[dev]
        touch ".venv/.installed"
    fi
else
    # Fallback to standard python3 -m venv if uv install was blocked by network/firewall
    echo -e "${YELLOW}[!] Falling back to standard Python venv...${RESET}"
    PYTHON_CMD="python3"
    if ! command -v python3 >/dev/null 2>&1 && command -v python >/dev/null 2>&1; then
        PYTHON_CMD="python"
    fi

    if [ ! -d ".venv" ]; then
        "$PYTHON_CMD" -m venv .venv
    fi

    if [ -f ".venv/bin/python" ]; then
        VENV_PYTHON=".venv/bin/python"
    elif [ -f ".venv/Scripts/python.exe" ]; then
        VENV_PYTHON=".venv/Scripts/python.exe"
    fi

    if [ ! -f ".venv/.installed" ]; then
        "$VENV_PYTHON" -m pip install -r requirements.txt
        "$VENV_PYTHON" -m pip install -e .
        touch ".venv/.installed"
    fi
fi

echo -e "${GREEN}${BOLD}[✓] Environment ready. Launching ProxyShield (pxs)...${RESET}\n"

# ------------------------------------------------------------------------------
# 3. Execute ProxyShield with all forwarded arguments
# ------------------------------------------------------------------------------
exec "$VENV_PYTHON" -m proxyshield.cli "$@"
