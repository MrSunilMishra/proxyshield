#!/usr/bin/env bash
# ==============================================================================
# ProxyShield - Bash Branding Preview & Integration Script
#
# Safe Configuration Reader: Reads branding.txt WITHOUT sourcing or evaluating
# arbitrary shell code to protect against arbitrary command execution.
#
# Author: Quarkova
# Organization: Quarkova
# Website: https://quarkova.com
# License: MIT
# ==============================================================================

set -euo pipefail

# Locate Configuration File
CONFIG_DIR="${HOME}/.config/proxyshield"
CONFIG_FILE="${CONFIG_DIR}/branding.txt"

# Fallback to local branding.txt or branding.example.txt if not in ~/.config
if [ ! -f "$CONFIG_FILE" ]; then
    if [ -f "./branding.txt" ]; then
        CONFIG_FILE="./branding.txt"
    elif [ -f "../branding.txt" ]; then
        CONFIG_FILE="../branding.txt"
    elif [ -f "./branding.example.txt" ]; then
        CONFIG_FILE="./branding.example.txt"
    fi
fi

# ------------------------------------------------------------------------------
# 1. Security Check: Enforce Owner-Only Permissions (chmod 600)
# ------------------------------------------------------------------------------
check_file_security() {
    local target="$1"
    if [ -f "$target" ]; then
        # Check permissions using stat (Linux/Termux compatible)
        local perms="600"
        if perms_out=$(stat -c "%a" "$target" 2>/dev/null); then
            perms="$perms_out"
        elif perms_out=$(stat -f "%Lp" "$target" 2>/dev/null); then
            perms="$perms_out"
        fi

        # Check for world-writable permission (last digit >= 2)
        local world_perm="${perms: -1}"
        if [ "$world_perm" -ge 2 ]; then
            echo -e "\033[31m[SECURITY WARNING] '${target}' is world-writable (mode ${perms})!\033[0m" >&2
            echo -e "\033[33mFix immediately with: chmod 600 '${target}'\033[0m" >&2
        fi
    fi
}

if [ -f "$CONFIG_FILE" ]; then
    check_file_security "$CONFIG_FILE"
fi

# ------------------------------------------------------------------------------
# 2. Safe INI Parser in AWK (Never uses 'source' or 'eval')
# ------------------------------------------------------------------------------
safe_ini_get() {
    local section="$1"
    local key="$2"
    local file="$3"

    if [ ! -f "$file" ]; then
        echo ""
        return
    fi

    # AWK-based parser: reads specified section and key, strips whitespace and quotes
    awk -F '=' -v sec="$section" -v k="$key" '
        BEGIN { in_sec = 0; val = "" }
        /^[ \t]*\[/ {
            gsub(/[\[\] \t]/, "", $0)
            if (tolower($0) == tolower(sec)) {
                in_sec = 1
            } else {
                in_sec = 0
            }
            next
        }
        in_sec {
            # Strip comments
            split($0, parts, ";")
            split(parts[1], subparts, "#")
            line = subparts[1]

            split(line, kv, "=")
            curr_k = kv[1]
            gsub(/^[ \t]+|[ \t]+$/, "", curr_k)

            if (tolower(curr_k) == tolower(k)) {
                # Extract value after first equals sign
                curr_v = substr(line, index(line, "=") + 1)
                gsub(/^[ \t]+|[ \t]+$/, "", curr_v)
                val = curr_v
                exit
            }
        }
        END { print val }
    ' "$file"
}

# ------------------------------------------------------------------------------
# 3. Execution: Prioritize Isolated Virtualenv (.venv) or System Python
# ------------------------------------------------------------------------------
PYTHON_BIN=""
if [ -f "./.venv/bin/python" ]; then
    PYTHON_BIN="./.venv/bin/python"
elif [ -f "./.venv/Scripts/python.exe" ]; then
    PYTHON_BIN="./.venv/Scripts/python.exe"
elif [ -f "../.venv/bin/python" ]; then
    PYTHON_BIN="../.venv/bin/python"
elif [ -f "../.venv/Scripts/python.exe" ]; then
    PYTHON_BIN="../.venv/Scripts/python.exe"
elif command -v uv >/dev/null 2>&1; then
    PYTHON_BIN="uv run python"
elif command -v python3 >/dev/null 2>&1 && python3 -c "import sys" >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1 && python -c "import sys" >/dev/null 2>&1; then
    PYTHON_BIN="python"
fi

if [ -n "$PYTHON_BIN" ] && $PYTHON_BIN -c "import proxyshield.branding" >/dev/null 2>&1; then
    # Full fidelity Python branding engine
    $PYTHON_BIN -m proxyshield.branding --render
    exit 0
fi

# ------------------------------------------------------------------------------
# 4. Pure POSIX/Bash Graceful Fallback if Python module is not yet installed
# ------------------------------------------------------------------------------
TOOL_NAME=$(safe_ini_get "IDENTITY" "tool_name" "$CONFIG_FILE")
AUTHOR="Quarkova" # Enforce Quarkova project rule
TAGLINE=$(safe_ini_get "IDENTITY" "tagline" "$CONFIG_FILE")
VERSION=$(safe_ini_get "IDENTITY" "version" "$CONFIG_FILE")
WEBSITE=$(safe_ini_get "IDENTITY" "website" "$CONFIG_FILE")
LICENSE=$(safe_ini_get "IDENTITY" "license" "$CONFIG_FILE")

[ -z "$TOOL_NAME" ] && TOOL_NAME="ProxyShield"
[ -z "$TAGLINE" ] && TAGLINE="Learn. Test. Secure."
[ -z "$VERSION" ] && VERSION="1.0.0"
[ -z "$WEBSITE" ] && WEBSITE="https://quarkova.com"
[ -z "$LICENSE" ] && LICENSE="MIT"

# Colors
C_CYAN="\033[36m"
C_YELLOW="\033[33m"
C_WHITE="\033[1;37m"
C_GRAY="\033[90m"
C_RESET="\033[0m"

echo ""
echo -e "${C_CYAN}  ____                       ____  _     _      _     _   ${C_RESET}"
echo -e "${C_CYAN} |  _ \ _ __ _____  ___   _/ ___|| |__ (_) ___| | __| |  ${C_RESET}"
echo -e "${C_CYAN} | |_) | '__/ _ \ \/ / | | \___ \| '_ \| |/ _ \ |/ _\` |  ${C_RESET}"
echo -e "${C_CYAN} |  __/| | | (_) >  <| |_| |___) | | | | |  __/ | (_| |  ${C_RESET}"
echo -e "${C_CYAN} |_|   |_|  \___/_/\_\\__, |____/|_| |_|_|\___|_|\__,_|  ${C_RESET}"
echo -e "${C_CYAN}                      |___/                               ${C_RESET}"
echo ""
echo -e "       ${C_CYAN}v${VERSION}${C_RESET} | ${C_YELLOW}Author: ${AUTHOR}${C_RESET} | ${C_GRAY}${LICENSE} License${C_RESET}"
echo -e "              ${C_WHITE}« ${TAGLINE} »${C_RESET}"
echo -e "                ${C_CYAN}${WEBSITE}${C_RESET}"
echo ""
