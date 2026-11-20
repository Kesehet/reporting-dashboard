import csv
import logging
import os
import sys
import tempfile
import time
from datetime import date, datetime
from decimal import Decimal
from io import StringIO
from pathlib import Path
from threading import Thread

from flask import Blueprint, Response, current_app, jsonify, request, stream_with_context

from authentication import request_identity, unauthorized
from DB import SQLConn


oppiq_api = Blueprint("oppiq_api", __name__)
logger = logging.getLogger(__name__)
CSV_FILENAME = "OPPIQ_Report.csv"

HEADERS = [
    "Banker_Name",
    "Lead_Assigned_By",
    "Customer_Name",
    "BRANCHID",
    "CLIENTID",
    "LEADID",
    "PRODUCT_NAME",
    "Lead_Assigned_On",
    "Lead_Status",
]

PREFIX = """
;WITH LatestLeadStatus AS
(
    SELECT
        ls.LEADID,
        ls.TOSTATUSID,
        ls.LASTUPDATEDATE,
        ROW_NUMBER() OVER
        (
            PARTITION BY ls.LEADID
            ORDER BY ls.LASTUPDATEDATE DESC,
                     ls.LEADSTATUSID DESC
        ) AS RN
    FROM OppDeux.dbo.LEAD_STATUS ls
)
"""

FIELDS = """
    b.FULLNAME AS Banker_Name,
    f.FULLNAME AS Lead_Assigned_By,
    e.FULLNAME AS Customer_Name,
    l.BRANCHID,
    e.CLIENTID,
    l.LEADID,
    d.PRODUCT_NAME,
    a.LASTUPDATEDATE AS Lead_Assigned_On,
    CASE
        WHEN a.LEADID IS NULL THEN 'UnAssigned'
        ELSE x.STATUSLABEL
    END AS Lead_Status
"""

SOURCE = """
FROM OppDeux.dbo.LEAD l
LEFT JOIN OppDeux.dbo.LEAD_ASSIGNMENT a
    ON l.LEADID = a.LEADID
   AND a.ACTIVEFLAG = 1
LEFT JOIN OppDeux.dbo.APPLUSER b
    ON a.ASSIGNEDTOUSERID = b.USERID
LEFT JOIN OppDeux.dbo.APPLUSER f
    ON a.ASSIGNEDBYUSERID = f.USERID
LEFT JOIN OppDeux.dbo.PRODUCT_CATALOG d
    ON l.PRODUCTID = d.PRODUCT_ID
LEFT JOIN OppDeux.dbo.CLIENT e
    ON l.CLIENTID = e.CLIENTID
LEFT JOIN LatestLeadStatus lls
    ON l.LEADID = lls.LEADID
   AND lls.RN = 1
LEFT JOIN OppDeux.dbo.LEAD_STATUS_CODE_XREF x
    ON lls.TOSTATUSID = x.STATUSID
WHERE l.PRIORITYSCORE > 399
"""

ORDERING = """
ORDER BY
    COALESCE(b.FULLNAME, 'UnAssigned'),
    l.LASTUPDATEDATE DESC,
    l.LEADID
"""

PAGED_QUERY = PREFIX + "SELECT\n    COUNT(*) OVER() AS Report_Total,\n" + FIELDS.strip() + "\n" + SOURCE + ORDERING + "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
EXPORT_QUERY = PREFIX + "SELECT\n" + FIELDS.strip() + "\n" + SOURCE + ORDERING


def _cell(value):
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def _csv_cell(value):
    value = _cell(value)
    if value is None:
        return ""
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def _connect():
    sql = SQLConn(kind="OPPIQ")
    sql.connect()
    if sql.connection is None:
        raise ConnectionError("OPPIQ SQL Server connection unavailable")
    return sql


def get_oppiq_csv_path():
    """Persist in the repository root (beside the application for packaged builds)."""
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).resolve().parent
        if base.name.lower() == "api-server":
            base = base.parent
    else:
        base = Path(__file__).resolve().parents[2]
    return base / "OPPIQ Report" / CSV_FILENAME


