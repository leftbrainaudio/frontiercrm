#!/usr/bin/env python3
"""FrontierCRM Wiki Viewer — local HTTP server rendering markdown as HTML."""

import http.server
import os
import subprocess
import urllib.parse
from pathlib import Path

WIKI_ROOT = os.path.expanduser("~/wiki/frontiercrm")
PORT = 8899

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FrontierCRM Wiki — {title}</title>
<style>
  :root {{
    --bg: #0B1120;
    --surface: #121A2E;
    --border: #1E293B;
    --text: #E2E8F0;
    --text-dim: #94A3B8;
    --primary: #3B82F6;
    --accent: #14B8A6;
    --warm: #F59E0B;
    --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', monospace;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: var(--font);
    line-height: 1.7;
    font-size: 15px;
  }}
  .layout {{
    display: flex;
    min-height: 100vh;
  }}
  .sidebar {{
    width: 280px;
    flex-shrink: 0;
    background: var(--surface);
    border-right: 1px solid var(--border);
    padding: 24px 16px;
    overflow-y: auto;
    position: sticky;
    top: 0;
    height: 100vh;
  }}
  .sidebar h2 {{
    font-size: 14px;
    font-weight: 600;
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 16px;
  }}
  .sidebar a {{
    display: block;
    padding: 4px 8px;
    color: var(--text-dim);
    text-decoration: none;
    font-size: 13px;
    border-radius: 4px;
    margin: 1px 0;
    transition: all 0.15s;
  }}
  .sidebar a:hover, .sidebar a.active {{
    color: var(--text);
    background: rgba(59, 130, 246, 0.1);
  }}
  .sidebar a.active {{
    color: var(--primary);
    font-weight: 500;
  }}
  .sidebar .section {{
    font-size: 11px;
    font-weight: 600;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-top: 16px;
    margin-bottom: 6px;
    padding: 0 8px;
  }}
  .main {{
    flex: 1;
    padding: 40px 48px;
    max-width: 960px;
  }}
  .main a {{
    color: var(--accent);
    text-decoration: none;
  }}
  .main a:hover {{ text-decoration: underline; }}
  .main h1 {{
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 8px;
    color: var(--text);
    border-bottom: 1px solid var(--border);
    padding-bottom: 12px;
  }}
  .main h2 {{ font-size: 22px; font-weight: 600; margin-top: 32px; margin-bottom: 12px; color: var(--primary); }}
  .main h3 {{ font-size: 18px; font-weight: 600; margin-top: 24px; margin-bottom: 8px; color: var(--accent); }}
  .main h4 {{ font-size: 16px; font-weight: 600; margin-top: 20px; margin-bottom: 6px; }}
  .main p {{ margin: 12px 0; }}
  .main ul, .main ol {{ margin: 8px 0; padding-left: 24px; }}
  .main li {{ margin: 4px 0; }}
  .main code {{
    font-family: var(--mono);
    background: rgba(59, 130, 246, 0.08);
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 13px;
    color: #93C5FD;
  }}
  .main pre {{
    background: #0F172A;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 16px;
    overflow-x: auto;
    margin: 16px 0;
  }}
  .main pre code {{
    background: none;
    padding: 0;
    color: var(--text);
    font-size: 13px;
    line-height: 1.5;
  }}
  .main blockquote {{
    border-left: 3px solid var(--primary);
    padding: 8px 16px;
    margin: 16px 0;
    background: rgba(59, 130, 246, 0.05);
    border-radius: 0 6px 6px 0;
    color: var(--text-dim);
  }}
  .main table {{
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    font-size: 13px;
  }}
  .main th, .main td {{
    padding: 8px 12px;
    border: 1px solid var(--border);
    text-align: left;
  }}
  .main th {{
    background: var(--surface);
    font-weight: 600;
    color: var(--accent);
  }}
  .main tr:nth-child(even) {{ background: rgba(18, 26, 46, 0.5); }}
  .main hr {{ border: none; border-top: 1px solid var(--border); margin: 24px 0; }}
  .main img {{ max-width: 100%; border-radius: 6px; border: 1px solid var(--border); }}
  .main strong {{ color: #F8FAFC; }}
  .header-bar {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border);
  }}
  .header-bar .logo {{
    font-weight: 700;
    font-size: 18px;
    color: var(--primary);
  }}
  .header-bar .tagline {{
    color: var(--text-dim);
    font-size: 13px;
  }}
  .header-bar .nav {{
    margin-left: auto;
    display: flex;
    gap: 8px;
  }}
  .header-bar .nav a {{
    font-size: 12px;
    color: var(--text-dim);
    padding: 4px 10px;
    border: 1px solid var(--border);
    border-radius: 4px;
    text-decoration: none;
  }}
  .header-bar .nav a:hover {{
    background: var(--surface);
    color: var(--text);
  }}
  @media (max-width: 768px) {{
    .layout {{ flex-direction: column; }}
    .sidebar {{ width: 100%; height: auto; position: static; }}
    .main {{ padding: 24px; }}
  }}
