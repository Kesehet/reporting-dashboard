from report_modules.condition_utils import All_CHARTS as CHART_NAMES


# export_charts_env.py
# pip install requests pandas openpyxl python-dotenv

import os
import json
import logging
from io import StringIO
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union, Optional

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import quote
from dotenv import load_dotenv

# =========================
# CONFIG (edit as needed)
# =========================

load_dotenv('../.env')  # reads .env from current working dir

# Static paths / names
OUTPUT_DIR = Path("exports")                      # static folder
FILENAME   = f"charts_{datetime.now():%Y%m%d_%H%M%S}.xlsx"  # static pattern

# Server settings from .env with safe defaults
BASE_URL     = os.getenv("BASE_URL", "http://localhost:5000")
ROUTE_PREFIX = os.getenv("ROUTE_PREFIX", "/charts")
TRACKING_CODE = os.getenv("ECA_TRACKING_CODE", "%")  # e.g. "%"

# Dynamic time window (override via .env if you want)
# START_DATE defaults to Jan 1 of current year; END_DATE to today
START_DATE = os.getenv("START_DATE") or f"2023-01-01"
END_DATE   = os.getenv("END_DATE")   or f"{date.today():%Y-%m-%d}"

# Optional: a JSON file path in .env to load chart names from; otherwise use ssthe list below
CHARTS_FILE = os.getenv("CHARTS_FILE")  # e.g. ./charts.json


# =========================
# Networking / Excel utils
# =========================

def make_session(total_retries: int = 3, backoff: float = 0.5, timeout: int = 600) -> Tuple[requests.Session, Tuple[int, int]]:
    session = requests.Session()
    retry = Retry(
        total=total_retries,
        read=total_retries,
        connect=total_retries,
        backoff_factor=backoff,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session, (timeout, timeout)

def to_dataframe(payload: Any) -> pd.DataFrame:
    if isinstance(payload, list):
        if not payload:
            return pd.DataFrame()
        if isinstance(payload[0], dict):
            return pd.DataFrame(payload)
        if isinstance(payload[0], (list, tuple)):
            header_like = all(isinstance(h, str) for h in payload[0])
            if header_like:
                return pd.DataFrame(payload[1:], columns=list(payload[0]))
            max_len = max(len(r) for r in payload if isinstance(r, (list, tuple)))
            cols = [f"col_{i+1}" for i in range(max_len)]
            norm = [list(r) + [None]*(max_len - len(r)) for r in payload]
            return pd.DataFrame(norm, columns=cols)

    if isinstance(payload, dict):
        if "data" in payload:
            data = payload["data"]
            cols = payload.get("columns")
            if isinstance(data, list) and isinstance(cols, list):
                return pd.DataFrame(data, columns=cols)
            return to_dataframe(data)
        if "rows" in payload:
            rows = payload["rows"]
            cols = payload.get("columns")
            if isinstance(cols, list):
                return pd.DataFrame(rows, columns=cols)
            return to_dataframe(rows)
        # flat dict
        if all(not isinstance(v, (list, dict)) for v in payload.values()):
            return pd.DataFrame([payload])

    if isinstance(payload, str) and ("," in payload or "\t" in payload or "\n" in payload):
        try:
            return pd.read_csv(StringIO(payload))
        except Exception:
            pass

    return pd.DataFrame({"value": [payload]})

FORBIDDEN = set(':\\/?*[]')
def safe_sheet_name(name: str, existing: set) -> str:
    n = "".join("_" if c in FORBIDDEN else c for c in (name or "Sheet")).strip() or "Sheet"
    n = n[:31]
    base = n
    i = 1
    while n in existing:
        n = base[:31 - len(f"_{i}")] + f"_{i}"
        i += 1
    existing.add(n)
    return n

def fetch_and_export(
    base_url: str,
    chart_names: List[str],
    start_date: str,
    end_date: str,
    tracking_code: str,
    out_path: Path,
    route_prefix: str = "/charts",
) -> Path:
    session, timeout_tuple = make_session()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    sheets: List[Tuple[str, pd.DataFrame]] = []
    for name in chart_names:
        if "Table" not in name:
            continue
        encoded = quote(name, safe="")
        url = f"{base_url.rstrip('/')}{route_prefix}/{encoded}"
        params = dict(start_date=start_date, end_date=end_date, eCATrackingCode=tracking_code, authorization=False)

        try:
            logging.info("GET %s", url)
            r = session.get(url, params=params, timeout=timeout_tuple)
            if r.status_code != 200:
                df = pd.DataFrame({"error": [f"HTTP {r.status_code}"], "source_url": [r.url]})
            else:
                try:
                    payload = r.json()
                except ValueError:
                    payload = r.text
                df = to_dataframe(payload)
            sheets.append((name, df))
        except requests.RequestException as ex:
            sheets.append((name, pd.DataFrame({"error": [str(ex)]})))

    used = set()
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        for sheet_name, df in sheets:
            df.to_excel(writer, index=False, sheet_name=safe_sheet_name(sheet_name, used))
    return out_path

# =========================
# Run
# =========================

def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


    out_path = OUTPUT_DIR / FILENAME
    path = fetch_and_export(
        base_url=BASE_URL,
        chart_names=CHART_NAMES,
        start_date=START_DATE,
        end_date=END_DATE,
        tracking_code=TRACKING_CODE,
        out_path=out_path,
        route_prefix=ROUTE_PREFIX,
    )
    print(f"Saved: {path}")

if __name__ == "__main__":
    main()
