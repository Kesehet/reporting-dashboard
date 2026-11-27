"""Durable JSON Workspace application snapshots in DigitalReport SQL Server.

No CSV dependency, no on-screen access required. Never delete snapshots on a
source miss or replace an earlier snapshot with an empty response.
"""
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import json

from jm_endpoints import JM_RETENTION_DAYS
from metrics import update_metrics
from report_modules.manual_review import query_jobs, WorkspaceReportError
from report_modules.transaction_timeline import (
    CODE, JOB_ATTRIBUTES, TXN_ATTRIBUTES, records, transaction_ref,
    merge_job_transactions, build_timeline,
)

ARCHIVE = "[DigitalReport].[dbo].[WorkspaceTimelineArchive]"
INDEX = "[DigitalReport].[dbo].[WorkspaceTimelineIndex]"
JOB_FIELDS = list(dict.fromkeys(JOB_ATTRIBUTES + ["timeCreated", "timeFinished", "properties", "txns.properties"]))
TXN_FIELDS = list(dict.fromkeys(TXN_ATTRIBUTES + ["properties"]))
PAGE_SIZE = 100


def ensure_archive(connection):
    cursor = connection.cursor()
    try:
        cursor.execute(f"""
            IF OBJECT_ID('{ARCHIVE}', 'U') IS NULL
            BEGIN
                CREATE TABLE {ARCHIVE} (
                    jobRefNumber NVARCHAR(128) NOT NULL,
                    snapshotHash CHAR(64) NOT NULL,
                    capturedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
                    payload NVARCHAR(MAX) NOT NULL,
                    PRIMARY KEY (jobRefNumber, snapshotHash)
                );
            END;
            IF OBJECT_ID('{INDEX}', 'U') IS NULL
            BEGIN
                CREATE TABLE {INDEX} (
                    trackingCode NVARCHAR(128) NOT NULL,
                    jobRefNumber NVARCHAR(128) NOT NULL,
                    PRIMARY KEY (trackingCode, jobRefNumber)
                );
            END;
        """)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


def valid_code(value):
    return isinstance(value, str) and CODE.fullmatch(value) is not None


def linked_ref(txn):
    props = txn.get("properties")
    ref = transaction_ref(txn) or (props.get("Link.FnbDashboardTrackingCode") if isinstance(props, dict) else None)
    return ref if valid_code(ref) else None


