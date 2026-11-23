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
JOB_PAGE_SIZE = 20
DETAIL_BATCH_SIZE = 10
QUERY_TIMEOUT_SECONDS = 60


class WorkspaceReportError(Exception):
    """A safe reason for a failed Workspace request."""


def normalized(value):
    return str(value if value is not None else "").strip().lower()


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


def query_jobs(workspace, payload, stage):
    offset = 0
    while True:
        try:
            response = workspace.session.post(
                workspace.base_url.rstrip("/") + "/secure/api/v1/job/query",
                json={**payload, "fetchOffset": offset},
                timeout=(10, QUERY_TIMEOUT_SECONDS),
                allow_redirects=False,
            )
        except Timeout:
            raise Timeout(f"Workspace {stage} timed out at offset {offset}") from None
        status = response.status_code
        if 300 <= status < 400 or status in (401, 403):
            raise WorkspaceReportError(
                f"Journey Manager did not authorize the {stage} (HTTP {status})."
            )
        if status != 200:
            raise WorkspaceReportError(
                f"Journey Manager rejected the {stage} (HTTP {status})."
            )
        try:
            data = response.json()
        except ValueError:
            raise WorkspaceReportError(f"Journey Manager {stage} returned a non-JSON response.") from None
        rows = data.get("result") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            raise WorkspaceReportError(f"Journey Manager {stage} did not contain a result list.")
        total = data.get("totalCount")
        if not rows:
            if isinstance(total, int) and offset < total:
                raise WorkspaceReportError(f"Journey Manager returned an incomplete {stage}.")
            return
        yield from rows
        offset += len(rows)
        if isinstance(total, int) and offset >= total:
            return
        if offset >= 20000:
            raise WorkspaceReportError("Workspace range is too large. Select a shorter date range.")


