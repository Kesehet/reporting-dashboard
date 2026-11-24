"""Local, aggregate dashboard usage history. Never persist credentials or raw payloads."""
from contextlib import closing, contextmanager
from datetime import date
from pathlib import Path
import sqlite3
import sys
import time
from threading import Lock
from urllib.parse import urlencode, quote

from flask import Blueprint, current_app, g, jsonify, request
from authentication import verify_token, unauthorized

DAY = 86400
RETENTION = 7 * DAY
CHARTS = frozenset(["Abandonment Report","Abandonment Report by Month Pie","Abandonment Report by Types of Abandonment Pie","Abandonment Report by Week Bar","Abandonment Report by Year Pie","All Bot Deduped Data Monthly Insights","All Branch Ids","All Filters Table","All Transactions","Application Volume By Product (All Opened Or Approved Apps) Line","Application Volume By Product (All Opened Or Approved Apps) Line Table","Application Volume By Product (All Opened Or Approved Apps) Pie - Year to Date","Application Volume By Product (All Opened Or Approved Apps) Pie Table - Year to Date","Application Volume By Product (All Started Apps) Line","Application Volume By Product (All Started Apps) Line Table","Application Volume By Product (All Started Apps) Pie - Year to Date","Application Volume By Product (All Started Apps) Pie Table - Year to Date","Application Volume By Product (All Submitted Apps) Line","Application Volume By Product (All Submitted Apps) Line Table","Application Volume By Product (All Submitted Apps) Pie - Year to Date","Application Volume By Product (All Submitted Apps) Pie Table - Year to Date","Application Volume By Product Quarterly (All Opened Or Approved Apps) Line","Application Volume By Product Quarterly (All Opened Or Approved Apps) Pie","Application Volume By Product Quarterly (All Opened Or Approved Apps) Table","Application Volume By Product Quarterly (All Started Apps) Line","Application Volume By Product Quarterly (All Started Apps) Pie","Application Volume By Product Quarterly (All Started Apps) Table","Application Volume By Product Quarterly (All Submitted Apps) Line","Application Volume By Product Quarterly (All Submitted Apps) Pie","Application Volume By Product Quarterly (All Submitted Apps) Table","Application Volume by Product Current Quarter (All Approved Apps) Pie","Application Volume by Product Current Quarter (All Approved Apps) Table","Application Volume by Product Current Quarter (All Started Apps) Pie","Application Volume by Product Current Quarter (All Started Apps) Table","Application Volume by Product Current Quarter (All Submitted Apps) Pie","Application Volume by Product Current Quarter (All Submitted Apps) Table","Bot Generated Reports Insights","Bot Generated Reports Monthly Insights","Branch Originated Reports","Branch Originated Reports Monthly Analytics Line","Business Account Summary Current Balance and Initial Deposit Table","Business Account Summary Number Of Apps Table","Business Account Summary Top 10 Branches Table","Business Account Summary Top 10 Products Table","Business Deposit Reports","Business Deposit Reports Monthly Analytics Line","Common App In Branch and Consumer Facing Report","Cross Sell Products Presented and Accepted Line","Cross Sell Products Presented and Accepted Table","Cross Sell Products Table","Current Total DDS Amount and Switches Insights","Custom Quarterly Analytics Common App Table","Custom Quarterly Analytics Customer eCA Table","Custom Quarterly Analytics InBranch Common App Table","Declined Report Line","Declined Report Table","Direct Deposit Switch Reports Insights","Direct Deposit Switch Reports Table","Document Center Insigths","Document Center Monthly Insigths","Document Center Monthly Insigths Line","E Delivery Report LOB Table","E-Delivery Report Insights","Funding Type Report","Funding Type Report Line","Lending And Deposit Reports","Loan Commitment Bar And Line","Loan Commitment Insights","Loan Commitment Stacked Bar","Loan Commitment Stacked Table","Monthly BPM and CRIF Report","Monthly Business Deposits And Loans Report","Monthly Consumer Facing Report","Monthly In Branch Report","Monthly In Branch vs BPM and CRIF Report","Monthly Multi Product Reports Line","Monthly Opening And Current Balance Table","Multi Products Cross Sell Bar","Multi Products Cross Sell Table","Multi Products Daily Product Set Id Insights","Multi Products Product Set Id Bar","Multi Products Product Set Id Table","New vs Exisitng Customers","New vs Existing Customers Table","Payment Switch Insights","PennState Branch Report Insights","PennState Student Banking Reports Insights","PennState Student Banking Reports Line","Shot Clock Application Reports Insights","Spot And Current Balance Account Insights","Spot And Current Balance Account Stacked Chart","Spot And Current Balance Account Table","Student Checking Monthly Report Table","Student Checking Report Insights","Top 10 Single product with Cross Sell Products Bar","Top 10 Single product with Cross Sell Products Table","Transaction Logger","Transaction Logger Recent Txns","Type Of Decline Reasons Bar","Type Of Decline Reasons Table","Zero Product Applications Bar","Zero Product Applications Table"])
TABS = frozenset(["Abandonment Report","All Filters Table","All Transactions","BOR","Bot Generated Reports","Business Accounts Summary","Business Deposit Reports","CSV Loader Reports","Cross Sell Reports","Customer Document Center","Declined Report","Direct Deposit Switch","E Delivery Report LOB","E-Delivery Report","Funding Type Report","Graphs","Key Rotation","Lending & Deposit Control Report","Loan Commitments","Manual Review Report","Monthly Report","Multi Product Reports","New vs Exisitng Customers","OPPIQ Report","Payment Switch Reports","PennState University Banking Reports","Post Processing","Spot And Current Balance Amounts","Student Checking Report","Transaction Logger"])
# Only exact, non-customer filter values may be replayed by a future warmer.
# Unknown filters make the entire request ineligible, rather than changing its meaning.
SAFE_VALUES = {
    "application_type": {"All", "Consumer", "Business", "Common App", "In Branch"},
    "eCATrackingCode": {"%25", "%", "All", "Consumer", "Business"},
    "monthlyReportProductTypeSelector": {"All"},
    "showComma": {"true", "false"},
    "return_format": {"json"},
    "send_avg": {"true", "false"},
    "send_sec_unsec": {"true", "false"},
    "send_total": {"true", "false"},
    "show_line": {"true", "false"},
    "sideByside": {"true", "false"},
    "variant": {"Started", "Submitted", "Opened/Approved"},
    "type": {"all", "submitted", "opened/approved"},
    "BranchID": {"All"},
}
DATE_FIELDS = {"start_date", "end_date", "start_date_for_left_graph",
               "end_date_for_left_graph", "start_date_for_right_graph",
               "end_date_for_right_graph"}
