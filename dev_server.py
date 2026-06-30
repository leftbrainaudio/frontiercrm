"""Simple dev server: serves frontend dist + proxies /api to Django backend."""
import http.server
import urllib.request
import os
import sys

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
BACKEND_URL = "http://localhost:8000"

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/") or self.path.startswith("/@vite/"):
            # Proxy to Django backend
            url = BACKEND_URL + self.path
            if self.path.startswith("/@vite/"):
                url = "http://localhost:5173" + self.path
            try:
                resp = urllib.request.urlopen(url, timeout=10)
                self.send_response(resp.status)
                for key, val in resp.headers.items():
                    if key.lower() not in ("transfer-encoding", "content-encoding", "connection"):
                        self.send_header(key, val)
                self.end_headers()
                self.wfile.write(resp.read())
            except Exception as e:
                self.send_error(502, f"Proxy error: {e}")
            return
        # Serve static files, fallback to index.html for SPA
        path = self.translate_path(self.path)
        if not os.path.exists(path):
            path = os.path.join(FRONTEND_DIR, "index.html")
        super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length else b""
            req = urllib.request.Request(
                BACKEND_URL + self.path,
                data=body,
                headers={k: v for k, v in self.headers.items() if k.lower() not in ("host", "transfer-encoding")},
                method="POST",
            )
            try:
                resp = urllib.request.urlopen(req, timeout=30)
                self.send_response(resp.status)
                for key, val in resp.headers.items():
                    if key.lower() not in ("transfer-encoding", "content-encoding", "connection"):
                        self.send_header(key, val)
                self.end_headers()
                self.wfile.write(resp.read())
            except Exception as e:
                self.send_error(502, f"Proxy error: {e}")
            return
        self.send_error(405)

if __name__ == "__main__":
    os.chdir(FRONTEND_DIR)
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5173
    server = http.server.HTTPServer(("0.0.0.0", port), ProxyHandler)
    print(f"Serving frontend + proxying /api → {BACKEND_URL}")
    print(f"→ http://localhost:{port}/")
    server.serve_forever()