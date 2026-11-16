# ProxyShield 🛡️

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Linux | Termux | macOS | Windows](https://img.shields.io/badge/platform-Linux%20%7C%20Termux%20%7C%20macOS%20%7C%20Windows-green.svg)](https://github.com/MrSunilMishra/proxyshield)
[![Organization: Quarkova](https://img.shields.io/badge/organization-Quarkova-orange.svg)](https://quarkova.com)

> **Advanced CFonts-Style Terminal Branding & Typography Engine for Network Security & Diagnostics Tools.**

```
             _____                      _____ _     _      _     _
            |  __ \                    / ____| |   █_█    | |   | |
            | |__█ | __ _____  ___   _| █___ | |__  _  ___| | __| |
            |  ___/ ▓__/ _ \ \/ / | | |\___ \| ▓_ \| |/ _ \ |/ _▓ |
            | |   | | | ▓_▓ ▓  ▓| |_| |____▓ | | | | |  __/ | ▓_| |
            |_|   |_|  \___/_/\_\\__▒ |_____/|_| |_|_|\___|_|\__▒_|
                                  __/ |
                                 |___/

                    v1.0.0 | Author: Quarkova | MIT License
                            « Learn. Test. Secure. »
                              https://quarkova.com
```

---

## ⚠️ Important Disclaimer & Educational Notice

> [!CAUTION]
> **FOR EDUCATIONAL, RESEARCH, AND AUTHORIZED DIAGNOSTIC PURPOSES ONLY.**
>
> * **DO NOT USE FOR DDOS OR DOS ATTACKS**: ProxyShield is designed strictly as a terminal branding, typography, and network diagnostic framework for learning and defensive testing. It must **NEVER** be used to launch Distributed Denial of Service (DDoS) attacks, flood network infrastructure, disrupt web services, or conduct unauthorized stress testing.
> * **LEGAL & ETHICAL USE**: You may only test and diagnose systems and networks that you own or have received **explicit, written authorization** to test. Unauthorized attacks against computers, networks, or services are illegal under federal and international laws (such as the US Computer Fraud and Abuse Act - CFAA).
> * **NO LIABILITY**: The author (**Quarkova**), developers, and contributors assume **no liability** and are not responsible for any misuse, damage, service downtime, or legal repercussions resulting from the use of this software. By using this tool, you agree to take full personal responsibility for complying with all applicable laws.

---

## 🌟 Key Features

* **CFonts-Inspired Terminal Typography**: Support for 11 core font styles (`standard`, `block`, `3d`, `huge`, `shadow`, `shade`, `console`, `slant`, `small`, `banner`, `digital`) and 570+ FIGlet backend fonts.
* **TrueColor & Dual Gradients**: 24-bit TrueColor RGB, HEX `#RRGGBB`, horizontal and vertical smooth multi-stop gradients, 7-color rainbow spectrum, and neon glowing effects.
* **Typographical Text Effects**: Halftone Unicode block shading (`█`, `▓`, `▒`, `░`), drop-shadows, 3D extrusions, and wireframe outlines.
* **Terminal Responsiveness**: Automatic terminal width detection (`shutil.get_terminal_size()`), text alignment (`left`, `center`, `right`), and automatic font resizing/fallback for narrow terminals.
* **Protected Configuration (`branding.txt`)**: Centralized INI configuration stored at `~/.config/proxyshield/branding.txt` secured with owner-only permissions (`chmod 600` for file, `chmod 700` for directory).
* **Dual Python & Bash Integration**: Bash scripts read configuration directly via AWK safe parsing without `source` or `eval`, eliminating arbitrary code execution risks.
* **Cross-Platform**: Fully compatible with Linux, Android Termux, macOS, and Windows.

---

## 🚀 Step-by-Step Installation Procedure

### ⚡ Recommended: Fast & Isolated Setup with `uv` (Zero System Pollution)

To keep your system clean and undisturbed, use [**uv**](https://github.com/astral-sh/uv) (ultra-fast Python package and project manager). All dependencies are contained in an isolated local `.venv` without touching global system packages:

```bash
# 1. Install uv (if not already installed)
# Linux / macOS / Termux:
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows (PowerShell):
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 2. Clone the repository
git clone https://github.com/MrSunilMishra/proxyshield.git
cd proxyshield

# 3. Create isolated virtual environment
uv venv .venv

# 4. Activate the virtual environment
# Linux / macOS / Termux:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# 5. Install ProxyShield in isolated environment
uv pip install -e .[dev]
```

---

### Alternative: Standard Python & Virtual Environment

If you prefer standard Python tooling:

#### 🐧 On Linux & macOS
```bash
git clone https://github.com/MrSunilMishra/proxyshield.git
cd proxyshield

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install -e .
```

#### 📱 On Android (Termux)
```bash
pkg update && pkg upgrade -y
pkg install python git -y

git clone https://github.com/MrSunilMishra/proxyshield.git
cd proxyshield

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install -e .
```

#### 🪟 On Windows (PowerShell)
```powershell
git clone https://github.com/MrSunilMishra/proxyshield.git
cd proxyshield

python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
pip install -e .
```

Verify your installation:
```bash
proxyshield --version
# Output: ProxyShield 1.0.0 by Quarkova
```

---

## 📖 How to Use ProxyShield

### 1. Launch Interactive Startup Screen

Simply run `proxyshield` without arguments to view the terminal startup screen with branding badges and the command directory:

```bash
proxyshield
```

---

### 2. Generate Custom Typography Banners

Use the `proxyshield banner` command to render banners with full customization:

#### Custom Text
```bash
proxyshield banner --text "SECURITY SCAN"
```

#### Font Styles
Choose from `standard`, `block`, `3d`, `huge`, `shadow`, `shade`, `console`, `slant`, `small`, `banner`, or `digital`:
```bash
proxyshield banner --text "PROXYSHIELD" --font 3d
proxyshield banner --text "FIREWALL" --font huge
proxyshield banner --text "TERMINAL" --font slant
```

#### Color Effects & Gradients
```bash
# Single named color or hex code
proxyshield banner --color red
proxyshield banner --color "#00ffff"

# Horizontal two-color gradient
proxyshield banner --gradient red,blue
proxyshield banner --gradient "#ff5500,#00ffff"

# Rainbow spectrum effect
proxyshield banner --color rainbow
```

#### Text Visual Effects
Add halftone block shading, drop shadows, or 3D extrusions:
```bash
# Halftone progressive block shading
proxyshield banner --font shadow --effect shade

# Drop shadow blocks
proxyshield banner --font standard --effect shadow

# 3D extrusion
proxyshield banner --font slant --effect 3d
```

#### Alignment
Align text relative to your current terminal width:
```bash
proxyshield banner --align center
proxyshield banner --align left
proxyshield banner --align right
```

#### Explore All Fonts & Visual Showcase
```bash
# View interactive typography gallery showcase
proxyshield banner --preview

# List all 570+ available font styles
proxyshield banner --list-fonts
```

---

### 3. Free Proxy Pool & Network Diagnostics

ProxyShield includes a multi-source free proxy aggregator that pulls, deduplicates, benchmarks, and filters live proxies from both **Geonode** and **ProxyScrape** APIs:
* **ProxyScrape v4 API**: `https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=json`
* **Geonode Proxy API**: `https://proxylist.geonode.com/api/proxy-list?page=1&limit=500&sort_by=responseTime&sort_type=asc`

#### Fetch & Filter Free Proxies
```bash
# Fetch fastest live proxies combining both Geonode and ProxyScrape (default)
proxyshield proxy

# Specify provider source (--source all | geonode | proxyscrape)
proxyshield proxy fetch --source geonode --limit 20
proxyshield proxy fetch --source proxyscrape --limit 20

# Filter by protocol (http, socks4, socks5)
proxyshield proxy fetch --protocol socks5 --limit 15
proxyshield proxy fetch --protocol http --ssl

# Filter by country code and anonymity level (elite, anonymous)
proxyshield proxy fetch --country US --anonymity elite
proxyshield proxy fetch --country DE --protocol socks5

# Export live proxies to file (.txt or .json)
proxyshield proxy fetch --limit 50 --output proxies.txt
proxyshield proxy fetch --source geonode --format json --output proxies.json
```

#### Concurrent Live Proxy Diagnostics & Health Check
Test live reachability, measure real round-trip latency, and diagnose dead proxies across concurrent threads:
```bash
# Concurrently diagnose 15 live proxies
proxyshield proxy check --limit 15 --timeout 3

# Save only verified working proxies to file
proxyshield proxy check --limit 30 --alive-only --output working_proxies.txt
```

#### Instant Random Working Proxy
Fetch a single formatted proxy endpoint for instant use in CLI tools, curl, or scripts:
```bash
proxyshield proxy random
# Output: socks5://120.220.197.198:59999

# Specific protocol or country
proxyshield proxy random --protocol socks5 --country US
```

---

### 4. Configuration Management

ProxyShield stores its settings in an INI file at:
```bash
~/.config/proxyshield/branding.txt
```

Manage and audit this configuration with the `proxyshield config` commands:

| Command | Description |
| :--- | :--- |
| `proxyshield config show` | Displays the current active branding configuration. |
| `proxyshield config validate` | Verifies syntax, required keys, color formats, and file permissions. |
| `proxyshield config edit` | Opens `branding.txt` in your system editor (`$EDITOR`, `nano`, `vim`, `notepad`). |
| `proxyshield config permissions` | Checks file permissions and flags any world-writable risks. |
| `proxyshield config permissions --fix` | Enforces `chmod 700` on the directory and `chmod 600` on the file. |
| `proxyshield config reset` | Restores default branding configuration (requests confirmation `[y/N]`). |

---

### 4. Bash Script Integration

If you are developing Bash or shell automation scripts, you can integrate ProxyShield branding **without executing unsafe `source` calls**:

```bash
# Execute the included turnkey Bash preview script
chmod +x scripts/branding-preview.sh
./scripts/branding-preview.sh
```

#### Querying values directly from Bash:
```bash
# Safely extract branding fields via Python bridge
TOOL_NAME=$(python3 -m proxyshield.branding --get IDENTITY.tool_name)
AUTHOR=$(python3 -m proxyshield.branding --get IDENTITY.author)
VERSION=$(python3 -m proxyshield.branding --get IDENTITY.version)

# Render full banner directly in any shell script
python3 -m proxyshield.branding --render
```

---

## 🔒 Security & Permission Model

ProxyShield enforces strict permission standards to prevent unauthorized modification:

1. **Owner-Only Access**:
   * Config Directory: `chmod 700 ~/.config/proxyshield`
   * Config File: `chmod 600 ~/.config/proxyshield/branding.txt`
2. **Prohibition of World-Writable Files**:
   * Mode `777` is strictly forbidden. If detected, ProxyShield reports a security alert.
3. **Safe Parsing**:
   * Bash scripts never evaluate `branding.txt` with `source` or `eval`. An isolated AWK parser prevents command injection.
4. **Update Safety**:
   * Software updates and installations never overwrite an existing user configuration.

---

## 🧪 Running Automated Tests

Run the complete test suite with `pytest`:

```bash
pytest -v
```

This validates:
* Font style resolution across all 11 required styles.
* TrueColor RGB and HEX parsing, interpolation, and gradient rendering.
* Halftone Unicode shade, shadow, 3D, and outline effects.
* Configuration validation, security error handling, and reset routines.
* Identity enforcement (verifying Author is always `Quarkova`).

---

## 📁 Repository Structure

```
proxyshield/
├── proxyshield/               # Core Python Package
│   ├── __init__.py           # Package identity & metadata
│   ├── cli.py                # Main CLI entry point (banner, config)
│   ├── font_engine.py        # CFonts typography & effect engine
│   ├── color_engine.py       # 24-bit TrueColor, gradients & rainbow
│   ├── config_manager.py     # Owner-protected config manager (0600/0700)
│   ├── branding.py           # Branding badges & shell integration bridge
│   └── banner.py             # Standalone banner & showcase preview
├── scripts/
│   └── branding-preview.sh   # Turnkey safe Bash integration script
├── docs/
│   └── BRANDING.md           # Deep-dive architecture & customization guide
├── tests/                    # Automated pytest test suite
│   ├── test_color_engine.py
│   ├── test_config.py
│   └── test_font_and_banner.py
├── branding.example.txt      # Factory default configuration template
├── pyproject.toml            # Build system & CLI entry point configuration
├── requirements.txt          # Python dependencies
└── README.md                 # Complete user guide & documentation
```

---

## 📜 Project Identity & License

* **Tool Name**: ProxyShield
* **Author / Organization**: [Quarkova](https://quarkova.com)
* **Website**: [https://quarkova.com](https://quarkova.com)
* **License**: [MIT](LICENSE) - Open Source Network Security & Diagnostics Toolkit
* **Repository**: [https://github.com/MrSunilMishra/proxyshield.git](https://github.com/MrSunilMishra/proxyshield.git)

*Learn. Test. Secure.*