NON_REPLAY = {"All Transactions", "All Filters Table", "Transaction Logger",
              "Transaction Logger Recent Txns", "All Branch Ids"}
usage_api = Blueprint("usage_analytics", __name__, url_prefix="/usage-report")


def database_path():
    # Match existing server runtime-directory convention, not the EXE extraction directory.
    return Path(current_app.config.get("USAGE_ANALYTICS_DB", Path.cwd() / "usage-analytics.sqlite3"))


def replay_url(chart, params):
    if chart not in CHARTS or chart in NON_REPLAY or not isinstance(params, dict):
        return None
    if not {"start_date", "end_date"}.issubset(params):
        return None
    clean = {}
    for key, value in params.items():
        if not isinstance(value, str):
            return None
        if key in DATE_FIELDS:
            try:
                if date.fromisoformat(value).isoformat() != value:
                    return None
            except ValueError:
                return None
        elif value not in SAFE_VALUES.get(key, ()):
            return None
        clean[key] = value
    return "/charts/" + quote(chart, safe="") + "?" + urlencode(sorted(clean.items()))


class UsageStore:
    def __init__(self, path):
        self.path = Path(path)
        self._ready = False
        self._lock = Lock()
        self._last_prune = 0

    @contextmanager
    def connection(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path, timeout=0.15)) as db, db:
            db.row_factory = sqlite3.Row
            if not self._ready or not self.path.exists():
                with self._lock:
                    db.execute("PRAGMA journal_mode=WAL")
                    db.executescript("""
                        CREATE TABLE IF NOT EXISTS usage_events (
                            id INTEGER PRIMARY KEY, at REAL NOT NULL,
                            kind TEXT NOT NULL, name TEXT NOT NULL,
                            method TEXT NOT NULL, status INTEGER NOT NULL,
                            duration_ms REAL NOT NULL, source TEXT NOT NULL,
                            cache_state TEXT NOT NULL, replay_url TEXT
                        );
                        CREATE INDEX IF NOT EXISTS usage_events_at ON usage_events(at);
                    """)
                    self._ready = True
            yield db

    def record(self, kind, name, method="", status=200, duration_ms=0,
               source="dashboard", cache_state="", url=None, now=None):
        now = time.time() if now is None else now
        with self.connection() as db:
            db.execute(
                """INSERT INTO usage_events
                   (at,kind,name,method,status,duration_ms,source,cache_state,replay_url)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (now, kind, name, method, status, duration_ms, source, cache_state, url),
            )
            if now - self._last_prune >= 3600:
                db.execute("DELETE FROM usage_events WHERE at < ?", (now - RETENTION,))
                self._last_prune = now

    def summary(self, now=None):
        now = time.time() if now is None else now
        where = "at >= ? AND at <= ? AND source != 'cache-generator'"
        args = (now - DAY, now)
        with self.connection() as db:
            rows = db.execute(
                f"""SELECT kind,name,method,COUNT(*) AS count,
                    ROUND(AVG(duration_ms),1) AS avg_ms, ROUND(MAX(duration_ms),1) AS max_ms,
                    SUM(CASE WHEN status >= 400 THEN 1 ELSE 0 END) AS errors,
                    SUM(CASE WHEN cache_state IN ('hit','wait_hit') THEN 1 ELSE 0 END) AS cache_hits,
                    SUM(CASE WHEN cache_state = 'miss' THEN 1 ELSE 0 END) AS cache_misses
                    FROM usage_events WHERE {where}
                    GROUP BY kind,name,method ORDER BY count DESC,name,method""", args
            ).fetchall()
            series = db.execute(
                f"""SELECT CAST(at / 3600 AS INTEGER)*3600 AS hour,kind,COUNT(*) AS count
                    FROM usage_events WHERE {where} GROUP BY hour,kind ORDER BY hour""", args
            ).fetchall()
            warm = db.execute(
                "SELECT COUNT(*) FROM usage_events WHERE at >= ? AND at <= ? AND source='cache-generator' AND kind='api'",
                args,
            ).fetchone()[0]
        result = {kind: [dict(row) for row in rows if row["kind"] == kind]
                  for kind in ("api", "chart", "tab")}
        result["hourly"] = [dict(row) for row in series]
        result["cache_warm_requests"] = warm
        return result

    def ranked_cache_urls(self, now=None, limit=100):
        """Future cache generator input: exact safe GET workloads, ranked by real demand."""
        now = time.time() if now is None else now
        with self.connection() as db:
            rows = db.execute(
                """SELECT replay_url AS url,COUNT(*) AS count,MAX(at) AS last_used
                   FROM usage_events WHERE at >= ? AND at <= ? AND kind='chart'
                   AND source='dashboard' AND status BETWEEN 200 AND 299
                   AND replay_url IS NOT NULL GROUP BY replay_url
                   ORDER BY count DESC,last_used DESC,url LIMIT ?""",
                (now-DAY, now, max(1, min(int(limit), 1000))),
            ).fetchall()
        return [dict(row) for row in rows]


def store():
    path = database_path()
    instance = current_app.extensions.get("usage_analytics_store")
    if instance is None or instance.path != path:
        instance = UsageStore(path)
        current_app.extensions["usage_analytics_store"] = instance
    return instance


def safe_record(*args, **kwargs):
    try:
        store().record(*args, **kwargs)
    except Exception as exc:
        # Telemetry failure must never change an existing API response.
        current_app.logger.warning("Usage recording unavailable: %s", type(exc).__name__)


@usage_api.before_request
def require_session():
    if not verify_token(request.headers.get("X-MSAL-ID-Token") or request.headers.get("Authorization")):
        return unauthorized()


@usage_api.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@usage_api.post("/tab")
def tab_visit():
    payload = request.get_json(silent=True)
    name = payload.get("tab") if isinstance(payload, dict) else None
    if not isinstance(name, str) or name not in TABS:
        return jsonify({"error": "Unknown report"}), 400
    safe_record("tab", name)
    return "", 204


@usage_api.get("")
def usage_summary():
    try:
        return jsonify(store().summary())
    except (OSError, sqlite3.Error):
        return jsonify({"error": "Report unavailable"}), 503


def install_usage_analytics(app):
    app.register_blueprint(usage_api)

    @app.before_request
    def start_usage_timer():
        g.usage_started = time.perf_counter()

    @app.after_request
    def record_usage(response):
        rule = request.url_rule
        if (rule is None or request.blueprint == "usage_analytics"
                or request.method in ("OPTIONS", "HEAD") or rule.endpoint == "static"):
            return response
        duration = round((time.perf_counter() - g.usage_started) * 1000, 2)
        identity = getattr(g, "usage_identity", None)
        source = "dashboard"
        if identity == "api_key":
            source = ("cache-generator" if request.headers.get("X-Usage-Source") == "cache-generator"
                      else "api-client")
        safe_record("api", rule.rule, request.method, response.status_code, duration, source)
        if rule.rule == "/charts/<name>" and identity:
            chart = (request.view_args or {}).get("name")
            name = chart if chart in CHARTS else "Unknown chart"
            url = None
            if (source == "dashboard" and request.method == "GET"
                    and response.status_code == 200
                    and all(len(request.args.getlist(key)) == 1 for key in request.args)):
                url = replay_url(chart, request.args.to_dict())
            safe_record("chart", name, request.method, response.status_code, duration,
                        source, getattr(g, "usage_cache", ""), url)
        return response