</style>
</head>
<body>
<div class="layout">
  <nav class="sidebar">
    <h2>📖 FrontierCRM</h2>
    {sidebar_links}
  </nav>
  <div class="main">
    <div class="header-bar">
      <span class="logo">◈ FrontierCRM</span>
      <span class="tagline">Project Wiki</span>
      <span class="nav">
        <a href="/">🏠 Index</a>
        <a href="https://github.com" target="_blank" style="border:none;padding:4px 0;">⬡</a>
      </span>
    </div>
    {content}
  </div>
</div>
</body>
</html>"""

INDEX_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FrontierCRM Wiki</title>
<style>
  :root {{
    --bg: #0B1120;
    --surface: #121A2E;
    --border: #1E293B;
    --text: #E2E8F0;
    --text-dim: #94A3B8;
    --primary: #3B82F6;
    --accent: #14B8A6;
    --warm: #F59E0B;
    --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: var(--font);
    line-height: 1.6;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
  }}
  .container {{
    max-width: 800px;
    padding: 48px 32px;
    text-align: center;
  }}
  .logo {{
    width: 64px;
    height: 64px;
    background: linear-gradient(135deg, var(--primary), var(--accent));
    border-radius: 16px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    margin-bottom: 24px;
  }}
  h1 {{ font-size: 32px; font-weight: 700; margin-bottom: 8px; }}
  .tagline {{ color: var(--text-dim); font-size: 16px; margin-bottom: 40px; }}
  .docs {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    text-align: left;
  }}
  .doc-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
    text-decoration: none;
    color: var(--text);
    transition: all 0.2s;
  }}
  .doc-card:hover {{
    border-color: var(--primary);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
  }}
  .doc-card .title {{ font-weight: 600; font-size: 14px; margin-bottom: 4px; }}
  .doc-card .desc {{ color: var(--text-dim); font-size: 12px; }}
  .doc-card .badge {{
    display: inline-block;
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 99px;
    background: rgba(20, 184, 166, 0.1);
    color: var(--accent);
    margin-top: 6px;
  }}
  .subdirs {{
    margin-top: 32px;
    text-align: left;
  }}
  .subdirs h3 {{ font-size: 14px; color: var(--text-dim); margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px; }}
  .subdir-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }}
  .subdir-link {{
    display: block;
    padding: 10px 14px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    text-decoration: none;
    color: var(--accent);
    font-size: 13px;
  }}
  .subdir-link:hover {{
    border-color: var(--primary);
  }}
  @media (max-width: 600px) {{
    .docs {{ grid-template-columns: 1fr; }}
    .subdir-grid {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>
<div class="container">
  <div class="logo">
    <img src="assets/brand/frontiercrm-icon-mark.png" alt="FrontierCRM" style="width:64px;height:64px;border-radius:16px;">
  </div>
  <img src="assets/brand/frontiercrm-logo-full.png" alt="FrontierCRM" style="height:36px;margin-bottom:8px;">
  <p class="tagline">Your sales. Your way. — Project Knowledge Base</p>
  <div class="docs">
    {cards}
  </div>
  <div class="subdirs">
    <h3>Subdirectories</h3>
    <div class="subdir-grid">
      {subdir_links}
    </div>
  </div>
</div>
</body>
</html>"""

