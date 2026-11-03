from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import argparse
import json

PUBLIC = Path(__file__).resolve().parent / "public"
BACKEND = "https://two026-it4200-fall.onrender.com"

def upstream_url(path):
    if not path.startswith("/api/"):
        raise ValueError("Expected /api/ prefix")
    return BACKEND + path[len("/api"):]

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC), **kwargs)

    def do_GET(self):
        if self.path.startswith("/api/"):
            self.proxy()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            self.proxy()
        else:
            self.send_error(404)

    def proxy(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > 1_000_000:
                self.send_error(413)
                return
            body = self.rfile.read(length) if length else None
            request = Request(upstream_url(self.path), data=body, method=self.command,
                              headers={"Content-Type": self.headers.get("Content-Type", "application/json")})
            try:
                response = urlopen(request, timeout=90)
            except HTTPError as error:
                response = error
            with response:
                payload = response.read()
                self.send_response(response.code)
                self.send_header("Content-Type", response.headers.get("Content-Type", "application/json"))
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(payload)
        except (URLError, TimeoutError, OSError):
            self.send_json_error(502, "Could not reach Render. It may be waking up; try again.")
        except ValueError:
            self.send_json_error(400, "Invalid request path or content length.")

    def send_json_error(self, status, message):
        payload = json.dumps({"error": message}).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    print(f"Arcade preview: http://127.0.0.1:{args.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
