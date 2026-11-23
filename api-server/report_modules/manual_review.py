"""Manual Review reporting from Journey Manager workflow history."""
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
import re

from flask import Blueprint, current_app, jsonify, request
from requests import RequestException, Timeout

from authentication import unauthorized, verify_microsoft_token, verify_token
from role_filter import all_groups


manual_review_api = Blueprint("manual_review", __name__)
REVIEW_STEPS = {"review application", "application review", "manual review"}
OUTCOMES = {
    "approve": "Approved", "approved": "Approved",
    "deny": "Denied", "denied": "Denied", "decline": "Denied", "declined": "Denied",
    "reject": "Denied", "rejected": "Denied",
}
PAGE_SIZE = 100


class WorkspaceReportError(Exception):
    """A safe reason for a failed Workspace request."""


def normalized(value):
    return str(value or "").strip().lower()


def timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else None


def decision(record):
    for field in ("result", "stepResult", "actionResult", "route", "decision", "outcome"):
        value = OUTCOMES.get(normalized(record.get(field)))
        if value:
            return value
    return None


def job_rows(workspace, start, end):
    if not workspace.login():
        raise WorkspaceReportError("Journey Manager Workspace sign-in failed.")

    payload = {
        "attributes": [
            "jobKey", "jobRefNumber", "status", "timeFinished", "timeCreated",
            "steps", "txns", "txns.comments", "txns.properties",
        ],
        "filters": [{
            "operator": "and",
            "criteria": [f"timeCreated >= '{start}'", f"timeCreated < '{end}'"],
        }],
        "sorts": ["timeCreated asc", "jobRefNumber asc"],
        "fetchLimit": PAGE_SIZE,
    }
    offset = 0
    while True:
        response = workspace.session.post(
            workspace.base_url.rstrip("/") + "/secure/api/v1/job/query",
            json={**payload, "fetchOffset": offset},
            timeout=20,
            allow_redirects=False,
        )
        status = response.status_code
        if 300 <= status < 400 or status in (401, 403):
            raise WorkspaceReportError(
                f"Journey Manager did not authorize the job history request (HTTP {status})."
            )
        if status != 200:
            raise WorkspaceReportError(
                f"Journey Manager rejected the job history request (HTTP {status})."
            )
        try:
            data = response.json()
        except ValueError:
            raise WorkspaceReportError("Journey Manager job history returned a non-JSON response.") from None
        rows = data.get("result") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            raise WorkspaceReportError("Journey Manager job history did not contain a result list.")
        total = data.get("totalCount")
        if not rows:
            if isinstance(total, int) and offset < total:
                raise ValueError("Incomplete Workspace job response")
            break
        yield from rows
        offset += len(rows)
        if isinstance(total, int) and offset >= total:
            break
        if offset >= 20000:
            raise ValueError("Workspace range is too large")


def tracking_code(job, transactions):
    start_keys = {
        action.get("submission")
        for step in job.get("steps") or [] if normalized(step.get("type")) == "start"
        for action in step.get("jobActions") or [] if action.get("submission")
    }
    candidates = [job.get("jobRefNumber")]
    candidates.extend(
        (txn.get("properties") or {}).get("Link.FnbDashboardTrackingCode")
        for txn in transactions
    )
    candidates.extend(
        txn.get("trackingCode") for txn in transactions if txn.get("submitKey") in start_keys
    )
    for value in candidates:
        if isinstance(value, str) and re.fullmatch(r"[BC]-[A-Z0-9]+", value, re.IGNORECASE):
            return value.upper()
    return None


def review_visits(job, transactions, now):
    by_key = {txn["submitKey"]: txn for txn in transactions if txn.get("submitKey")}
    for step in job.get("steps") or []:
        if normalized(step.get("name")) not in REVIEW_STEPS:
            continue
        actions = step.get("jobActions") or []
        keys = dict.fromkeys(
            action["submission"] for action in actions
            if normalized(action.get("type")) == "job task assign" and action.get("submission")
        )
        tasks = [by_key[key] for key in keys if key in by_key]
        started = timestamp(step.get("timeCreated"))
        action_times = [timestamp(action.get("timeActionExecuted")) for action in actions]
        task_times = [timestamp(task.get("timeCreated") or task.get("timeRequest")) for task in tasks]
        started = min(filter(None, [started, *action_times, *task_times]), default=None)
        step_status = normalized(step.get("status"))
        if not started and not tasks and step_status not in {"in progress", "completed", "expired"}:
            continue

        completed_tasks = [task for task in tasks if timestamp(task.get("timeCompleted"))]
        completed_tasks.sort(key=lambda task: timestamp(task["timeCompleted"]))
        finished = timestamp(step.get("timeFinished") or step.get("timeCompleted"))
        if not finished and step_status == "completed" and completed_tasks:
            finished = timestamp(completed_tasks[-1]["timeCompleted"])
        outcome = decision(step) or next(
            (value for action in reversed(actions) if (value := decision(action))), None
        )
        reviewer = step.get("userLoginName") or (
            completed_tasks[-1].get("userLoginName") if completed_tasks else None
        )
        notes = list(dict.fromkeys(
            comment["message"] for task in tasks for comment in task.get("comments") or []
            if isinstance(comment.get("message"), str) and comment["message"].strip()
        ))
        active = step_status in {"ready", "in progress", "assigned"} and not finished
        end = finished or (now if active else None)
        duration = int((end - started).total_seconds()) if started and end and end >= started else None
        yield {
            "started": started, "finished": finished, "duration": duration,
            "outcome": outcome, "reviewer": reviewer, "notes": notes, "active": active,
        }


