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

TABLE = "[DigitalReport].[dbo].[WorkspaceExtract]"
LEGACY_ARCHIVE = "[DigitalReport].[dbo].[WorkspaceTimelineArchive]"
ARCHIVE_KEY = "_reportingTimelineArchive"
JOB_FIELDS = list(dict.fromkeys(JOB_ATTRIBUTES + ["timeCreated", "timeFinished", "properties", "txns.properties"]))
TXN_FIELDS = list(dict.fromkeys(TXN_ATTRIBUTES + ["properties"]))
PAGE_SIZE = 100


def ensure_archive(connection):
    """Validate the existing table only; no new tables or columns are required."""
    cursor = connection.cursor()
    try:
        cursor.execute(f"SELECT TOP 0 trackingCode,currentQueue,assignedTo,formName,timeCreated,jobRefNumber,dump FROM {TABLE}")
    finally:
        cursor.close()


def decode_dump(value):
    if value is None or value == "":
        return [], []
    data = json.loads(value) if isinstance(value, str) else value
    if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
        raise ValueError("Workspace dump is not a JSON transaction array")
    rows, snapshots = [], []
    for item in data:
        item = dict(item)
        metadata = item.pop(ARCHIVE_KEY, [])
        if not isinstance(metadata, list):
            raise ValueError("Invalid Workspace archive metadata")
        snapshots.extend(metadata)
        if item:
            rows.append(item)
    return rows, snapshots


def encode_dump(rows, snapshots):
    data = [dict(row) for row in rows]
    if snapshots:
        if not data:
            data.append({})
        data[0][ARCHIVE_KEY] = snapshots
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def merge_raw_rows(old, new):
    """Keep existing XML/properties; update returned values and accumulate notes."""
    rows = [dict(item) for item in old]
    for item in new:
        item = dict(item)
        item.pop(ARCHIVE_KEY, None)
        code = item.get("trackingCode")
        key = item.get("submitKey")
        candidates = [row for row in rows if
                      (code and row.get("trackingCode") == code) or
                      (key and row.get("submitKey") == key and
                       (not code or not row.get("trackingCode") or row["trackingCode"] == code))]
        if len(candidates) != 1:
            if item not in rows:
                rows.append(item)
            continue
        target = candidates[0]
        for field, value in item.items():
            if field == "comments":
                existing = records(target.get(field))
                target[field] = existing + [n for n in records(value) if n not in existing]
            elif isinstance(value, dict) and isinstance(target.get(field), dict):
                target[field] = {**target[field], **{k: v for k, v in value.items() if v is not None}}
            elif value is not None and value != "" and value != []:
                target[field] = value
    return rows


def merge_workspace_dump(existing, incoming):
    """Used by the old WorkspaceExtract writer so it cannot erase archive data."""
    old, snapshots = decode_dump(existing)
    new, _ = decode_dump(incoming)
    return encode_dump(merge_raw_rows(old, new), snapshots)


def valid_code(value):
    return isinstance(value, str) and CODE.fullmatch(value) is not None


def linked_ref(txn):
    props = txn.get("properties")
    ref = transaction_ref(txn) or (props.get("Link.FnbDashboardTrackingCode") if isinstance(props, dict) else None)
    return ref if valid_code(ref) else None


