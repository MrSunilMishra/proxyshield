# ProxyShield – Technical Architecture & User Manual

Welcome to the **ProxyShield** Technical Architecture & User Manual. ProxyShield is an advanced, transparent public-proxy-based network security auditing and terminal branding engine inspired by CFonts.

---

## 1. Project Identity

* **Tool Name:** ProxyShield
* **Short Alias:** `pxs` (or `PxS`)
* **Author:** Quarkova
* **Organization:** Quarkova
* **Website:** [https://quarkova.com](https://quarkova.com)
* **License:** MIT
* **Category:** Network Security & Diagnostics
* **Repository:** [https://github.com/MrSunilMishra/proxyshield.git](https://github.com/MrSunilMishra/proxyshield.git)

> [!IMPORTANT]
> The author is strictly designated as **Quarkova**. No personal author names are used.

---

## ⚠️ Legal & Privacy Transparency Statement (Section J)

> **"ProxyShield uses publicly available third-party proxy services for educational and authorized network security auditing. The operator's direct public IP is not intentionally used for target requests in strict proxy-only mode. Public proxy operators may observe, inspect or log traffic. ProxyShield does not guarantee anonymity, privacy or proxy security. All testing must be conducted against authorized targets."**

---

## 2. Quick Automated 1-Click Setup

ProxyShield includes turnkey bootstrap scripts that automatically install `uv`, create an isolated `.venv`, install all dependencies, and launch the tool:

### 🐧 Linux, Android (Termux) & macOS:
```bash
git clone https://github.com/MrSunilMishra/proxyshield.git
cd proxyshield
chmod +x run.sh
./run.sh
```

### 🪟 Windows (CMD / PowerShell):
```powershell
git clone https://github.com/MrSunilMishra/proxyshield.git
cd proxyshield
.\run.bat
```

---

## 3. Command Syntax & Short-Form (`pxs`)

You can run commands using **either** `proxyshield` or the quick alias **`pxs`**:

| Command | Short Alias | Function |
| :--- | :--- | :--- |
| `proxyshield` | `pxs` | Launch interactive menu and CFonts startup screen |
| `proxyshield -h` | `pxs -h` | Display global help and command overview |
| `proxyshield -v` | `pxs -v` | Display version and author metadata |
| `proxyshield proxy` | `pxs p` | Multi-source free proxy aggregator (Geonode + ProxyScrape) |
| `proxyshield proxy fetch` | `pxs p f` | Query and filter proxies (`--protocol`, `--country`) |
| `proxyshield proxy check` | `pxs p c` | Test live proxy connectivity and measure roundtrip latency |
| `proxyshield proxy random` | `pxs p r` | Get a single instant working proxy URL |
| `proxyshield audit` | `pxs a` | Run strict-proxy security audit (`-t <URL>`, `-n <limit>`, `-d <delay>`) |
| `proxyshield banner` | `pxs b` | Custom CFonts typography banner (`-t`, `-f`, `-g`, `-e`) |
| `proxyshield config` | `pxs c` | Configuration management (`show`, `validate`, `edit`, `reset`, `permissions`) |

---

## 4. Typography & CFonts Engine

ProxyShield includes an advanced ASCII art typography engine backed by `pyfiglet`, `rich`, and `colorama`.

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

Over 570 backend fonts are accessible via `pxs b --list-fonts`.

### Text Effects
* **`shade`**: Progressive vertical halftone shading (`█` → `▓` → `▒`).
* **`shadow`**: Renders subtle right/bottom drop-shadow blocks (`░`).
* **`3d`**: Adds 3D extrusion borders (`▌`).
* **`outline`**: Converts solid blocks into hollow/wireframe glyphs (`□` / `◦`).
* **`none`**: Standard unmodified output.

### Color Modes & Gradients
* **Hex Codes:** e.g. `#ff5500`, `#00ffff`
* **RGB Values:** e.g. `rgb(255, 85, 0)` or `255,85,0`
* **Named Colors:** `cyan`, `yellow`, `red`, `green`, `blue`, `magenta`, `white`, `bright_red`, etc.
* **Gradients:**
  * Horizontal: Interpolated left-to-right across line width (`pxs b -g red,blue`).
  * Vertical: Interpolated top-to-bottom across ASCII height.
* **Rainbow:** 7-stage vibrant spectral cycle (`pxs b --color rainbow`).
* **Neon:** High-intensity glowing contrast with soft highlights.

---

## 5. Free Proxy Aggregator (Geonode + ProxyScrape)

ProxyShield integrates live proxy feeds from both **Geonode API** and **ProxyScrape v4 API**:
* `https://proxylist.geonode.com/api/proxy-list?page=1&limit=500&sort_by=responseTime&sort_type=asc`
* `https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=json`

### Usage Examples:
```bash
# Fetch live proxies from both providers
pxs p

# Fetch from specific provider with filters
pxs p f -s geonode --limit 20
pxs p f -s proxyscrape --protocol socks5 --country US

# Live concurrency check & latency benchmarking
pxs p c -n 15 -t 3 --alive-only -o working_proxies.txt

# Instant random working proxy URL
pxs p r --protocol socks5

# Pipe directly into curl to verify IP protection
curl -x $(pxs p r) https://api.ipify.org
```

---

## 6. Strict Direct-IP Protection & Security Auditing

Before conducting an audit against an **authorized target URL**, ProxyShield discovers the operator's real public IP as a baseline:
* **Zero Direct Fallback:** Target requests are NEVER routed directly when in proxy mode.
* **Immediate Abort on Leak:** If an observed exit IP unexpectedly matches the operator's real IP, the request is halted.
* **Detailed Diagnostics:** Classifies `SUCCESS`, `HTTP_403` (WAF block), `HTTP_429` (rate limit), `HTTP_5XX` (server error), `TCP_FAIL`, `TLS_FAIL`, `DNS_FAIL`, and `PROXY_FAIL`.

### Running an Audit:
```bash
# Basic audit across 10 verified proxies
pxs a -t "https://example.com"

# Custom rate delay and report output name
pxs a -t "https://example.com" -n 15 -d 1.5 -r my_security_audit
```

### Viewing Generated Reports:
Audits automatically produce:
1. `my_security_audit.html` (interactive dashboard)
2. `my_security_audit.json` (machine telemetry)
3. `my_security_audit.csv` (SIEM spreadsheet log)

Open in your browser:
* Windows: `start my_security_audit.html`
* macOS: `open my_security_audit.html`
* Linux: `xdg-open my_security_audit.html`

---

## 7. Configuration & File Security (`branding.txt`)

Stored at `~/.config/proxyshield/branding.txt`:
* **Directory Permission:** `chmod 700 ~/.config/proxyshield`
* **File Permission:** `chmod 600 ~/.config/proxyshield/branding.txt`
* **Prohibition of World-Writable Files:** Mode `777` is strictly forbidden.

```bash
# View configuration
pxs c s

# Validate keys, color hexes, and permissions
pxs c v

# Edit in $EDITOR
pxs c e

# Enforce 0600 file security
pxs c p --fix

# Reset to defaults
pxs c r
```

---

## 8. Automated Testing

Run the automated test suite with pytest:
```bash
pytest -v
```
Validates all 35 test cases covering direct-IP protection, proxy discovery, CFonts typography, SQLite persistence, and CLI aliases.
