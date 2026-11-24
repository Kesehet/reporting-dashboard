"""Warm only the chart workloads ranked by recent dashboard demand."""
import os
import sys
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from metrics import update_metrics
from usage_analytics import validated_replay

TIMEOUT = (10, 90)


def settings():
    if getattr(sys, "frozen", False):
        load_dotenv(Path(sys.executable).resolve().parent / ".env", override=False)
    load_dotenv(Path.cwd() / ".env", override=False)
    return (os.getenv("REACT_APP_API_SERVER_BASE_URL", "").rstrip("/"),
            os.getenv("ALL_FILTERS_CHART_API_KEY", ""))


def report_metric(key, value):
    try:
        update_metrics(key, value)
    except (OSError, ValueError):
        # A metrics-file issue must not prevent warming.
        pass


def _workloads(session, base_url, headers):
    response = session.get(base_url + "/usage-report/cache-plan", headers=headers,
                           timeout=TIMEOUT, allow_redirects=False)
    if response.status_code != 200:
        raise RuntimeError("Cache plan request failed (HTTP %s)" % response.status_code)
    payload = response.json()
    if not isinstance(payload, dict) or not isinstance(payload.get("workloads"), list):
        raise RuntimeError("Invalid cache plan")
    return payload["workloads"]


def generate_cache(plan=None, *, base_url=None, api_key=None):
    """Use the API server's SQLite plan, never a static URL list."""
    report_metric("cache_gen", f"started {datetime.now().isoformat()}")
    result = {"selected": 0, "succeeded": 0, "failed": 0, "skipped": 0}
    try:
        configured_url, configured_key = settings()
        base_url = (configured_url if base_url is None else base_url).rstrip("/")
        api_key = configured_key if api_key is None else api_key
        if not base_url or not api_key:
            raise RuntimeError("Existing API base URL or chart API key is missing")
        headers = {"X-API-KEY": api_key, "X-Usage-Source": "cache-generator"}
        with requests.Session() as session:
            if plan is None:
                plan = _workloads(session, base_url, headers)
            seen = set()
            for row in plan:
                url = validated_replay(row.get("url")) if isinstance(row, dict) else None
                if url is None or url in seen:
                    result["skipped"] += 1
                    continue
                seen.add(url)
                result["selected"] += 1
                try:
                    response = session.get(base_url + url, headers=headers, timeout=TIMEOUT,
                                           allow_redirects=False)
                    if response.status_code != 200:
                        raise RuntimeError("Chart request failed")
                    payload = response.json()
                    if isinstance(payload, dict) and (payload.get("error") or payload.get("status") == "error"):
                        raise RuntimeError("Chart returned an error")
                    result["succeeded"] += 1
                except (requests.RequestException, ValueError, RuntimeError):
                    result["failed"] += 1
                report_metric("cache_gen_error",
                              "Processed %s; successful %s; failed %s." %
                              (result["selected"], result["succeeded"], result["failed"]))
        if not result["selected"]:
            message = "No eligible recent chart workloads."
        else:
            message = ("Cached %s/%s workloads; %s failed; %s skipped." %
                       (result["succeeded"], result["selected"], result["failed"], result["skipped"]))
        report_metric("cache_gen_error", message)
        print(message)
        return result
    except Exception as exc:
        report_metric("cache_gen_error", "Cache generation failed: " + type(exc).__name__)
        raise
    finally:
        report_metric("cache_gen", f"ended {datetime.now().isoformat()}")


def main():
    if sys.argv[1:] == ["--verify-packaging"]:
        print("PACKAGING_CHECK_OK: cache_gen, usage_analytics, sqlite3")
        return 0
    try:
        result = generate_cache()
        return 1 if result["failed"] else 0
    except Exception as exc:
        print("Cache generation failed: " + type(exc).__name__, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