def _local_datetime(value):
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def save_snapshot(connection, ref, job, *, captured_at=None):
    if not valid_code(ref):
        raise ValueError("Invalid archive reference")
    job = dict(job)
    job["jobRefNumber"] = ref
    payload = json.dumps(job, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    captured = captured_at or datetime.now(timezone.utc).isoformat()
    txns = {t["trackingCode"]: t for t in records(job.get("txns")) if valid_code(t.get("trackingCode"))}
    # A job reference need not be an actual transaction. Anchor on a real
    # transaction whenever possible; job-only records use the reference.
    anchor = ref if ref in txns or not txns else min(txns)
    codes = sorted(set(txns) | {anchor})
    cursor = connection.cursor()
    try:
        inserted = False
        for code in codes:
            cursor.execute(f"SELECT dump,jobRefNumber FROM {TABLE} WITH (UPDLOCK,HOLDLOCK) WHERE trackingCode=?", (code,))
            row = cursor.fetchone()
            old, snapshots = decode_dump(row[0] if row else None)
            if row and row[1] and row[1] not in (ref, code):
                raise ValueError("Workspace tracking code belongs to a different job")
            current = txns.get(code, {})
            if current:
                old = merge_raw_rows(old, [current])
            if code == anchor and not any(s.get("hash") == digest for s in snapshots):
                snapshots.append({"hash": digest, "capturedAt": captured, "job": job})
                inserted = True
            dump = encode_dump(old, snapshots)
            fields = (current.get("formStatus"), current.get("userLoginName"),
                      current.get("formName"), _local_datetime(current.get("timeCreated")), ref, dump)
            if row:
                cursor.execute(f"""
                    UPDATE {TABLE} SET
                        currentQueue=COALESCE(?,currentQueue),
                        assignedTo=COALESCE(?,assignedTo),
                        formName=COALESCE(?,formName),
                        timeCreated=COALESCE(?,timeCreated),
                        jobRefNumber=?,dump=?
                    WHERE trackingCode=?
                """, fields + (code,))
            else:
                cursor.execute(f"""
                    INSERT INTO {TABLE} (currentQueue,assignedTo,formName,timeCreated,jobRefNumber,dump,trackingCode)
                    VALUES (?,?,?,?,?,?,?)
                """, fields + (code,))
        connection.commit()
        return inserted
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


def migrate_previous_archive(connection):
    """Copy any snapshots written by the previous release; never drop old tables."""
    cursor = connection.cursor()
    try:
        cursor.execute(f"SELECT OBJECT_ID('{LEGACY_ARCHIVE}', 'U')")
        exists = cursor.fetchone()
    finally:
        cursor.close()
    if not exists or exists[0] is None:
        return
    last_ref, last_hash = "", ""
    while True:
        cursor = connection.cursor()
        try:
            cursor.execute(f"""
                SELECT TOP 100 jobRefNumber,snapshotHash,capturedAt,payload
                FROM {LEGACY_ARCHIVE}
                WHERE jobRefNumber > ? OR (jobRefNumber = ? AND snapshotHash > ?)
                ORDER BY jobRefNumber,snapshotHash
            """, (last_ref, last_ref, last_hash))
            rows = cursor.fetchall()
        finally:
            cursor.close()
        if not rows:
            return
        for ref, digest, captured, payload in rows:
            save_snapshot(connection, ref, json.loads(payload),
                          captured_at=captured.isoformat() + "Z")
        last_ref, last_hash = rows[-1][0], rows[-1][1]


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
        migrate_previous_archive(sql.connection)
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
    """Resolve related tracking codes using the existing jobRefNumber column."""
    cursor = connection.cursor()
    try:
        cursor.execute(f"SELECT jobRefNumber FROM {TABLE} WHERE trackingCode=?", (code,))
        direct = cursor.fetchone()
        ref = direct[0] if direct and valid_code(direct[0]) else code
        cursor.execute(f"SELECT trackingCode,dump FROM {TABLE} WHERE jobRefNumber=? OR trackingCode=?", (ref, ref))
        rows = cursor.fetchall()
        if not rows:
            return None
        job = {"jobRefNumber": ref, "txns": [], "comments": [], "steps": []}
        snapshots = {}
        for row_code, dump in rows:
            raw, saved = decode_dump(dump)
            # Legacy dumps can contain several related forms. Include only
            # proven members of the selected application.
            related = [t for t in raw if t.get("trackingCode") == row_code
                       or transaction_ref(t) == ref or t.get("trackingCode") == ref]
            job["txns"] = merge_raw_rows(job["txns"], related)
            for entry in saved:
                if isinstance(entry, dict) and isinstance(entry.get("job"), dict):
                    if entry["job"].get("jobRefNumber") == ref:
                        snapshots.setdefault(entry["hash"], entry)
        ordered = sorted(snapshots.values(), key=lambda s: s.get("capturedAt") or "")
        for entry in ordered:
            snapshot = entry["job"]
            if snapshot.get("status"):
                job["status"] = snapshot["status"]
            if snapshot.get("steps"):
                job["steps"] = snapshot["steps"]
            for note in records(snapshot.get("comments")):
                if note not in job["comments"]:
                    job["comments"].append(note)
            job["txns"] = merge_raw_rows(job["txns"], records(snapshot.get("txns")))
        result = build_timeline(job)
        if not result["transactions"] and not result["application_comments"]:
            return None
        result["source"] = "archive"
        result["archived_at"] = ordered[-1].get("capturedAt") if ordered else None
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