def job_rows(workspace, start, end):
    if not workspace.login():
        raise WorkspaceReportError("Journey Manager Workspace sign-in failed.")

    date_filter = {
        "operator": "and",
        "criteria": [f"timeCreated >= '{start}'", f"timeCreated < '{end}'"],
    }
    sorts = ["timeCreated asc", "jobRefNumber asc"]
    summaries = query_jobs(workspace, {
        "attributes": ["jobRefNumber", "steps"],
        "filters": [date_filter],
        "sorts": sorts,
        "fetchLimit": JOB_PAGE_SIZE,
    }, "job history scan")

    references = {}
    for job in summaries:
        if not any(normalized(step.get("name")) in REVIEW_STEPS for step in job.get("steps") or []):
            continue
        reference = job.get("jobRefNumber")
        if not isinstance(reference, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", reference):
            raise WorkspaceReportError("Journey Manager returned an invalid review job reference.")
        references[reference] = None

    references = list(references)
    for offset in range(0, len(references), DETAIL_BATCH_SIZE):
        batch = references[offset:offset + DETAIL_BATCH_SIZE]
        reference_list = ", ".join(f"'{reference}'" for reference in batch)
        details = list(query_jobs(workspace, {
            "attributes": [
                "jobKey", "jobRefNumber", "status", "timeFinished", "timeCreated",
                "steps", "comments", "properties", "txns", "txns.comments", "txns.properties",
            ],
            "filters": [
                date_filter,
                {"operator": "and", "criteria": [f"jobRefNumber IN ({reference_list})"]},
            ],
            "sorts": sorts,
            "fetchLimit": DETAIL_BATCH_SIZE,
        }, "review detail query"))
        if {job.get("jobRefNumber") for job in details} != set(batch):
            raise WorkspaceReportError("Journey Manager returned incomplete review details. Rerun the report.")
        yield from details


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


def workspace_channel(job, transactions):
    values = {
        normalized((record.get("properties") or {}).get("isBankerAssisted"))
        for record in [job, *transactions]
    }
    channels = set()
    if values & {"true", "1", "yes"}:
        channels.add("In-Branch")
    if values & {"false", "0", "no"}:
        channels.add("Online")
    return next(iter(channels)) if len(channels) == 1 else None


def workflow_decision(steps, index):
    """Infer a decision only from an executed, unambiguous downstream branch."""
    outcomes = set()
    for step in steps[index + 1:]:
        name = normalized(step.get("name"))
        if name in REVIEW_STEPS:
            break
        outcome = {
            "approve application": "Approved",
            "decline application": "Denied",
        }.get(name)
        if outcome and normalized(step.get("status")) in {"in progress", "completed"}:
            outcomes.add(outcome)
    return next(iter(outcomes)) if len(outcomes) == 1 else None


def review_visits(job, transactions, now):
    steps = job.get("steps") or []
    only_review = sum(normalized(step.get("name")) in REVIEW_STEPS for step in steps) == 1
    for index, step in enumerate(steps):
        if normalized(step.get("name")) not in REVIEW_STEPS:
            continue
        actions = step.get("jobActions") or []
        action_keys = {action["jobActionKey"] for action in actions if action.get("jobActionKey")}
        submissions = {action["submission"] for action in actions if isinstance(action.get("submission"), str)}
        tasks = [
            txn for txn in transactions
            if txn.get("submitKey") in submissions or txn.get("trackingCode") in submissions
            or txn.get("jobActionKey") in action_keys
        ]
        if not tasks and only_review:
            candidates = [
                txn for txn in transactions
                if normalized(txn.get("groupName")) == "manual review"
                or normalized(txn.get("taskType")) == "review"
            ]
            if len(candidates) == 1:
                tasks = candidates
        started = timestamp(step.get("timeCreated"))
        action_times = [timestamp(action.get("timeActionExecuted")) for action in actions]
        task_times = [timestamp(task.get("timeCreated") or task.get("timeRequest")) for task in tasks]
        started = min(filter(None, [started, *action_times, *task_times]), default=None)
        step_status = normalized(step.get("status"))
        if not started and not tasks and step_status not in {"in progress", "completed", "expired"}:
            continue

        completed_tasks = [
            task for task in tasks
            if timestamp(task.get("timeCompleted")) or normalized(task.get("formStatus")) == "completed"
        ]
        completed_tasks.sort(
            key=lambda task: timestamp(task.get("timeCompleted")) or datetime.min.replace(tzinfo=timezone.utc)
        )
        finished = timestamp(step.get("timeFinished") or step.get("timeCompleted"))
        if not finished and step_status == "completed" and completed_tasks:
            finished = timestamp(completed_tasks[-1].get("timeCompleted"))
        outcome = decision(step) or next(
            (value for action in reversed(actions) if (value := decision(action))), None
        )
        if not outcome and step_status == "completed":
            outcome = workflow_decision(steps, index)
        reviewer = step.get("userLoginName") or (
            completed_tasks[-1].get("userLoginName") if completed_tasks else None
        )
        if not reviewer and len(tasks) == 1:
            reviewer = tasks[0].get("userLoginName")

        task_ids = {
            key for task in tasks for key in (task.get("submitKey"), task.get("trackingCode")) if key
        }
        comments = [comment for task in tasks for comment in task.get("comments") or []]
        comments.extend(
            comment for comment in job.get("comments") or []
            if comment.get("jobActionKey") in action_keys
            or comment.get("trackingCode") in task_ids
            or comment.get("submitKey") in task_ids
            or (only_review and normalized(comment.get("jobStep")) == normalized(step.get("name")))
        )
        notes = list(dict.fromkeys(
            comment["message"] for comment in comments
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
            visit["channel"] = workspace_channel(job, transactions)
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
            "channel": latest["channel"],
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
    except Timeout as error:
        current_app.logger.warning("Manual Review query timed out: %s", error)
        return jsonify(error="Journey Manager job history request timed out. Try a shorter date range."), 504
    except (RequestException, ValueError, TypeError, AttributeError) as error:
        current_app.logger.warning("Manual Review Workspace query failed: %s", type(error).__name__)
        return jsonify(error="Journey Manager could not return the Manual Review history."), 502

    try:
        channels = channels_for([row["application_id"] for row in rows if not row["channel"]])
    except Exception as error:
        current_app.logger.error("Manual Review channel lookup failed: %s", type(error).__name__)
        return jsonify(error="The application channel lookup failed."), 503

    for row in rows:
        row["channel"] = row["channel"] or channels.get(row["application_id"], "Unknown")
    return jsonify(rows=rows)
