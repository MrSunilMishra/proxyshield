"""
ProxyShield Local Web Server & Dashboard
Provides a local HTTP dashboard to view generated security audit reports,
telemetry, and proxy status in your browser.

Author: Quarkova
Website: https://quarkova.com
License: MIT
"""

import os
import sys
import json
import glob
import time
import socket
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional, Tuple, Dict, Any, List

from proxyshield import __version__, __author__, __organization__, __website__
from proxyshield.color_engine import colorize_text

# Global server instance tracker
_SERVER_THREAD: Optional[threading.Thread] = None
_SERVER_INSTANCE: Optional[ThreadingHTTPServer] = None
_ACTIVE_PORT: Optional[int] = None


def find_available_port(start_port: int = 8080, max_attempts: int = 20) -> int:
    """Finds an open TCP port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start_port


def check_local_dns_status() -> Dict[str, Any]:
    """Checks whether proxyshield.test is configured in the OS hosts file."""
    hosts_path = (
        r"C:\Windows\System32\drivers\etc\hosts"
        if sys.platform == "win32"
        else "/etc/hosts"
    )
    configured = False
    if os.path.exists(hosts_path):
        try:
            with open(hosts_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    stripped = line.strip()
                    if not stripped.startswith("#") and "proxyshield.test" in stripped:
                        configured = True
                        break
        except Exception:
            pass

    return {
        "hosts_path": hosts_path,
        "configured": configured,
        "win_cmd": 'Add-Content -Path "C:\\Windows\\System32\\drivers\\etc\\hosts" -Value "127.0.0.1 proxyshield.test"',
        "nix_cmd": 'echo "127.0.0.1 proxyshield.test" | sudo tee -a /etc/hosts'
    }


def generate_dashboard_html(reports: List[Dict[str, Any]], port: int) -> str:
    """Generates the modern local dashboard HTML page."""
    report_rows = ""
    if not reports:
        report_rows = """
        <tr>
          <td colspan="5" style="text-align: center; padding: 30px; color: #94a3b8;">
            No audit reports generated yet. Run <code>audit &lt;target-url&gt;</code> in ProxyShield to generate your first report.
          </td>
        </tr>
        """
    else:
        for r in reports:
            fmt_badge = f'<span class="badge badge-{r["format"].lower()}">{r["format"].upper()}</span>'
            view_btn = f'<a href="/{r["name"]}" target="_blank" class="btn btn-sm btn-primary">Open Report ↗</a>'
            report_rows += f"""
            <tr>
              <td style="font-weight: 600; color: #f1f5f9;">{r["name"]}</td>
              <td>{fmt_badge}</td>
              <td style="color: #94a3b8;">{r["size_kb"]:.1f} KB</td>
              <td style="color: #94a3b8;">{r["modified"]}</td>
              <td>{view_btn}</td>
            </tr>
            """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ProxyShield Local Dashboard | Reports & Diagnostics</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #090d16;
      --card-bg: #0f172a;
      --border: #1e293b;
      --primary: #38bdf8;
      --accent: #facc15;
      --success: #10b981;
      --text: #f1f5f9;
      --muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: 'Inter', sans-serif;
      line-height: 1.6;
      padding: 30px 20px;
    }}
    .container {{
      max-width: 1100px;
      margin: 0 auto;
    }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 25px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 30px;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .brand-title {{
      font-size: 24px;
      font-weight: 800;
      color: var(--primary);
      letter-spacing: -0.5px;
    }}
    .brand-badge {{
      background: rgba(56, 189, 248, 0.1);
      border: 1px solid rgba(56, 189, 248, 0.3);
      color: var(--primary);
      font-size: 11px;
      padding: 3px 8px;
      border-radius: 999px;
      font-weight: 600;
    }}
    .author-tag {{
      color: var(--muted);
      font-size: 13px;
    }}
    .author-tag a {{
      color: var(--primary);
      text-decoration: none;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 20px;
      margin-bottom: 30px;
    }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 24px;
    }}
    .card-title {{
      font-size: 16px;
      font-weight: 700;
      color: var(--primary);
      margin-bottom: 12px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .stat-number {{
      font-size: 32px;
      font-weight: 800;
      color: #fff;
      font-family: 'Fira Code', monospace;
    }}
    .stat-desc {{
      font-size: 13px;
      color: var(--muted);
      margin-top: 4px;
    }}
    .domain-tip {{
      background: rgba(250, 204, 21, 0.08);
      border: 1px solid rgba(250, 204, 21, 0.3);
      border-radius: 8px;
      padding: 16px 20px;
      margin-bottom: 30px;
      font-size: 14px;
      color: #fef08a;
    }}
    .domain-tip code {{
      background: #1e293b;
      color: #38bdf8;
      padding: 2px 6px;
      border-radius: 4px;
      font-family: 'Fira Code', monospace;
      font-size: 13px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 15px;
    }}
    th, td {{
      padding: 12px 16px;
      text-align: left;
      border-bottom: 1px solid var(--border);
      font-size: 14px;
    }}
    th {{
      color: var(--muted);
      font-weight: 600;
      text-transform: uppercase;
      font-size: 11px;
      letter-spacing: 0.5px;
    }}
    .badge {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 700;
      font-family: 'Fira Code', monospace;
    }}
    .badge-html {{ background: rgba(56, 189, 248, 0.15); color: #38bdf8; }}
    .badge-json {{ background: rgba(250, 204, 21, 0.15); color: #facc15; }}
    .badge-csv {{ background: rgba(16, 185, 129, 0.15); color: #10b981; }}
    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: var(--primary);
      color: #090d16;
      font-weight: 600;
      padding: 6px 14px;
      border-radius: 6px;
      text-decoration: none;
      font-size: 13px;
      transition: opacity 0.2s;
    }}
    .btn:hover {{ opacity: 0.9; }}
    .btn-sm {{ padding: 4px 10px; font-size: 12px; }}
    footer {{
      margin-top: 50px;
      text-align: center;
      font-size: 13px;
      color: var(--muted);
      border-top: 1px solid var(--border);
      padding-top: 20px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="brand">
        <span class="brand-title">ProxyShield</span>
        <span class="brand-badge">Local Web Dashboard</span>
      </div>
      <div class="author-tag">
        Developed by <a href="{__website__}" target="_blank"><strong>{__author__}</strong></a> | Version {__version__}
      </div>
    </header>

    <!-- Local Domain Customization Tip -->
    <div class="domain-tip">
      <strong>💡 Custom Local Domain Tip:</strong> You can access this dashboard via <code>http://proxyshield.test:{port}</code>!<br>
      To enable it, simply add <code>127.0.0.1 proxyshield.test</code> to your system <code>hosts</code> file (Windows: <code>C:\\Windows\\System32\\drivers\\etc\\hosts</code> | Linux/macOS: <code>/etc/hosts</code>).
    </div>

    <!-- Quick Stats Grid -->
    <div class="grid">
      <div class="card">
        <div class="card-title">📊 Total Audit Reports</div>
        <div class="stat-number">{len(reports)}</div>
        <div class="stat-desc">Available HTML, JSON, and CSV reports on local disk</div>
      </div>
      <div class="card">
        <div class="card-title">🛡️ Direct-IP Guard Policy</div>
        <div class="stat-number" style="color: #10b981; font-size: 24px; padding-top: 8px;">ACTIVE</div>
        <div class="stat-desc">Zero direct fallback strictly enforced on all audit runs</div>
      </div>
      <div class="card">
        <div class="card-title">🌐 Local Webserver Address</div>
        <div class="stat-number" style="color: #38bdf8; font-size: 20px; padding-top: 10px;">http://127.0.0.1:{port}</div>
        <div class="stat-desc">Or <code>http://proxyshield.test:{port}</code> with hosts file entry</div>
      </div>
    </div>

    <!-- Reports Table Card -->
    <div class="card">
      <div class="card-title">📁 Generated Audit Transparency Reports</div>
      <table>
        <thead>
          <tr>
            <th>Report File</th>
            <th>Format</th>
            <th>Size</th>
            <th>Generated Timestamp</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {report_rows}
        </tbody>
      </table>
    </div>

    <footer>
      ProxyShield v{__version__} &bull; Author: <a href="{__website__}" style="color: var(--primary);">{__author__}</a> &bull; MIT License &bull; Learn. Test. Secure.
    </footer>
  </div>
</body>
</html>
"""


class ProxyShieldDashboardHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler serving dashboard and audit reports."""

    def do_GET(self):
        # Clean path
        clean_path = self.path.split("?")[0]

        if clean_path in ("/", "/dashboard", "/index.html", "/reports"):
            # Discover reports in working directory
            reports = []
            files = sorted(
                glob.glob("*.html") + glob.glob("*.json") + glob.glob("*.csv"),
                key=os.path.getmtime,
                reverse=True
            )
            for f in files:
                # Do not list the documentation website index.html as an audit report
                if f.lower() == "index.html":
                    continue
                ext = f.split(".")[-1].upper()
                stat = os.stat(f)
                reports.append({
                    "name": f,
                    "format": ext,
                    "size_kb": stat.st_size / 1024.0,
                    "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime))
                })

            port = self.server.server_address[1]
            content = generate_dashboard_html(reports, port).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        elif clean_path == "/api/status":
            files = sorted(glob.glob("*.html") + glob.glob("*.json") + glob.glob("*.csv"), key=os.path.getmtime, reverse=True)
            data = {
                "tool": "ProxyShield",
                "version": __version__,
                "author": __author__,
                "organization": __organization__,
                "website": __website__,
                "reports_count": len([f for f in files if f.lower() != "index.html"]),
                "server_port": self.server.server_address[1]
            }
            body = json.dumps(data, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # Otherwise serve file from current working directory
        return super().do_GET()

    def log_message(self, format, *args):
        """Suppress default HTTP access logs to keep terminal quiet."""
        pass


def start_report_server(
    port: int = 8080,
    open_browser: bool = True,
    background: bool = False
) -> Tuple[str, int]:
    """
    Launches the local ProxyShield report web server.
    Returns (server_url, bound_port).
    """
    global _SERVER_THREAD, _SERVER_INSTANCE, _ACTIVE_PORT

    actual_port = find_available_port(port)
    server_addr = ("0.0.0.0", actual_port)

    try:
        httpd = ThreadingHTTPServer(server_addr, ProxyShieldDashboardHandler)
    except Exception as e:
        # Fallback to 127.0.0.1 binding
        httpd = ThreadingHTTPServer(("127.0.0.1", actual_port), ProxyShieldDashboardHandler)

    _SERVER_INSTANCE = httpd
    _ACTIVE_PORT = actual_port
    local_url = f"http://127.0.0.1:{actual_port}"
    domain_url = f"http://proxyshield.test:{actual_port}"

    if background:
        _SERVER_THREAD = threading.Thread(target=httpd.serve_forever, daemon=True)
        _SERVER_THREAD.start()
    else:
        # In foreground: open browser and serve
        if open_browser:
            webbrowser.open(local_url)
        print(colorize_text(f"\n[ProxyShield Web Server] Running at: {local_url}", "bright_green", bold=True))
        print(colorize_text(f"  • Custom Domain: {domain_url} (requires hosts file entry)", "bright_cyan"))
        print(colorize_text("  • Serving audit reports (*.html, *.json, *.csv) and dashboard", "white"))
        print(colorize_text("Press Ctrl+C to stop the server.\n", "bright_yellow"))
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print(colorize_text("\n[ProxyShield] Web server stopped.", "bright_yellow"))
            httpd.server_close()

    return local_url, actual_port
