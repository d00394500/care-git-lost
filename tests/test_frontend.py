import io
import json
from pathlib import Path
import re
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from http.server import ThreadingHTTPServer
import dev_server

ROOT = Path(__file__).resolve().parents[1]

class FrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), dev_server.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_static_assets_and_standalone_template(self):
        for path in ("/", "/arcade.css", "/arcade.js"):
            with urlopen(self.base + path) as response:
                self.assertEqual(response.status, 200)
        html = (ROOT / "public/index.html").read_text(encoding="utf-8")
        self.assertNotIn("{{", html)
        catalog = json.loads(re.search(r'<script id="api-routes"[^>]*>(.*?)</script>', html, re.S).group(1))
        self.assertIn("/roulette-payout", [route["path"] for route in catalog])
        self.assertIn({"path": "/add-score", "methods": ["POST"]}, catalog)

    def test_fixed_upstream(self):
        self.assertEqual(dev_server.upstream_url("/api/coinflip/heads"), dev_server.BACKEND + "/coinflip/heads")
        self.assertTrue(dev_server.upstream_url("/api//evil.example/path").startswith(dev_server.BACKEND + "/"))
        with self.assertRaises(ValueError):
            dev_server.upstream_url("https://evil.example")

    def test_proxy_forwards_post_query_and_errors(self):
        error = HTTPError(dev_server.BACKEND + "/add-score", 400, "Bad Request",
                          {"Content-Type": "application/json"}, io.BytesIO(b'{"error":"test"}'))
        with patch("dev_server.urlopen", side_effect=error) as upstream:
            request = Request(self.base + "/api/add-score?test=1", data=b'{"score":3}',
                              headers={"Content-Type": "application/json"})
            with self.assertRaises(HTTPError) as caught:
                urlopen(request)
            self.assertEqual(caught.exception.code, 400)
            self.assertEqual(json.loads(caught.exception.read()), {"error": "test"})
            sent = upstream.call_args.args[0]
            self.assertEqual(sent.full_url, dev_server.BACKEND + "/add-score?test=1")
            self.assertEqual(sent.data, b'{"score":3}')
            self.assertEqual(sent.method, "POST")

    def test_hosting_proxy_matches_preview(self):
        config = (ROOT / "netlify.toml").read_text()
        self.assertIn(dev_server.BACKEND + "/:splat", config)
        self.assertIn('publish = "public"', config)