def save_snapshot(connection, ref, job):
    if not valid_code(ref):
        raise ValueError("Invalid archive reference")
    payload = json.dumps(job, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    aliases = {ref} | {t["trackingCode"] for t in records(job.get("txns")) if valid_code(t.get("trackingCode"))}
    cursor = connection.cursor()
    try:
        # Key-range locks make concurrent daily/manual archive runs idempotent.
        cursor.execute(f"SELECT 1 FROM {ARCHIVE} WITH (UPDLOCK,HOLDLOCK) WHERE jobRefNumber=? AND snapshotHash=?",
                       (ref, digest))
        inserted = cursor.fetchone() is None
        if inserted:
            cursor.execute(f"INSERT INTO {ARCHIVE} (jobRefNumber,snapshotHash,payload) VALUES (?,?,?)",
                           (ref, digest, payload))
        for code in sorted(aliases):
            cursor.execute(f"""
                INSERT INTO {INDEX} (trackingCode,jobRefNumber)
                SELECT ?,? WHERE NOT EXISTS (
                    SELECT 1 FROM {INDEX} WITH (UPDLOCK,HOLDLOCK)
                    WHERE trackingCode=? AND jobRefNumber=?
                )
            """, (code, ref, code, ref))
        connection.commit()
        return inserted
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


def scan_txns(workspace, start, end):
    """Page all accessible form statuses; include recently changed older forms."""
    offset = 0
    criteria = [
        f"(timeCreated >= '{start}' AND timeCreated < '{end}')",
        f"(timeUserLastModified >= '{start}' AND timeUserLastModified < '{end}')",
    ]
    while True:
        response = workspace.session.post(
            workspace.base_url.rstrip("/") + "/secure/api/v1/txn/query",
            json={"scope": "Form", "attributes": TXN_FIELDS,
                  "filters": [{"operator": "or", "criteria": criteria}],
                  "sorts": ["timeCreated asc", "trackingCode asc"],
                  "fetchLimit": PAGE_SIZE, "fetchOffset": offset},
            timeout=(10, 60), allow_redirects=False,
        )
        if response.status_code != 200:
            raise WorkspaceReportError(f"Workspace archive transaction scan failed (HTTP {response.status_code}).")
        data = response.json()
        rows = data.get("result") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            raise WorkspaceReportError("Workspace archive scan returned no result list.")
        total = data.get("totalCount")
        if not rows:
            if isinstance(total, int) and offset < total:
                raise WorkspaceReportError("Incomplete Workspace archive transaction scan.")
            return
        yield from records(rows)
        offset += len(rows)
        if isinstance(total, int) and offset >= total:
            return
        if offset >= 200000:
            raise WorkspaceReportError("Workspace archive scan exceeded its safety limit.")


def collect_day(workspace, start, end):
    """Capture jobs and standalone/updated transactions, without CSV or XML filters."""
    by_ref = defaultdict(list)
    for txn in scan_txns(workspace, start, end):
        ref = linked_ref(txn) or txn.get("trackingCode")
        if valid_code(ref):
            by_ref[ref].append(txn)
    seen = set()
    for job in query_jobs(workspace, {
        "attributes": JOB_FIELDS,
        "filters": [{"operator": "and", "criteria": [f"timeCreated >= '{start}'", f"timeCreated < '{end}'"]}],
        "sorts": ["timeCreated asc", "jobRefNumber asc"], "fetchLimit": 20,
    }, "workspace archive job scan"):
        ref = job.get("jobRefNumber")
        if not valid_code(ref) or ref in seen:
            continue
        seen.add(ref)
        job = dict(job)
        actions = [records(s.get("jobActions") or s.get("actions")) for s in records(job.get("steps"))]
        job["txns"] = merge_job_transactions(job, by_ref.pop(ref, []), actions)
        yield ref, job
    # Jobs created before this day may have new/updated transactions. Retrieve
    # their complete history rather than overwriting earlier records with a subset.
    for ref, txns in by_ref.items():
        jobs = list(query_jobs(workspace, {
            "attributes": JOB_FIELDS,
            "filters": [{"operator": "and", "criteria": [f"jobRefNumber = '{ref}'"]}],
            "fetchLimit": 10,
        }, "workspace archive related job query")) if any(linked_ref(t) for t in txns) else []
        exact = [j for j in jobs if j.get("jobRefNumber") == ref]
        if len(exact) > 1:
            raise WorkspaceReportError("Ambiguous related Workspace job.")
        if exact:
            job = dict(exact[0])
            actions = [records(s.get("jobActions") or s.get("actions")) for s in records(job.get("steps"))]
            job["txns"] = merge_job_transactions(job, txns, actions)
        else:
            job = {"jobRefNumber": ref, "txns": txns}
        yield ref, job


def archive_workspace_history(sql, txn=None, *, report_error=None):
    """Daily or manual post-processing; oldest dates first to beat source expiry."""
    from DB import WorkspaceExtract
    stats = {"started_at": datetime.now(timezone.utc).isoformat(), "scanned": 0,
             "saved": 0, "unchanged": 0, "failed": 0}
    workspace = None
    try:
        if not sql.connection:
            raise RuntimeError("Reporting database connection unavailable.")
        ensure_archive(sql.connection)
        workspace = WorkspaceExtract(setup_table=False)
        if not workspace.login():
            raise WorkspaceReportError("Workspace archive sign-in failed.")
        today = datetime.now(timezone.utc).date()
        # Seven full preceding calendar dates plus today covers the rolling
        # seven-day source window regardless of midnight/timezone boundaries.
        for delta in range(JM_RETENTION_DAYS, -1, -1):
            day = today - timedelta(days=delta)
            try:
                for ref, job in collect_day(workspace, day.isoformat(), (day + timedelta(days=1)).isoformat()):
                    stats["scanned"] += 1
                    try:
                        if save_snapshot(sql.connection, ref, job):
                            stats["saved"] += 1
                        else:
                            stats["unchanged"] += 1
                    except Exception:
                        stats["failed"] += 1
                        if report_error:
                            report_error("Could not save a Workspace archive snapshot.")
            except Exception:
                stats["failed"] += 1
                if report_error:
                    report_error("Workspace archive date scan failed; retry before source retention expires.")
        if stats["failed"] and not report_error:
            raise RuntimeError("Workspace archive did not complete successfully.")
        return stats
    except Exception:
        if not stats["failed"]:
            stats["failed"] += 1
        raise
    finally:
        if workspace is not None and workspace.session is not None:
            workspace.session.close()
        stats["finished_at"] = datetime.now(timezone.utc).isoformat()
        update_metrics("workspace_archive_summary", stats)
        print("Workspace archive: scanned={scanned} saved={saved} unchanged={unchanged} failed={failed}".format(**stats))


def read_archive(connection, code):
    """Return a merged history across retained snapshots, even after source purge."""
    cursor = connection.cursor()
    try:
        cursor.execute(f"IF OBJECT_ID('{INDEX}', 'U') IS NULL SELECT 0 ELSE SELECT 1")
        if not cursor.fetchone()[0]:
            return None
        cursor.execute(f"SELECT jobRefNumber FROM {INDEX} WHERE trackingCode=?", (code,))
        refs = [row[0] for row in cursor.fetchall()]
        if len(refs) != 1:
            return None
        ref = refs[0]
        cursor.execute(f"SELECT capturedAt,payload FROM {ARCHIVE} WHERE jobRefNumber=? ORDER BY capturedAt ASC,snapshotHash ASC",
                       (ref,))
        rows = cursor.fetchall()
        if not rows:
            return None
        job = {"jobRefNumber": ref, "txns": [], "comments": [], "steps": []}
        transactions = {}
        notes = []
        for captured, payload in rows:
            snapshot = json.loads(payload)
            if snapshot.get("status"):
                job["status"] = snapshot["status"]
            if snapshot.get("steps"):
                job["steps"] = snapshot["steps"]
            for note in records(snapshot.get("comments")):
                if note not in notes:
                    notes.append(note)
            for txn in records(snapshot.get("txns")):
                key = txn.get("trackingCode") or txn.get("submitKey")
                if not key:
                    continue
                previous = transactions.setdefault(key, {})
                combined_notes = records(previous.get("comments"))
                for note in records(txn.get("comments")):
                    if note not in combined_notes:
                        combined_notes.append(note)
                previous.update({k: v for k, v in txn.items() if v is not None and v != "" and v != []})
                previous["comments"] = combined_notes
        job["txns"] = list(transactions.values())
        job["comments"] = notes
        result = build_timeline(job)
        result["source"] = "archive"
        result["archived_at"] = rows[-1][0].isoformat() + "Z"
        return result
    finally:
        cursor.close()


def archived_history(code):
    from DB import SQLConn
    sql = SQLConn()
    try:
        sql.connect()
        if not sql.connection:
            return None
        return read_archive(sql.connection, code)
    finally:
        sql.disconnect()


def supplement_exact_search(result, tracking_codes):
    """Find archived tracking codes that are no longer returned by Journey Manager."""
    if not isinstance(result, dict) or not isinstance(result.get("headers"), list):
        return result
    headers = result["headers"]
    rows = result.get("rows", [])
    found = ({str(row[headers.index("tracking_code")]).upper()
              for row in rows if len(row) > headers.index("tracking_code")}
             if "tracking_code" in headers else set())
    archived_rows = []
    for code in dict.fromkeys(tracking_codes):
        if not valid_code(code) or code.upper() in found:
            continue
        history = archived_history(code)
        if not history:
            continue
        item = next((t for t in history["transactions"]
                     if (t.get("tracking_code") or "").upper() == code.upper()), None)
        if not item:
            continue
        archived_rows.append({
            "tracking_code": item["tracking_code"],
            "Start Date": item.get("created"),
            "Form Name": item.get("name"),
            "Form Status": item.get("status"),
            "Associated Tracking Codes": ", ".join(
                t["tracking_code"] for t in history["transactions"] if t.get("tracking_code")),
            "Source": "Archived SQL",
        })
        found.add(code.upper())
    if not archived_rows:
        return result
    if "tracking_code" not in headers:
        headers = ["isBankerAssisted", "Start Date", "Associated Tracking Codes", "Form Name",
                   "CurrentPage", "is_error", "error", "tracking_code", "submissionGroupNames", "Form Status"]
        rows = []
    new_headers = headers if "Source" in headers else headers + ["Source"]
    live_rows = [row if "Source" in headers else row + ["Live Journey Manager"] for row in rows]
    return {"headers": new_headers,
            "rows": live_rows + [[row.get(key) for key in new_headers] for row in archived_rows]}