DOCS_META = [
    ("00_INDEX.md", "Master Index", "Full link graph and doc map", "index"),
    ("01_MARKET_RESEARCH.md", "Market Research", "10 competitors, $101.4B market", "phase-1"),
    ("02_FEATURE_MATRIX.md", "Feature Matrix", "40+ features mapped", "phase-1"),
    ("03_PERSONAS.md", "User Personas", "8 personas consolidated", "phase-2"),
    ("04_INTEGRATIONS.md", "Integrations", "28 third-party providers", "phase-1"),
    ("04B_EMERGING_TECH.md", "Emerging Tech", "14 innovation opportunities", "phase-1"),
    ("05_TECH_STACK.md", "Tech Stack", "Django/DRF/React/Postgres + 11 ADRs", "phase-2"),
    ("06_DATA_ARCHITECTURE.md", "Data Architecture", "Models, API design, sync", "phase-2"),
    ("07_UX_WORKFLOWS.md", "UX Workflows", "Full workflow specifications", "phase-2"),
    ("08_BRAND_GUIDELINES.md", "Brand Guidelines", "Colors, typography, tone, voice", "phase-3"),
    ("09_PRICING.md", "Pricing Strategy", "Tiers, profit analysis", "phase-3"),
    ("10_ROADMAP.md", "Roadmap", "Release plan and milestones", "phase-3"),
    ("11_DECISION_LOG.md", "Decision Log (ADRs)", "11 architectural decisions", "meta"),
    ("api-endpoints.md", "API Endpoints", "Full API reference", "dev"),
    ("competitive-analysis.md", "Competitive Analysis", "Deep competitive research", "phase-1"),
    ("integration-specs.md", "Integration Specs", "Detailed integration specs", "phase-1"),
    ("integration-specs-social-analytics.md", "Social Analytics Spec", "Social integration details", "phase-1"),
    ("salesforce_research_report.md", "Salesforce Report", "Deep Salesforce analysis", "phase-1"),
    ("sync-architecture-adr.md", "Sync Architecture ADR", "Offline sync design decisions", "phase-2"),
    ("screen-mockups.md", "Screen Mockups", "10 key screens visualized", "phase-3"),
    ("ui-design-system.md", "UI Design System", "17 components specced", "phase-3"),
]

SIDEBAR_SECTIONS = [
    ("Overview", ["00_INDEX.md"]),
    ("📊 Research", ["competitive-analysis.md", "01_MARKET_RESEARCH.md", "salesforce_research_report.md"]),
    ("🔧 Features", ["02_FEATURE_MATRIX.md", "04_INTEGRATIONS.md", "04B_EMERGING_TECH.md", "integration-specs.md", "integration-specs-social-analytics.md"]),
    ("👥 Personas & UX", ["03_PERSONAS.md", "07_UX_WORKFLOWS.md"]),
    ("🏗️ Architecture", ["05_TECH_STACK.md", "06_DATA_ARCHITECTURE.md", "api-endpoints.md", "sync-architecture-adr.md"]),
    ("🎨 Design", ["08_BRAND_GUIDELINES.md", "ui-design-system.md", "screen-mockups.md"]),
    ("💼 Business", ["09_PRICING.md", "10_ROADMAP.md"]),
    ("📝 Meta", ["11_DECISION_LOG.md"]),
]


def get_readable_name(filename):
    for f, name, _, _ in DOCS_META:
        if f == filename:
            return name
    return filename.replace(".md", "").replace("_", " ").replace("-", " ").title()


def build_sidebar(current):
    links = ""
    for section, files in SIDEBAR_SECTIONS:
        links += f'<div class="section">{section}</div>\n'
        for f in files:
            cls = 'active' if f == current else ''
            name = get_readable_name(f)
            links += f'<a href="/{f}" class="{cls}">{name}</a>\n'
    return links


def build_index():
    cards = ""
    for filename, title, desc, _ in DOCS_META:
        cards += f'<a href="/{filename}" class="doc-card">'
        cards += f'<div class="title">{title}</div>'
        cards += f'<div class="desc">{desc}</div>'
        cards += f'<span class="badge">{filename}</span>'
        cards += '</a>\n'

    subdirs_html = ""
    for d in sorted(os.listdir(WIKI_ROOT)):
        dp = os.path.join(WIKI_ROOT, d)
        if os.path.isdir(d) and not d.startswith('.'):
            subdirs_html += f'<a href="/dir/{d}" class="subdir-link">📁 {d}/</a>\n'

    return INDEX_PAGE.format(cards=cards, subdir_links=subdirs_html)


def render_markdown(filepath):
    try:
        result = subprocess.run(
            ["pandoc", "-f", "markdown", "-t", "html", "--wrap=preserve", str(filepath)],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout if result.returncode == 0 else f"<pre>Error rendering markdown: {result.stderr}</pre>"
    except Exception as e:
        return f"<pre>Error: {e}</pre>"


class WikiHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.lstrip("/")

        # Index page
        if path == "" or path == "index.html" or path == "00_INDEX.md":
            html = build_index()
            self._send_html(html)
            return

        # Subdirectory listing
        if path.startswith("dir/"):
            subdir = path[4:]
            subdir_path = os.path.join(WIKI_ROOT, subdir)
            if os.path.isdir(subdir_path):
                files = sorted(os.listdir(subdir_path))
                cards = ""
                for f in files:
                    if f.endswith(".md") and not f.startswith('.'):
                        cards += f'<a href="/{subdir}/{f}" class="doc-card"><div class="title">{get_readable_name(f)}</div><span class="badge">{f}</span></a>\n'
                html = INDEX_PAGE.format(cards=cards, subdir_links="")
                self._send_html(html)
                return

        # Handle subdirectory paths like design-system/SOME_FILE.md
        filepath = os.path.join(WIKI_ROOT, path)
        # Also try with .md if no extension
        if not os.path.exists(filepath) and not path.endswith(".md"):
            filepath_md = filepath + ".md"
            if os.path.exists(filepath_md):
                filepath = filepath_md

        if os.path.exists(filepath) and filepath.endswith(".md"):
            content = render_markdown(filepath)
            title = get_readable_name(os.path.basename(path))
            sidebar = build_sidebar(os.path.basename(path) if '/' not in path else path)
            html = HTML_TEMPLATE.format(title=title, content=content, sidebar_links=sidebar)
            self._send_html(html)
            return

        # Static files (images, etc.)
        if os.path.exists(filepath) and not filepath.endswith(".md"):
            self._serve_static(filepath)
            return

        # 404
        sidebar = build_sidebar("")
        html = HTML_TEMPLATE.format(
            title="Not Found",
            content="<h1>404 — Page Not Found</h1><p>The requested document doesn't exist in the wiki.</p>",
            sidebar_links=sidebar
        )
        self._send_html(html, status=404)

    def _send_html(self, html, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _serve_static(self, filepath):
        ext = os.path.splitext(filepath)[1].lower()
        mime = {
            ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".gif": "image/gif", ".svg": "image/svg+xml", ".webp": "image/webp",
            ".ico": "image/x-icon", ".html": "text/html", ".css": "text/css",
            ".js": "application/javascript", ".json": "application/json",
        }.get(ext, "application/octet-stream")
        try:
            with open(filepath, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Cache-Control", "max-age=3600")
            self.end_headers()
            self.wfile.write(data)
        except Exception:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        print(f"[wiki] {args[0]} {args[1]} {args[2]}")


if __name__ == "__main__":
    os.makedirs(WIKI_ROOT, exist_ok=True)
    server = http.server.HTTPServer(("127.0.0.1", PORT), WikiHandler)
    print(f"🌐 FrontierCRM Wiki Server running!")
    print(f"   → http://127.0.0.1:{PORT}")
    print(f"   → Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()