def save_oppiq_csv(destination=None):
    """Replace the daily CSV atomically, keeping the previous file on errors."""
    path = Path(destination) if destination is not None else get_oppiq_csv_path()
    sql = None
    cursor = None
    temporary_path = None
    row_count = 0
    try:
        sql = _connect()
        cursor = sql.connection.cursor()
        cursor.execute(EXPORT_QUERY)
        path.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8-sig",
            newline="",
            dir=path.parent,
            prefix=".oppiq_",
            suffix=".tmp",
            delete=False,
        ) as output:
            temporary_path = Path(output.name)
            writer = csv.writer(output)
            writer.writerow(HEADERS)
            while True:
                batch = cursor.fetchmany(1000)
                if not batch:
                    break
                for record in batch:
                    writer.writerow([_csv_cell(value) for value in record])
                    row_count += 1
            output.flush()
            os.fsync(output.fileno())

        os.replace(temporary_path, path)
        temporary_path = None
        return path, row_count
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                logger.warning("Could not remove temporary OPPIQ CSV: %s", temporary_path)
        if cursor is not None:
            cursor.close()
        if sql is not None:
            sql.disconnect()


def start_daily_oppiq_csv_export():
    """Export immediately on startup, then once per calendar day while running."""
    def refresh_loop():
        last_successful_day = None
        while True:
            today = date.today()
            if today != last_successful_day:
                try:
                    path, count = save_oppiq_csv()
                    last_successful_day = date.today()
                    logger.info("OPPIQ CSV refreshed: %s (%d rows)", path, count)
                except Exception:
                    logger.exception("OPPIQ CSV refresh failed; previous CSV retained")
            # Check for a new day; retry failures without restarting the server.
            time.sleep(300)

    worker = Thread(target=refresh_loop, name="oppiq-csv-refresh", daemon=True)
    worker.start()
    return worker


@oppiq_api.route("/oppiq-report", methods=["GET"])
def oppiq_report():
    if request_identity() is None:
        return unauthorized()

    try:
        page = int(request.args.get("page", "1"))
        page_size = int(request.args.get("page_size", "50"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid pagination parameters."}), 400

    if page < 1 or page_size not in (25, 50, 100) or page > 1000000:
        return jsonify({"error": "Invalid pagination parameters."}), 400

    sql = None
    cursor = None
    try:
        sql = _connect()
        cursor = sql.connection.cursor()
        cursor.execute(PAGED_QUERY, (page - 1) * page_size, page_size)
        result = cursor.fetchall()
        rows = [[_cell(value) for value in row[1:]] for row in result]
        total = int(result[0][0]) if result else 0
        return jsonify({
            "headers": HEADERS,
            "rows": rows,
            "total": total,
            "page": page,
            "page_size": page_size,
        })
    except ConnectionError:
        current_app.logger.exception("OPPIQ report database unavailable")
        return jsonify({"error": "OPPIQ database is unavailable."}), 503
    except Exception:
        current_app.logger.exception("OPPIQ report query failed")
        return jsonify({"error": "Unable to load OPPIQ report."}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if sql is not None:
            sql.disconnect()


@oppiq_api.route("/oppiq-report/export", methods=["GET"])
def oppiq_report_export():
    if request_identity() is None:
        return unauthorized()

    sql = None
    cursor = None
    try:
        sql = _connect()
        cursor = sql.connection.cursor()
        cursor.execute(EXPORT_QUERY)
    except ConnectionError:
        if sql is not None:
            sql.disconnect()
        current_app.logger.exception("OPPIQ export database unavailable")
        return jsonify({"error": "OPPIQ database is unavailable."}), 503
    except Exception:
        if cursor is not None:
            cursor.close()
        if sql is not None:
            sql.disconnect()
        current_app.logger.exception("OPPIQ export query failed")
        return jsonify({"error": "Unable to export OPPIQ report."}), 500

    def generate():
        output = StringIO()
        writer = csv.writer(output)
        try:
            yield "\ufeff"
            writer.writerow(HEADERS)
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)
            while True:
                batch = cursor.fetchmany(1000)
                if not batch:
                    break
                for record in batch:
                    writer.writerow([_csv_cell(value) for value in record])
                    yield output.getvalue()
                    output.seek(0)
                    output.truncate(0)
        finally:
            cursor.close()
            sql.disconnect()

    filename = "OPPIQ_Report_" + datetime.now().strftime("%Y-%m-%d") + ".csv"
    return Response(
        stream_with_context(generate()),
        content_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )
