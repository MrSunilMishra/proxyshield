# ProxyShield 🛡️

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Linux | Termux | macOS | Windows](https://img.shields.io/badge/platform-Linux%20%7C%20Termux%20%7C%20macOS%20%7C%20Windows-green.svg)](https://github.com/MrSunilMishra/proxyshield)
[![Organization: Quarkova](https://img.shields.io/badge/organization-Quarkova-orange.svg)](https://quarkova.com)

> **Advanced Public Proxy Intelligence, Transparency & Authorized Network Security Auditing Engine.**

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

## ⚠️ Privacy & Legal Transparency Notice

> [!IMPORTANT]
> **ProxyShield uses publicly available third-party proxy services for educational and authorized network security auditing. The operator's direct public IP is not intentionally used for target requests in strict proxy-only mode. Public proxy operators may observe, inspect or log traffic. ProxyShield does not guarantee anonymity, privacy or proxy security. All testing must be conducted against authorized targets.**

> [!CAUTION]
> **DO NOT USE FOR MALICIOUS ATTACKS OR DDOS:**
> * ProxyShield is strictly intended for defensive research, transparency auditing, and authorized diagnostic evaluations.
> * Never use this tool for unauthorized port scanning, denial-of-service, traffic flooding, or evading third-party security controls.
> * Always obtain explicit written authorization before auditing any target network.

---

## 🌟 Core Architecture & Capabilities

* **Public Proxy Discovery**: Configurable source registry pulling from **Geonode**, **ProxyScrape**, and manual imports (TXT/JSON). Tracks provider attribution, protocol (HTTP, HTTPS, SOCKS4, SOCKS5), and health history in SQLite.
* **Strict Direct-IP Protection**: Zero direct-fallback enforcement. Discovers the operator's real public IP as a baseline; if an observed exit IP unexpectedly matches the operator's IP or a proxy fails, the request is immediately aborted.
* **Multi-Proxy Security Auditing**: Executes low-rate, controlled HTTP requests across verified proxy endpoints against authorized targets.
* **Firewall Diagnostic Categorization**: Accurately classifies responses: `SUCCESS`, `HTTP_403`, `HTTP_429`, `HTTP_5XX`, `TCP_FAIL`, `TLS_FAIL`, `DNS_FAIL`, `PROXY_FAIL`, and true `FIREWALL_BLOCK` (backed by server-side log evidence).
* **Proxy Risk Scoring Engine**: Evaluates protocol security, HTTPS support, header leaks (`X-Forwarded-For`, `Via`), and assigns transparency labels: `Unverified`, `Verified Connectivity`, `High Risk`, and `Unavailable`.
* **Advanced Multi-Format Reporting**: Generates comprehensive transparency reports in **HTML**, **JSON**, and **CSV**.
* **CFonts Terminal Branding Engine**: 11 typography styles, 570+ FIGlet fonts, 24-bit TrueColor gradients, and owner-protected configuration (`chmod 600` / `700`).

---

## ⚡ Instant 1-Click Automated Setup (Zero Effort)

Simply clone and run the automated bootstrap script. It will **automatically install `uv`**, create the isolated `.venv` environment, install all dependencies, and launch ProxyShield:

### 🐧 On Linux, Android (Termux) & macOS:
```bash
# 1. Clone repository
git clone https://github.com/MrSunilMishra/proxyshield.git
cd proxyshield

# 2. Run the automated script (installs uv, sets up venv, and launches)
chmod +x run.sh
./run.sh
```

### 🪟 On Windows (PowerShell or CMD):
```powershell
# 1. Clone repository
git clone https://github.com/MrSunilMishra/proxyshield.git
cd proxyshield

# 2. Run the automated script (installs uv, sets up venv, and launches)
.\run.bat
```

> [!TIP]
> You can pass any options directly to the script:
> ```bash
> ./run.sh -h                                # Help overview
> ./run.sh p r                               # Get instant free proxy
> ./run.sh a -t "https://example.com"        # Run strict security audit
> ```

---

## 📥 Manual Download & Installation Procedure

Choose one of the two download options below:

### Option A: Download via Git (Recommended)
Open your terminal and run:
```bash
git clone https://github.com/MrSunilMishra/proxyshield.git
cd proxyshield
```

### Option B: Download as ZIP (No Git Required)
1. Download the ZIP package directly:  
   👉 **[Download ProxyShield ZIP](https://github.com/MrSunilMishra/proxyshield/archive/refs/heads/main.zip)**
2. Extract `proxyshield-main.zip` to a folder on your computer.
3. Open a terminal or PowerShell inside the extracted `proxyshield-main` folder.

---

## 🚀 How to Install & Run

### ⚡ Recommended: Fast & Isolated Setup with `uv` (Zero System Pollution)

To keep your system clean and undisturbed, use [**uv**](https://github.com/astral-sh/uv) (ultra-fast Python package and project manager). All dependencies are contained in an isolated local `.venv` without touching global system packages:

```bash
# 1. Install uv (if not already installed)
# Linux / macOS / Termux:
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows (PowerShell):
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 2. Inside the proxyshield directory, create the virtual environment:
uv venv .venv

# 3. Activate the environment:
# On Linux / macOS / Termux:
source .venv/bin/activate
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Windows Command Prompt (CMD):
.venv\Scripts\activate.bat

# 4. Install ProxyShield & dependencies:
uv pip install -e .[dev]
```

---

### Alternative: Standard Python Setup (Without `uv`)

#### 🐧 On Linux & macOS
```bash
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install -e .
```

#### 📱 On Android (Termux)
```bash
pkg update && pkg install python git -y
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
pip install -e .
```

#### 🪟 On Windows (PowerShell / Command Prompt)
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
pip install -e .
```

---

## 🎯 How to Run the Tool

After activating your environment, you can run commands using **either** `proxyshield` or the short alias **`pxs`**:

```bash
# 1. Launch main interactive menu & banner:
pxs
# (or: proxyshield)

# 2. View global help and all options:
pxs -h

# 3. Check version:
pxs -v
```

---

## 🌐 How to Use with Target URLs (Step-by-Step)

### 1. Auditing an Authorized Target URL
To audit an authorized web server or API strictly through public proxies without exposing your real IP:

```bash
# Basic target audit (tests through 10 verified proxies):
pxs a -t "https://example.com"

# Audit with custom request delay and report name:
pxs a -t "https://example.com" -n 15 -d 1.5 -r my_security_audit
```

**What Happens During the Audit:**
1. **Direct-IP Guard:** ProxyShield automatically checks your real public IP first.
2. **Zero Direct Fallback:** If any proxy fails, the request is aborted immediately; it will **never** fall back to your direct connection.
3. **Leak Detection:** If an exit IP matches your real IP, ProxyShield blocks the request instantly.
4. **Response Categorization:** Classifies HTTP `200`, `403` (WAF block), `429` (rate limit), `5xx` (server error), or timeout.
5. **Generates 3 Reports:**
   * `my_security_audit.html` (interactive web dashboard)
   * `my_security_audit.json` (machine telemetry)
   * `my_security_audit.csv` (spreadsheet / SIEM log)

#### How to Open and View the Generated HTML Report:
* **On Windows:**
  ```powershell
  start my_security_audit.html
  ```
* **On macOS:**
  ```bash
  open my_security_audit.html
  ```
* **On Linux:**
  ```bash
  xdg-open my_security_audit.html
  ```

---

### 2. Using Free Proxy URLs with Other Tools (curl, browsers, Python)

You can grab live, working proxy URLs directly from ProxyShield to use with `curl` or external tools:

```bash
# 1. Get an instant fast working proxy URL:
pxs p r
# Output: socks5://120.220.197.198:59999

# 2. Use the proxy URL with curl to test IP masking:
curl -x $(pxs p r) https://api.ipify.org
# Output: 120.220.197.198 (Your real IP is protected!)

# 3. Export working proxy URLs to a text file:
pxs p f -s geonode --protocol socks5 -n 30 -o proxies.txt
```

---

## ⚡ Command Short-Form (`pxs`) & Quick Aliases

You can run commands using **either** `proxyshield` or the quick alias **`pxs`**:

| Full Command | Short Alias (`pxs`) | Description |
| :--- | :--- | :--- |
| `proxyshield -h` | `pxs -h` | Display global help and quick command overview |
| `proxyshield -v` | `pxs -v` | Display version and author metadata |
| `proxyshield proxy` | `pxs p` | Query and display live free proxies |
| `proxyshield proxy fetch` | `pxs p f` | Filter & fetch proxies (`--protocol`, `--country`) |
| `proxyshield proxy check` | `pxs p c` | Concurrent live connectivity and latency check |
| `proxyshield proxy random`| `pxs p r` | Get a single instant working proxy |
| `proxyshield audit` | `pxs a` | Run strict-proxy security audit (`-t <URL>`) |
| `proxyshield banner` | `pxs b` | Generate CFonts typography banner (`-t`, `-f`, `-g`) |
| `proxyshield config` | `pxs c` | Configuration management (`show`, `validate`, `edit`) |

> [!TIP]
> Add `-h` or `--help` after any command or alias for contextual usage and options (e.g. `pxs p -h`, `pxs a -h`, `pxs b -h`).

---

## 📖 How to Use ProxyShield

### 1. Launch Interactive Startup Screen

Run `proxyshield` or `pxs` without arguments:

```bash
pxs
# Or:
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

### 4. Strict-Proxy Security Auditing & Firewall Diagnostics

Conduct low-rate, defensive audits against **authorized targets only** strictly through verified public proxy endpoints. Automatic direct fallback is disabled to prevent accidental direct IP exposure:

```bash
# Audit an authorized target across 10 verified proxies
proxyshield audit --target "https://example.com" --limit 10

# Customize request delay (rate-limit safety) and export reports
proxyshield audit --target "https://example.com" --delay 1.5 --report my_security_audit
```

This generates three synchronized reports:
* `my_security_audit.html` (interactive executive dashboard)
* `my_security_audit.json` (machine-readable metrics & telemetry)
* `my_security_audit.csv` (tabular log for SIEM or spreadsheet analysis)

---

### 5. Configuration Management

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

