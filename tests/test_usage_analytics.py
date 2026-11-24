import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api-server"))
from flask import Flask, g
from usage_analytics import DAY, UsageStore, install_usage_analytics, replay_url


class UsageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "new" / "usage-analytics.sqlite3"
        self.store = UsageStore(self.path)

    def test_window_ranking_restart_and_privacy(self):
        now = time.time()
        chart = "Monthly In Branch Report"
        url = replay_url(chart, {"start_date": "2026-11-01", "end_date": "2026-11-24"})
        self.assertTrue(url)
        self.assertIsNone(replay_url(chart, {"start_date": "2026-11-01",
            "end_date": "2026-11-24", "api_key": "secret"}))
        for source, at in [("dashboard", now-1), ("dashboard", now-2),
                           ("dashboard", now-DAY-1), ("cache-generator", now-3)]:
            self.store.record("chart", chart, "GET", 200, 42, source, "hit", url, at)
        other = UsageStore(self.path)
        self.assertEqual(other.summary(now)["chart"][0]["count"], 2)
        self.assertEqual(other.ranked_cache_urls(now)[0]["count"], 2)
        self.assertEqual(other.ranked_cache_urls(now)[0]["url"], url)

    def test_http_routes_and_fail_open(self):
        app = Flask(__name__)
        app.config["USAGE_ANALYTICS_DB"] = self.path
        install_usage_analytics(app)

        @app.get("/charts/<name>")
        def chart(name):
            g.usage_identity = "session"
            g.usage_cache = "miss"
            return {"ok": True}

        client = app.test_client()
        url = "/charts/Monthly%20In%20Branch%20Report?start_date=2026-11-01&end_date=2026-11-24"
        self.assertEqual(client.get(url).status_code, 200)
        self.assertEqual(client.get("/usage-report").status_code, 401)
        with patch("usage_analytics.verify_token", return_value={"role": "session"}):
            self.assertEqual(client.post("/usage-report/tab", json={"tab": "Monthly Report"}).status_code, 204)
            data = client.get("/usage-report").get_json()
            self.assertEqual(data["chart"][0]["cache_misses"], 1)
            self.assertEqual(data["api"][0]["name"], "/charts/<name>")
            self.assertEqual(data["tab"][0]["count"], 1)
        with patch("usage_analytics.UsageStore.record", side_effect=OSError):
            self.assertEqual(client.get(url).status_code, 200)


if __name__ == "__main__":
    unittest.main()
