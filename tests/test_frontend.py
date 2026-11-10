import io
import json
from pathlib import Path
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
        with urlopen(self.base + "/api-routes.json") as response:
            self.assertEqual(response.status, 200)
            catalog = json.load(response)
        html = (ROOT / "public/index.html").read_text(encoding="utf-8")
        self.assertNotIn("{{", html)
        self.assertIn('<script src="./arcade.js" defer="">', html)
        self.assertNotIn("api-routes", html)
        self.assertIn("/roulette-payout", [route["path"] for route in catalog])
        self.assertIn({"path": "/add-score", "methods": ["POST"]}, catalog)

    def test_arcade_includes_cross_road_and_rocket_ride(self):
        html = (ROOT / "public/index.html").read_text(encoding="utf-8")
        script = (ROOT / "public/arcade.js").read_text(encoding="utf-8")
        self.assertIn('<form data-game="crossRoad">', html)
        self.assertIn('<form data-game="rocketRide">', html)
        self.assertIn('name="cash_out" type="number" min="0" max="100"', html)
        self.assertIn('data-cross-road-action="jump"', html)
        self.assertIn('data-cross-road-action="cashout"', html)
        self.assertIn('action, bet: new FormData(form).get("bet")', script)
        self.assertIn('{ action, round_id: roundId }', script)
        self.assertIn('controls.querySelector(\'[data-cross-road-action="cashout"]\').disabled = false', script)
        self.assertIn('rocketRide: `/rocketRide?${new URLSearchParams(fields)}`', script)

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

    def test_pieces_game_integration(self):
        """Verify the Pieces game is connected to the class API."""
        html = (ROOT / "public" / "index.html").read_text(encoding="utf-8")
        javascript = (ROOT / "public" / "arcade.js").read_text(encoding="utf-8")

        self.assertIn('id="pieces-game"', html)
        self.assertIn('data-game="pieces"', html)
        self.assertIn('pieces: "/pieces"', javascript)
        self.assertIn('if (game === "pieces")', javascript)
        self.assertIn("data.matching_pieces", javascript)
        self.assertIn("data.payout", javascript)
        self.assertIn("data.profit", javascript)