def build_report(jobs, now):
    by_application = defaultdict(list)
    seen_jobs = set()
    for job in jobs:
        key = job.get("jobKey") or job.get("jobRefNumber")
        if key and key in seen_jobs:
            continue
        if key:
            seen_jobs.add(key)
        transactions = job.get("txns") or []
        code = tracking_code(job, transactions)
        if not code:
            continue
        finished = timestamp(job.get("timeFinished")) if normalized(job.get("status")) == "completed" else None
        for visit in review_visits(job, transactions, now):
            visit["application_finished"] = finished
            by_application[code].append(visit)

    rows = []
    for code, visits in sorted(by_application.items()):
        visits.sort(key=lambda visit: visit["started"] or datetime.min.replace(tzinfo=timezone.utc))
        latest = visits[-1]
        completed = (
            latest["finished"] is not None
            and latest["application_finished"] is not None
            and latest["application_finished"] >= latest["finished"]
        )
        rows.append({
            "application_id": code,
            "application_type": "Business" if code.startswith("B-") else "Consumer",
            "outcome": latest["outcome"],
            "reviewer": latest["reviewer"],
            "notes": list(dict.fromkeys(note for visit in visits for note in visit["notes"])),
            "duration_seconds": sum(visit["duration"] for visit in visits)
            if all(visit["duration"] is not None for visit in visits) else None,
            "in_review": any(visit["active"] for visit in visits),
            "completed": completed,
        })
    return rows


def channels_for(codes):
    if not codes:
        return {}
    from DB import SQLConn

    sql = SQLConn()
    channels = defaultdict(set)
    sql.connect()
    try:
        cursor = sql.connection.cursor()
        for offset in range(0, len(codes), 500):
            batch = codes[offset:offset + 500]
            placeholders = ", ".join("?" for _ in batch)
            cursor.execute(
                "SELECT DISTINCT eCATrackingCode, APPLICATION_TYPE "
                "FROM [DigitalReport].[dbo].[Transactions] "
                f"WHERE eCATrackingCode IN ({placeholders})",
                tuple(batch),
            )
            for tracking, application_type in cursor.fetchall():
                channel = {"online": "Online", "banker assisted": "In-Branch"}.get(
                    normalized(application_type)
                )
                if channel:
                    channels[tracking.upper()].add(channel)
    finally:
        sql.disconnect()
    return {code: next(iter(values)) for code, values in channels.items() if len(values) == 1}


@manual_review_api.after_request
def no_store(response):
    response.headers["Cache-Control"] = "private, no-store"
    return response


@manual_review_api.get("/reports/manual-review")
def manual_review():
    msal = request.headers.get("X-MSAL-ID-Token", "").strip()
    if msal:
        authorized = verify_microsoft_token(msal) is not None
    else:
        identity = verify_token(request.headers.get("Authorization")) or {}
        authorized = identity.get("role") in all_groups
    if not authorized:
        return unauthorized()

    try:
        start = date.fromisoformat(request.args.get("start_date", ""))
        end = date.fromisoformat(request.args.get("end_date", ""))
        if not 0 <= (end - start).days < 31:
            raise ValueError
        end_exclusive = end + timedelta(days=1)
    except (ValueError, OverflowError):
        return jsonify(error="Select an application creation date range of 1 to 31 days."), 400

    from DB import WorkspaceExtract

    try:
        workspace = WorkspaceExtract(setup_table=False)
        try:
            rows = build_report(job_rows(workspace, start, end_exclusive), datetime.now(timezone.utc))
        finally:
            if workspace.session is not None:
                workspace.session.close()
    except WorkspaceReportError as error:
        current_app.logger.warning("Manual Review Workspace query failed: %s", error)
        return jsonify(error=str(error)), 502
    except Timeout:
        current_app.logger.warning("Manual Review Workspace job query timed out")
        return jsonify(error="Journey Manager job history request timed out. Try a shorter date range."), 504
    except (RequestException, ValueError, TypeError, AttributeError) as error:
        current_app.logger.warning("Manual Review Workspace query failed: %s", type(error).__name__)
        return jsonify(error="Journey Manager could not return the Manual Review history."), 502

    try:
        channels = channels_for([row["application_id"] for row in rows])
    except Exception as error:
        current_app.logger.error("Manual Review channel lookup failed: %s", type(error).__name__)
        return jsonify(error="The application channel lookup failed."), 503

    for row in rows:
        row["channel"] = channels.get(row["application_id"], "Unknown")
    return jsonify(rows=rows)
