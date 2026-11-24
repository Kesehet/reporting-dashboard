import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api-server"))
from flask import Flask
import cache_gen
from usage_analytics import UsageStore, install_usage_analytics, replay_url, validated_replay

CHART = "Monthly In Branch Report"


def url(start="2026-11-01", end="2026-11-24", **params):
    return replay_url(CHART, {"start_date": start, "end_date": end, **params})


class CachePlanTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "usage-analytics.sqlite3"
        self.store = UsageStore(self.path)
        self.now = datetime(2026, 11, 24, 10, tzinfo=timezone.utc).timestamp()

    def add(self, target, count=1, **kwargs):
        for _ in range(count):
            self.store.record("chart", CHART, kwargs.get("method", "GET"),
                              kwargs.get("status", 200), source=kwargs.get("source", "dashboard"),
                              url=target, now=kwargs.get("at", self.now-1))

    def test_rank_and_exclude(self):
        high = url(application_type="Online")
        low = url(application_type="All")
        once = url(application_type="Banker Assisted")
        self.add(low, 2)
        self.add(high, 5)
        self.add(once)
        self.add(low, 30, source="cache-generator")
        self.add(low, 30, status=500)
        self.add(low, 30, method="POST")
        self.add(low, 30, at=self.now-86401)
        self.add("https://evil.invalid/charts/anything", 100)
        plan = self.store.cache_plan(self.now)
        self.assertEqual([(x["url"], x["count"]) for x in plan], [(high, 5), (low, 2)])
        self.assertEqual(len(self.store.cache_plan(self.now, limit=1)), 1)

    def test_roll_only_default_dates(self):
        observed = datetime.fromtimestamp(self.now, timezone.utc)-timedelta(days=1)
        end = observed.date()
        start = end-timedelta(days=90)
        old = url(start.isoformat(), end.isoformat())
        fixed = url("2026-01-01", "2026-03-31")
        self.add(old, 3, at=observed.timestamp()+3600)
        self.add(fixed, 2, at=observed.timestamp()+3600)
        plan = self.store.cache_plan(self.now)
        self.assertEqual(plan[0]["url"], url((end-timedelta(days=89)).isoformat(), (end+timedelta(days=1)).isoformat()))
        self.assertEqual(plan[1]["url"], fixed)

    def test_replay_validation(self):
        self.assertIsNone(validated_replay(url() + "&api_key=secret"))
        self.assertIsNone(validated_replay(url() + "&start_date=2026-11-01"))
        self.assertIsNone(validated_replay("//evil.invalid/charts/test"))
        self.assertIsNone(validated_replay(url("2026-12-01", "2026-11-24")))
        self.assertEqual(validated_replay(url()), url())

    def test_plan_api_key_only_and_no_store(self):
        app = Flask(__name__)
        app.config["USAGE_ANALYTICS_DB"] = self.path
        install_usage_analytics(app)
        client = app.test_client()
        with patch.dict(os.environ, {"ALL_FILTERS_CHART_API_KEY": "test-key"}):
            self.assertEqual(client.get("/usage-report/cache-plan").status_code, 401)
            self.assertEqual(client.get("/usage-report/cache-plan", headers={"X-MSAL-ID-Token": "fake"}).status_code, 401)
            result = client.get("/usage-report/cache-plan", headers={"X-API-KEY": "test-key"})
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json, {"workloads": []})
            self.assertEqual(result.headers["Cache-Control"], "no-store")


class GeneratorTests(unittest.TestCase):
    def setUp(self):
        self.session = Mock()
        self.session.__enter__ = Mock(return_value=self.session)
        self.session.__exit__ = Mock(return_value=False)
        self.patch = patch("cache_gen.requests.Session", return_value=self.session)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        metric = patch("cache_gen.update_metrics")
        metric.start()
        self.addCleanup(metric.stop)
        self.base = "https://dashboard.invalid/api"

    @staticmethod
    def response(status=200, payload=None):
        result = Mock(status_code=status)
        result.json.return_value = {} if payload is None else payload
        return result

    def test_ranked_order_headers_failure_and_no_static_list(self):
        high, low = url(application_type="Online"), url(application_type="All")
        self.session.get.side_effect = [
            self.response(payload={"workloads": [{"url": high, "count": 5}, {"url": low, "count": 2}]}),
            self.response(), self.response(500),
        ]
        result = cache_gen.generate_cache(base_url=self.base, api_key="test-key")
        self.assertEqual(result, {"selected": 2, "succeeded": 1, "failed": 1, "skipped": 0})
        self.assertEqual([c.args[0] for c in self.session.get.call_args_list],
                         [self.base+"/usage-report/cache-plan", self.base+high, self.base+low])
        for call in self.session.get.call_args_list:
            self.assertEqual(call.kwargs["headers"], {"X-API-KEY": "test-key", "X-Usage-Source": "cache-generator"})
            self.assertFalse(call.kwargs["allow_redirects"])

    def test_empty_and_unsafe_plan(self):
        result = cache_gen.generate_cache(plan=[], base_url=self.base, api_key="test-key")
        self.assertEqual(result["selected"], 0)
        self.session.get.assert_not_called()
        result = cache_gen.generate_cache(plan=[{"url": "https://evil.invalid/"}], base_url=self.base, api_key="test-key")
        self.assertEqual(result["skipped"], 1)
        self.session.get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
